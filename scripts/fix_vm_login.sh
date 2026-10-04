#!/usr/bin/env bash
# ==============================================================================
# Script de Reparación Inmediata de Acceso y Credenciales en VM Azure
# ==============================================================================
set -e

echo "[1/4] Configurando SESSION_COOKIE_SECURE = False en /opt/security-portal/app/config.py..."
cat << 'EOF' | sudo tee /opt/security-portal/app/config.py > /dev/null
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secure-key-cloud-security-evaluation-3-iso27001")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "data", "portal_security.db"))
    
    # Configuraciones de seguridad para cookies y sesiones (OWASP / ISO 27001 A.9)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Permitir sesiones sobre HTTP (puerto 80) sin SSL
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutos de inactividad
EOF

echo "[2/4] Verificando e insertando usuarios en la base de datos de Hostify..."
sudo /opt/security-portal/venv/bin/python << 'EOF'
import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("/opt/security-portal/data/portal_security.db")
c = conn.cursor()

admin_hash = generate_password_hash("AdminSecurity2024!")
encargado_hash = generate_password_hash("EncargadoSecurity2024!")

# Insertar o actualizar admin
c.execute("""
    INSERT INTO users (id, username, password_hash, role, full_name, is_active)
    VALUES (1, 'admin', ?, 'admin', 'Administrador General', 1)
    ON CONFLICT(username) DO UPDATE SET
        password_hash = excluded.password_hash,
        role = 'admin',
        is_active = 1
""", (admin_hash,))

# Insertar o actualizar encargado
c.execute("""
    INSERT INTO users (id, username, password_hash, role, full_name, is_active)
    VALUES (2, 'encargado', ?, 'encargado', 'Encargado de Recepción', 1)
    ON CONFLICT(username) DO UPDATE SET
        password_hash = excluded.password_hash,
        role = 'encargado',
        is_active = 1
""", (encargado_hash,))

conn.commit()

print("[✓] Usuarios listos en la base de datos:")
c.execute("SELECT id, username, role, is_active FROM users")
for u in c.fetchall():
    print(f"    - ID: {u[0]} | Usuario: {u[1]} | Rol: {u[2]} | Activo: {u[3]}")

conn.close()
EOF

echo "[3/4] Ajustando permisos de carpetas para appuser..."
sudo chown -R appuser:appuser /opt/security-portal

echo "[4/4] Reiniciando servicio security-portal..."
sudo systemctl restart security-portal
sleep 2

echo "======================================================================"
echo " [✓] REPARACIÓN EXITOSA. Ya puedes iniciar sesión en tu navegador:"
echo " URL: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}')"
echo ""
echo " Credenciales listas para probar:"
echo "  1) Encargado (Recepción): encargado / EncargadoSecurity2024!"
echo "  2) Administrador:          admin / AdminSecurity2024!"
echo "======================================================================"
