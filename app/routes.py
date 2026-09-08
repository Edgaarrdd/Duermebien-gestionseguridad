from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from .models import get_db_connection
from .auth import login_required, role_required, record_audit

routes = Blueprint("routes", __name__)

@routes.app_context_processor
def inject_user():
    return {
        "current_user": {
            "is_authenticated": "user_id" in session,
            "username": session.get("username"),
            "full_name": session.get("full_name"),
            "role": session.get("role")
        }
    }

@routes.route("/health")
def health_check():
    """Endpoint de monitoreo de disponibilidad para sondas y balanceadores"""
    return jsonify({
        "status": "UP",
        "service": "Portal de Seguridad y Gestión de Incidentes",
        "compliance": ["ISO 27001", "NIST CSF", "CSA STAR"],
        "timestamp": request.environ.get("REQUEST_TIME", "")
    }), 200

@routes.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for("routes.login"))

@routes.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection(current_app.config["DATABASE_PATH"])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user["is_active"] and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            record_audit(
                action="LOGIN_SUCCESS",
                status="SUCCESS",
                details=f"Inicio de sesión exitoso para usuario {username} con rol {user['role']}"
            )
            flash(f"Bienvenido/a {user['full_name']} ({user['role'].upper()})", "success")
            return redirect(url_for("routes.dashboard"))
        else:
            record_audit(
                action="LOGIN_FAILED",
                status="FAILURE",
                details=f"Intento de inicio de sesión fallido para el usuario: '{username}'"
            )
            flash("Credenciales inválidas o cuenta deshabilitada. Intento registrado.", "danger")

    return render_template("login.html")

@routes.route("/logout")
def logout():
    username = session.get("username", "ANONYMOUS")
    record_audit(
        action="LOGOUT",
        status="SUCCESS",
        details=f"Cierre de sesión del usuario {username}"
    )
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("routes.login"))

@routes.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection(current_app.config["DATABASE_PATH"])
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE status = 'ABIERTO'")
    count_abiertos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE status = 'EN_ANALISIS'")
    count_analisis = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE status IN ('RESUELTO', 'CERRADO')")
    count_resueltos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE severity = 'CRITICO' AND status != 'CERRADO'")
    count_criticos = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 10")
    incidents = cursor.fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        stats={
            "abiertos": count_abiertos,
            "analisis": count_analisis,
            "resueltos": count_resueltos,
            "criticos": count_criticos
        },
        incidents=incidents
    )

@routes.route("/incidents/new", methods=["GET", "POST"])
@login_required
def new_incident():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        severity = request.form.get("severity", "MEDIO")

        if not title or not description:
            flash("El título y la descripción son obligatorios.", "warning")
            return render_template("new_incident.html")

        conn = get_db_connection(current_app.config["DATABASE_PATH"])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO incidents (title, description, severity, reported_by) VALUES (?, ?, ?, ?)",
            (title, description, severity, session["username"])
        )
        conn.commit()
        incident_id = cursor.lastrowid
        conn.close()

        record_audit(
            action="INCIDENT_REPORTED",
            status="SUCCESS",
            details=f"Incidente #{incident_id} reportado: '{title}' con severidad {severity}"
        )
        flash("Incidente de seguridad registrado exitosamente.", "success")
        return redirect(url_for("routes.dashboard"))

    return render_template("new_incident.html")

@routes.route("/incidents/<int:incident_id>/status", methods=["POST"])
@login_required
@role_required("admin")
def update_incident_status(incident_id):
    new_status = request.form.get("status")
    if new_status not in ['ABIERTO', 'EN_ANALISIS', 'RESUELTO', 'CERRADO']:
        flash("Estado no válido.", "danger")
        return redirect(url_for("routes.dashboard"))

    conn = get_db_connection(current_app.config["DATABASE_PATH"])
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE incidents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_status, incident_id)
    )
    conn.commit()
    conn.close()

    record_audit(
        action="INCIDENT_STATUS_CHANGE",
        status="SUCCESS",
        details=f"Incidente #{incident_id} actualizado a estado '{new_status}' por administrador {session['username']}"
    )
    flash(f"Estado del incidente #{incident_id} actualizado a {new_status}.", "success")
    return redirect(url_for("routes.dashboard"))

@routes.route("/admin/users", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_users():
    conn = get_db_connection(current_app.config["DATABASE_PATH"])
    cursor = conn.cursor()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "operador")

        if not username or not password or not full_name:
            flash("Todos los campos son obligatorios para crear usuario.", "warning")
        else:
            try:
                hashed = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                    (username, hashed, full_name, role)
                )
                conn.commit()
                record_audit(
                    action="USER_CREATED",
                    status="SUCCESS",
                    details=f"Usuario '{username}' creado con rol '{role}'"
                )
                flash(f"Usuario {username} creado con éxito.", "success")
            except Exception as e:
                flash(f"Error al crear usuario (posible nombre duplicado): {e}", "danger")

    cursor.execute("SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY id ASC")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin_users.html", users=users)

@routes.route("/admin/audit-logs")
@login_required
@role_required("admin")
def admin_audit_logs():
    conn = get_db_connection(current_app.config["DATABASE_PATH"])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50")
    logs = cursor.fetchall()
    conn.close()

    record_audit(
        action="VIEW_AUDIT_LOGS",
        status="SUCCESS",
        details="Acceso a la bitácora central de auditoría de seguridad"
    )

    return render_template("audit_logs.html", logs=logs)
