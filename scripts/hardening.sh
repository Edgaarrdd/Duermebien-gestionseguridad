#!/usr/bin/env bash
# ==============================================================================
# Script de Endurecimiento (Hardening) del Sistema Operativo - Ubuntu 22.04 LTS
# Alineado con ISO/IEC 27001 (A.12.1, A.13.1) y NIST SP 800-123
# ==============================================================================

set -e

echo "[*] Iniciando proceso de Hardening en VM Azure (vm-database-azure)..."

# 1. Verificar privilegios de root
if [ "$EUID" -ne 0 ]; then
  echo "[-] Por favor ejecute este script con privilegios de root (sudo bash hardening.sh)"
  exit 1
fi

# 2. Actualización de paquetes de seguridad
echo "[+] Actualizando repositorios y parches de seguridad del sistema..."
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# 3. Instalación de herramientas de defensa perimetral y detección
echo "[+] Instalando UFW y Fail2ban..."
apt-get install -y ufw fail2ban

# 4. Creación de usuario dedicado sin privilegios (Principio de Menor Privilegio)
if ! id -u appuser >/dev/null 2>&1; then
    echo "[+] Creando usuario de servicio 'appuser' (sin shell de login)..."
    useradd -r -s /usr/sbin/nologin -d /opt/security-portal appuser
fi

# 5. Configuración del Firewall UFW
echo "[+] Configurando reglas estrictas en Firewall UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Permitir SSH (puerto 22)
ufw allow 22/tcp comment 'Gestion SSH Segura'

# Permitir tráfico Web (80 y 443)
ufw allow 80/tcp comment 'Trafico Web HTTP'
ufw allow 443/tcp comment 'Trafico Web HTTPS'

# Bloqueo explícito de puertos de base de datos hacia el exterior
ufw deny 3306/tcp comment 'Bloqueo MySQL Externo'
ufw deny 5432/tcp comment 'Bloqueo PostgreSQL Externo'
ufw deny 27017/tcp comment 'Bloqueo MongoDB Externo'

ufw --force enable
echo "[+] Estado de UFW:"
ufw status verbose

# 6. Configuración de Fail2ban contra ataques de fuerza bruta SSH
echo "[+] Configurando Fail2ban para proteccion SSH..."
cat << 'EOF' > /etc/fail2ban/jail.local
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 4

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 24h
EOF

systemctl restart fail2ban
systemctl enable fail2ban

# 7. Endurecimiento de configuración SSH (/etc/ssh/sshd_config.d/99-hardened.conf)
echo "[+] Aplicando politicas de endurecimiento para el servicio SSH..."
mkdir -p /etc/ssh/sshd_config.d/
cat << 'EOF' > /etc/ssh/sshd_config.d/99-hardened.conf
# Politica de Seguridad SSH - ISO 27001
PermitRootLogin no
PasswordAuthentication no
ChallengeResponseAuthentication no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
EOF

systemctl restart sshd || systemctl restart ssh

# 8. Endurecimiento de parámetros del Kernel de Red (sysctl)
echo "[+] Aplicando parametros de seguridad al Kernel..."
cat << 'EOF' > /etc/sysctl.d/99-security-hardening.conf
# Deshabilitar redirecciones ICMP (previene envenenamiento de rutas)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Deshabilitar enrutamiento de paquetes IP fuente
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Mitigacion contra ataques SYN Flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048

# Ignorar peticiones ICMP broadcast
net.ipv4.icmp_echo_ignore_broadcasts = 1
EOF

sysctl -p /etc/sysctl.d/99-security-hardening.conf >/dev/null 2>&1 || true

echo "[✓] Hardening completado exitosamente en el servidor."
