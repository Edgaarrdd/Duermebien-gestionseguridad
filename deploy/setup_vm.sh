#!/usr/bin/env bash
# ==============================================================================
# Script de Despliegue Automatizado - Solución Cloud en Azure VM (Ubuntu 22.04)
# Proyecto Integrador: Gestión de Seguridad de la Información
# ==============================================================================

set -e

echo "======================================================================"
echo "    INICIANDO INSTALACIÓN Y DESPLIEGUE EN VM-DATABASE-AZURE           "
echo "======================================================================"

if [ "$EUID" -ne 0 ]; then
  echo "[-] Por favor ejecute como root: sudo bash deploy/setup_vm.sh"
  exit 1
fi

PROJECT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="/opt/security-portal"

echo "[1/7] Instalando paquetes base del sistema (Python, Nginx, UFW, Fail2ban)..."
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    ufw \
    fail2ban \
    curl \
    tar

echo "[2/7] Creando usuario de servicio 'appuser' y carpetas de trabajo..."
if ! id -u appuser >/dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin -d ${TARGET_DIR} appuser
fi

mkdir -p ${TARGET_DIR}
cp -r ${PROJECT_SRC}/app ${TARGET_DIR}/
cp -r ${PROJECT_SRC}/scripts ${TARGET_DIR}/
cp -r ${PROJECT_SRC}/deploy ${TARGET_DIR}/
cp ${PROJECT_SRC}/run.py ${TARGET_DIR}/
cp ${PROJECT_SRC}/requirements.txt ${TARGET_DIR}/

mkdir -p ${TARGET_DIR}/data
mkdir -p ${TARGET_DIR}/logs
mkdir -p ${TARGET_DIR}/backups

chmod +x ${TARGET_DIR}/scripts/*.sh

echo "[3/7] Creando entorno virtual e instalando dependencias..."
python3 -m venv ${TARGET_DIR}/venv
${TARGET_DIR}/venv/bin/pip install --upgrade pip
${TARGET_DIR}/venv/bin/pip install -r ${TARGET_DIR}/requirements.txt

# Inicializar Base de Datos con modelos y usuarios por defecto
echo "[+] Inicializando base de datos SQLite con RBAC y auditoría..."
${TARGET_DIR}/venv/bin/python -c "from app import create_app; app = create_app(); print('BD Inicializada con exito.')"

# Asignar permisos seguros al usuario de la aplicacion
chown -R appuser:appuser ${TARGET_DIR}
chmod 750 ${TARGET_DIR}
chmod 700 ${TARGET_DIR}/data
chmod 700 ${TARGET_DIR}/logs
chmod 700 ${TARGET_DIR}/backups

echo "[4/7] Configurando servicio Systemd para Alta Disponibilidad..."
cp ${TARGET_DIR}/deploy/security-portal.service /etc/systemd/system/security-portal.service
systemctl daemon-reload
systemctl enable security-portal
systemctl restart security-portal

echo "[5/7] Configurando Proxy Inverso Nginx y Cabeceras de Seguridad..."
cp ${TARGET_DIR}/deploy/nginx.conf /etc/nginx/sites-available/security-portal
ln -sf /etc/nginx/sites-available/security-portal /etc/nginx/sites-enabled/security-portal
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
systemctl enable nginx

echo "[6/7] Aplicando Hardening del Sistema (Firewall UFW, Fail2ban, SSH)..."
bash ${TARGET_DIR}/scripts/hardening.sh

echo "[7/7] Configurando tarea automatizada de respaldos (Disponibilidad)..."
bash ${TARGET_DIR}/scripts/backup_automation.sh --install-cron
bash ${TARGET_DIR}/scripts/backup_automation.sh --verify

echo "======================================================================"
echo "    VERIFICANDO ESTADO Y SONDAS DE SALUD DEL SISTEMA                  "
echo "======================================================================"
sleep 2
HEALTH_STATUS=$(curl -s http://127.0.0.1/health || echo "ERROR")
echo "[+] Respuesta de Sonda de Salud (/health):"
echo "$HEALTH_STATUS"

echo ""
echo "======================================================================"
echo "    DESPLIEGUE COMPLETADO EXITOSAMENTE                                "
echo "======================================================================"
echo "Servicio Web: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}')"
echo ""
echo "Credenciales RBAC para Pruebas:"
echo " - Administrador: admin / AdminSecurity2024!"
echo " - Encargado:     encargado / EncargadoSecurity2024!"
echo ""
echo "Comandos útiles de diagnóstico:"
echo " - Ver servicio: sudo systemctl status security-portal"
echo " - Ver logs app: sudo journalctl -u security-portal -f"
echo " - Ver auditoria: cat ${TARGET_DIR}/logs/security_audit.log"
echo "======================================================================"
