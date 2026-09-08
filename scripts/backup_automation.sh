#!/usr/bin/env bash
# ==============================================================================
# Script de Respaldo Automatizado y Verificación de Disponibilidad
# Alineado con ISO/IEC 27001 (Control A.12.3 Copias de Seguridad) y NIST CP-9
# ==============================================================================

set -e

BACKUP_DIR="/opt/security-portal/backups"
DATA_DIR="/opt/security-portal/data"
CONFIG_DIR="/opt/security-portal/app"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_ARCHIVE="${BACKUP_DIR}/backup_security_portal_${TIMESTAMP}.tar.gz"
CHECKSUM_FILE="${BACKUP_ARCHIVE}.sha256"

# 1. Instalar en Cron si se solicita
if [ "$1" == "--install-cron" ]; then
    echo "[+] Registrando tarea cron de respaldo diario a las 02:00 AM..."
    CRON_CMD="0 2 * * * /bin/bash /opt/security-portal/scripts/backup_automation.sh >> /var/log/portal_backup.log 2>&1"
    (crontab -l 2>/dev/null | grep -v "backup_automation.sh" ; echo "$CRON_CMD") | crontab -
    echo "[✓] Cron instalado con éxito. Programación actual:"
    crontab -l | grep "backup_automation"
    exit 0
fi

# 2. Crear directorio de backups con permisos restringidos (solo root / appuser)
mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

echo "[*] [${TIMESTAMP}] Iniciando proceso de respaldo de seguridad..."

# 3. Comprobar existencia de base de datos
if [ ! -f "${DATA_DIR}/portal_security.db" ]; then
    echo "[!] Advertencia: Base de datos no encontrada en ${DATA_DIR}/portal_security.db. Creando respaldo de estructura..."
fi

# 4. Generar archivo comprimido de respaldo
tar -czf "${BACKUP_ARCHIVE}" -C /opt/security-portal data logs app run.py deploy 2>/dev/null || \
tar -czf "${BACKUP_ARCHIVE}" -C /opt/security-portal data app run.py

# 5. Generar Checksum SHA-256 para verificación de integridad (Anti-tampering)
sha256sum "${BACKUP_ARCHIVE}" > "${CHECKSUM_FILE}"

echo "[✓] Respaldo generado con éxito: ${BACKUP_ARCHIVE}"
echo "[✓] Hash de Integridad SHA-256: $(cat ${CHECKSUM_FILE})"

# 6. Política de retención: Eliminar respaldos con más de 7 días
echo "[+] Aplicando política de rotación (retención de 7 días)..."
find "${BACKUP_DIR}" -type f -name "backup_security_portal_*.tar.gz*" -mtime +7 -delete

# 7. Modo de verificación o prueba si se pasa el argumento --verify
if [ "$1" == "--verify" ]; then
    echo "[+] Verificando integridad del respaldo recién creado..."
    sha256sum -c "${CHECKSUM_FILE}"
    echo "[+] Listando contenido del archivo de respaldo:"
    tar -ztvf "${BACKUP_ARCHIVE}" | head -n 10
    echo "[✓] Prueba de recuperación y verificación de respaldo EXITOSA."
fi
