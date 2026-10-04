#!/usr/bin/env bash
# Script para solucionar acceso inmediato en la VM
set -e

echo "[+] Corrigiendo configuración de cookies seguras para HTTP en /opt/security-portal/app/config.py..."
sudo sed -i 's/SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"/SESSION_COOKIE_SECURE = False/g' /opt/security-portal/app/config.py
sudo sed -i 's/SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")/SESSION_COOKIE_SECURE = False/g' /opt/security-portal/app/config.py

echo "[+] Asegurando credenciales en la base de datos de Hostify..."
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

c.execute("SELECT id, username, role, is_active FROM users")
print("[✓] Usuarios actuales en BD:")
for row in c.fetchall():
    print(f"    - ID: {row[0]}, Usuario: {row[1]}, Rol: {row[2]}, Activo: {row[3]}")

conn.close()
EOF

echo "[+] Ajustando permisos de appuser..."
sudo chown -R appuser:appuser /opt/security-portal

echo "[+] Reiniciando servicio security-portal..."
sudo systemctl restart security-portal
sleep 2

echo "[✓] Servicio reiniciado con éxito. Prueba iniciar sesión en tu navegador ahora:"
echo "    - Encargado: encargado / EncargadoSecurity2024!"
echo "    - Admin:     admin / AdminSecurity2024!"
