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
        "service": "Hostify Hotel Management System",
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

    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status = 'DISPONIBLE'")
    count_disponibles = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status = 'OCUPADA'")
    count_ocupadas = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status = 'PENDIENTE'")
    count_pendientes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM guests")
    count_guests = cursor.fetchone()[0]

    # Traer reservas recientes
    cursor.execute("""
        SELECT r.id, ro.number as room_number, g.full_name as guest_name, r.check_in_date, r.check_out_date, r.status
        FROM reservations r
        JOIN rooms ro ON r.room_id = ro.id
        JOIN guests g ON r.guest_id = g.id
        ORDER BY r.created_at DESC LIMIT 10
    """)
    reservations = cursor.fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        stats={
            "disponibles": count_disponibles,
            "ocupadas": count_ocupadas,
            "pendientes": count_pendientes,
            "huespedes": count_guests
        },
        reservations=reservations
    )

@routes.route("/rooms")
@login_required
def rooms():
    conn = get_db_connection(current_app.config["DATABASE_PATH"])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms ORDER BY number ASC")
    rooms_list = cursor.fetchall()
    conn.close()
    return render_template("rooms.html", rooms=rooms_list)

@routes.route("/rooms/<int:room_id>/status", methods=["POST"])
@login_required
@role_required("admin")
def update_room_status(room_id):
    new_status = request.form.get("status")
    if new_status not in ['DISPONIBLE', 'OCUPADA', 'MANTENIMIENTO', 'LIMPIEZA']:
        flash("Estado no válido.", "danger")
        return redirect(url_for("routes.rooms"))

    conn = get_db_connection(current_app.config["DATABASE_PATH"])
    cursor = conn.cursor()
    cursor.execute("UPDATE rooms SET status = ? WHERE id = ?", (new_status, room_id))
    conn.commit()
    conn.close()

    record_audit(
        action="ROOM_STATUS_CHANGE",
        status="SUCCESS",
        details=f"Habitación #{room_id} actualizada a estado '{new_status}' por administrador {session['username']}"
    )
    flash(f"Estado de la habitación actualizado a {new_status}.", "success")
    return redirect(url_for("routes.rooms"))

@routes.route("/guests", methods=["GET", "POST"])
@login_required
def guests():
    conn = get_db_connection(current_app.config["DATABASE_PATH"])
    cursor = conn.cursor()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        
        if not full_name or not email:
            flash("El nombre y el email son obligatorios.", "warning")
        else:
            try:
                cursor.execute(
                    "INSERT INTO guests (full_name, email, phone) VALUES (?, ?, ?)",
                    (full_name, email, phone)
                )
                conn.commit()
                record_audit(
                    action="GUEST_CREATED",
                    status="SUCCESS",
                    details=f"Huésped '{full_name}' registrado por {session['username']}"
                )
                flash(f"Huésped {full_name} registrado con éxito.", "success")
            except Exception as e:
                flash(f"Error al registrar huésped (posible email duplicado).", "danger")

    cursor.execute("SELECT * FROM guests ORDER BY created_at DESC")
    guests_list = cursor.fetchall()
    conn.close()
    return render_template("guests.html", guests=guests_list)

@routes.route("/reservations", methods=["GET", "POST"])
@login_required
def reservations():
    conn = get_db_connection(current_app.config["DATABASE_PATH"])
    cursor = conn.cursor()

    if request.method == "POST":
        room_id = request.form.get("room_id")
        guest_id = request.form.get("guest_id")
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")

        if not room_id or not guest_id or not check_in or not check_out:
            flash("Todos los campos son obligatorios para crear una reserva.", "warning")
        else:
            cursor.execute(
                "INSERT INTO reservations (room_id, guest_id, check_in_date, check_out_date, created_by) VALUES (?, ?, ?, ?, ?)",
                (room_id, guest_id, check_in, check_out, session["username"])
            )
            # Update room status to OCUPADA automatically as an example of business logic
            cursor.execute("UPDATE rooms SET status = 'OCUPADA' WHERE id = ?", (room_id,))
            conn.commit()
            
            res_id = cursor.lastrowid
            record_audit(
                action="RESERVATION_CREATED",
                status="SUCCESS",
                details=f"Reserva #{res_id} creada para huésped #{guest_id} en habitación #{room_id}"
            )
            flash("Reserva creada con éxito.", "success")

    cursor.execute("""
        SELECT r.id, ro.number as room_number, g.full_name as guest_name, r.check_in_date, r.check_out_date, r.status
        FROM reservations r
        JOIN rooms ro ON r.room_id = ro.id
        JOIN guests g ON r.guest_id = g.id
        ORDER BY r.created_at DESC
    """)
    reservations_list = cursor.fetchall()
    
    # Para el formulario de nueva reserva
    cursor.execute("SELECT * FROM rooms WHERE status = 'DISPONIBLE'")
    available_rooms = cursor.fetchall()
    
    cursor.execute("SELECT * FROM guests ORDER BY full_name ASC")
    all_guests = cursor.fetchall()
    
    conn.close()
    return render_template("reservations.html", reservations=reservations_list, rooms=available_rooms, guests=all_guests)


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
        role = request.form.get("role", "encargado")

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
