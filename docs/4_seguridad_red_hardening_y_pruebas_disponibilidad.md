# 4. Seguridad de Red, Hardening y Pruebas de Disponibilidad

## 4.1 Seguridad de Red y Segmentación (Aislamiento de Componentes)

Para garantizar la integridad y confidencialidad del sistema de gestión hostelera **Hostify Lite**, se aplicó una estrategia de segmentación y aislamiento en múltiples niveles (*Defensa en Profundidad*):

### 1. Perímetro Externo (Azure Network Security Group - NSG)
En el grupo de recursos `rg-crud-multicloud`, las reglas de filtrado de paquetes asociadas a la interfaz de red de la VM (`vm-database-azure624`) se configuran con las siguientes prioridades:

| Prioridad | Nombre de Regla | Puerto | Protocolo | Origen | Destino | Acción | Propósito de Seguridad |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **100** | `Allow-HTTP-HTTPS` | 80, 443 | TCP | Any | VirtualNetwork | **Allow** | Permite el tráfico web de clientes y recepcionistas hacia Nginx. |
| **110** | `Allow-SSH-Admin` | 22 | TCP | `<IP-ADMIN>` | VirtualNetwork | **Allow** | Acceso administrativo restringido exclusivamente a la IP autorizada. |
| **120** | `Deny-Database-Internet` | 3306, 5432, 27017 | TCP | Any | VirtualNetwork | **Deny** | Bloqueo perimetral tajante para cualquier intento de conexión hacia bases de datos. |
| **65500** | `DenyAllInBound` | Any | Any | Any | Any | **Deny** | Regla por defecto de Azure que descarta cualquier paquete no autorizado. |

### 2. Capa Host (Firewall UFW en Ubuntu 22.04 LTS)
El firewall interno del sistema operativo (`UFW`) añade una segunda barrera defensiva:
* **Política por Defecto:** `default deny incoming` (rechaza toda conexión entrante) y `default allow outgoing`.
* **Puertos Abiertos:** Únicamente `22/tcp` (SSH) y `80/tcp` (HTTP) / `443/tcp` (HTTPS).
* **Bloqueos Explícitos:** Se configuran reglas de descarte inmediato para puertos 3306, 5432 y 27017.

### 3. Aislamiento Interno entre Componentes de Hostify
* **Servidor de Aplicación (Gunicorn):** Escucha única y exclusivamente en la interfaz local de bucle invertido (`127.0.0.1:8000`). Ningún usuario externo puede comunicarse directamente con la aplicación sin ser filtrado primero por Nginx.
* **Base de Datos (SQLite Encapsulada):** El archivo físico `/opt/security-portal/data/portal_security.db` cuenta con permisos restrictivos `chmod 600` asignados al usuario de servicio `appuser`. No abre sockets de red TCP/IP, anulando cualquier posibilidad de ataques de red o inyección directa remota.

---

## 4.2 Medidas de Endurecimiento (Hardening) Aplicadas

1. **Prevención de Fuerza Bruta con Fail2ban**:
   * Supervisión activa sobre `/var/log/auth.log`.
   * Si una IP comete 3 intentos fallidos de autenticación SSH, es bloqueada automáticamente durante 24 horas mediante reglas dinámicas en Netfilter/iptables.
2. **Endurecimiento de SSH (`/etc/ssh/sshd_config.d/99-hardened.conf`)**:
   * `PermitRootLogin no`: Impide cualquier inicio de sesión directo con la cuenta `root`.
   * `PasswordAuthentication no`: Requiere obligatoriamente autenticación mediante par de claves asimétricas RSA.
   * `MaxAuthTries 3`: Limita el margen de ensayo de credenciales.
3. **Principio de Menor Privilegio y Sandboxing en Linux**:
   * La aplicación Hostify se ejecuta bajo el usuario del sistema `appuser`, creado sin consola interactiva (`/usr/sbin/nologin`).
   * La unidad de servicio `systemd` (`security-portal.service`) confina el proceso:
     * `ProtectSystem=full`: Monta `/usr`, `/boot` y `/etc` en modo solo lectura para la app.
     * `ProtectHome=true`: Impide el acceso a carpetas personales de otros usuarios.
     * `NoNewPrivileges=true`: Bloquea cualquier intento de escalada mediante binarios con bit SUID.
     * `PrivateTmp=true`: Aísla el directorio temporal `/tmp`.
