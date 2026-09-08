import functools
import logging
import os
from flask import session, redirect, url_for, flash, request, abort, current_app
from .models import get_db_connection

# Configurar logger de auditoría en archivo local para evidencia y SIEM
AUDIT_LOG_FILE = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "logs", "security_audit.log")
os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)

audit_logger = logging.getLogger("SecurityAuditLogger")
if not audit_logger.handlers:
    audit_logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(AUDIT_LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}')
    file_handler.setFormatter(formatter)
    audit_logger.addHandler(file_handler)

def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"

def record_audit(action, status, details=""):
    username = session.get("username", "ANONYMOUS")
    role = session.get("role", "NONE")
    ip_addr = get_client_ip()

    # 1. Guardar en Base de Datos
    try:
        db_path = current_app.config["DATABASE_PATH"]
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (username, role, action, ip_address, status, details) VALUES (?, ?, ?, ?, ?, ?)",
            (username, role, action, ip_addr, status, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error escribiendo en BD de auditoría: {e}")

    # 2. Guardar en Archivo de Auditoría Segura (formato JSON estructurado)
    import json
    log_entry = json.dumps({
        "username": username,
        "role": role,
        "action": action,
        "ip_address": ip_addr,
        "status": status,
        "details": details
    })
    audit_logger.info(log_entry)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Debe iniciar sesión para acceder a este recurso.", "warning")
            return redirect(url_for("routes.login"))
        return view(**kwargs)
    return wrapped_view

def role_required(*allowed_roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if "user_id" not in session:
                return redirect(url_for("routes.login"))
            
            user_role = session.get("role")
            if user_role not in allowed_roles:
                record_audit(
                    action="UNAUTHORIZED_ACCESS_ATTEMPT",
                    status="DENIED",
                    details=f"Acceso denegado a ruta {request.path}. Rol actual: {user_role}. Roles requeridos: {allowed_roles}"
                )
                flash("Acceso denegado: Su rol no posee privilegios suficientes para este recurso (ISO 27001 A.9.4).", "danger")
                return redirect(url_for("routes.dashboard"))
            return view(**kwargs)
        return wrapped_view
    return decorator