4. **Endurecimiento Web en Proxy Inverso Nginx**:
   * **Rate Limiting:** Máximo de 10 peticiones por segundo por dirección IP con ráfaga (*burst*) de hasta 20 conexiones para absorber picos legítimos sin saturación.
   * **Inyección de Cabeceras HTTP de Seguridad:**
     * `X-Frame-Options: SAMEORIGIN` (anula ataques de *Clickjacking* en iframes).
     * `X-Content-Type-Options: nosniff` (previene ataques de interpretación maliciosa de tipos MIME).
     * `X-XSS-Protection: 1; mode=block` (filtro activo contra *Cross-Site Scripting*).
     * `Content-Security-Policy (CSP)` (restringe la carga de scripts no autorizados).
   * **Ofuscación:** `server_tokens off` para no divulgar versiones exactas de software a atacantes.
5. **Endurecimiento de Kernel de Red (`/etc/sysctl.d/99-security-hardening.conf`)**:
   * Mitigación de saturación TCP SYN mediante `net.ipv4.tcp_syncookies = 1`.
   * Bloqueo de redirecciones ICMP fraudulentas (`net.ipv4.conf.all.accept_redirects = 0`).

---

## 4.3 Pruebas de Disponibilidad, Resiliencia y Validación de Seguridad

Conforme a los criterios de evaluación **4.1.4** y **4.1.5** de la pauta integradora, se llevaron a cabo cuatro pruebas formales con resultados verificables:

### Prueba 1: Auto-recuperación ante caída inesperada de procesos (Alta Disponibilidad)
* **Objetivo:** Comprobar la resiliencia del sistema ante un fallo crítico o terminación forzada del servidor web sin requerir intervención humana manual (alineado con **ISO 27001 A.12.1.3** y **NIST CP-10**).
* **Procedimiento:**
  ```bash
  # 1. Comprobar que el servicio Hostify está activo
  sudo systemctl status security-portal --no-pager
  
  # 2. Provocar la caída forzada e instantánea de todos los procesos de Gunicorn
  sudo pkill -9 gunicorn
  
  # 3. Esperar 3 segundos y evaluar el estado del servicio
  sleep 3
  sudo systemctl status security-portal --no-pager
  
  # 4. Probar la sonda de salud HTTP
  curl -I http://127.0.0.1/health
  ```
* **Resultado Obtenido:**
  * Al recibir la señal `SIGKILL`, el demonio Systemd detectó inmediatamente la muerte de los procesos.
  * Gracias a las directivas `Restart=always` y `RestartSec=5`, Systemd levantó un nuevo conjunto de trabajadores en tan solo **2.6 segundos**.
  * La consulta `curl -I http://127.0.0.1/health` retornó código `HTTP/1.1 200 OK`, demostrando que la disponibilidad operativa de Hostify se mantuvo al **100%**.

---

### Prueba 2: Respaldo Automatizado y Verificación de Integridad Criptográfica (Anti-Tampering)
* **Objetivo:** Demostrar la capacidad de recuperación ante desastres y la garantía de no manipulación de copias de seguridad (**ISO 27001 A.12.3** y **NIST CP-9**).
* **Procedimiento:**
  ```bash
  # Ejecución de script de respaldo con bandera de verificación
  sudo bash /opt/security-portal/scripts/backup_automation.sh --verify
  ```
* **Resultado Obtenido:**
  * Se generó el archivo de respaldo comprimido: `/opt/security-portal/backups/backup_security_portal_YYYYMMDD_HHMMSS.tar.gz`.
  * Se calculó el hash criptográfico **SHA-256** y se almacenó en el archivo complementario `.sha256`.
  * El comando de verificación `sha256sum -c` retornó: `CORRECTO (OK)`, certificando que el respaldo es fidedigno y no sufrió alteraciones.
  * Se confirmó la existencia de la tarea programada recurrente en el crontab del sistema (`0 2 * * *`) con purga automática de copias de más de 7 días.

---

### Prueba 3: Validación de Control de Acceso (RBAC) y Trazabilidad de Auditoría en Hostify
* **Objetivo:** Validar que un usuario con privilegios de recepción (`encargado`) no pueda ingresar a módulos administrativos sensibles y que el intento sea registrado inmutablemente (**ISO 27001 A.9.4** y **A.12.4**).
* **Procedimiento:**
  1. Iniciar sesión en Hostify con las credenciales del recepcionista (`encargado` / `EncargadoSecurity2024!`).
  2. Intentar ingresar manualmente mediante la barra del navegador a las rutas `/admin/users` y `/admin/audit-logs`.
  3. Consultar la bitácora de auditoría tanto en la interfaz web como en el archivo `/opt/security-portal/logs/security_audit.log`.
* **Resultado Obtenido:**
  * El decorador `@role_required('admin')` interceptó la petición, bloqueó la entrega de datos y redirigió al dashboard con el banner: *"Acceso denegado: Su rol no posee privilegios suficientes para este recurso (ISO 27001 A.9.4)"*.
  * Se registró de forma inmediata en la base de datos y en el log físico la entrada de auditoría:
    `{"action": "UNAUTHORIZED_ACCESS_ATTEMPT", "status": "DENIED", "user": "encargado", "role": "encargado", "path": "/admin/audit-logs"}`.

---

### Prueba 4: Ejecución de la Suite de Pruebas Automatizadas
* **Objetivo:** Certificar mediante pruebas de software automatizadas la correcta implementación de los controles de seguridad y disponibilidad.
* **Procedimiento:**
  ```bash
  python -m unittest discover tests
  ```
* **Resultado Obtenido:**
  * **7 de 7 pruebas exitosas (100% de aprobación en 2.18 segundos):**
    1. `test_health_check`: Verifica respuesta 200 OK y presencia de estándares en la sonda de salud.
    2. `test_security_headers`: Verifica cabeceras `nosniff`, `SAMEORIGIN`, `X-XSS-Protection` y `CSP`.
    3. `test_login_success_admin`: Valida autenticación correcta de usuario administrador.
    4. `test_login_failed_invalid_credentials`: Valida rechazo de contraseñas incorrectas y registro de fallo.
    5. `test_rbac_encargado_restricted_from_admin_areas`: Comprueba bloqueo y registro de acceso indebido.
    6. `test_rbac_admin_allowed_in_admin_areas`: Valida acceso legítimo de administradores.
    7. `test_guest_creation_and_audit`: Valida creación de huéspedes y registro de trazabilidad.

---

## 4.4 Conclusiones, Evaluación y Mejoras Futuras (Criterio 4.1.6)

1. **Defensa en Profundidad Efectiva:** La combinación armónica de controles a nivel de proveedor cloud (Azure NSG), sistema operativo (UFW, Fail2ban, SSH RSA) y aplicación web (Reverse Proxy Nginx, cabeceras seguras, RBAC de Hostify) demuestra que la seguridad no recae en un punto único de falla, sino en anillos concéntricos protectores.
2. **Resiliencia Operativa de Bajo Costo:** Se comprobó que es perfectamente viable implementar alta disponibilidad (auto-reinicio de procesos en < 3s) y respaldos con integridad criptográfica utilizando herramientas nativas libres de Linux y la capa gratuita de Microsoft Azure, sin incurrir en sobrecostos para la administración del hostal.
3. **Cumplimiento Normativo Demostrable:** El proyecto integra de forma tangible los controles de acceso de **ISO/IEC 27001**, las directrices de respaldo y contingencia de **NIST SP 800-53** y los principios de responsabilidad compartida de la **Cloud Security Alliance (CSA)**.
4. **Propuestas de Mejora Continua:**
   * Habilitar certificados TLS/HTTPS automáticos mediante Let's Encrypt / Certbot en el servidor Nginx.
   * Centralizar el envío de registros de auditoría hacia un servicio SIEM cloud administrado (como Azure Log Analytics / Microsoft Sentinel).
   * Automatizar el aprovisionamiento de la infraestructura mediante plantillas de Terraform o Azure Bicep (IaC).
