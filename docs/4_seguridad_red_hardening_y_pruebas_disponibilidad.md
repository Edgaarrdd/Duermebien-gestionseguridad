# 4. Seguridad de Red, Hardening y Pruebas de Disponibilidad

## 4.1 Seguridad de Red y Segmentación (Aislamiento de Componentes)

Para dar cumplimiento al requisito de segmentación y aislamiento, se implementó una estrategia en tres capas:

### 1. Perímetro Externo (Azure Network Security Group - NSG)
En el grupo de recursos `rg-crud-multicloud`, las reglas de seguridad de red asociadas a la interfaz de la VM se configuran de la siguiente manera:

| Prioridad | Nombre de Regla | Puerto | Protocolo | Origen | Destino | Acción | Propósito de Seguridad |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **100** | `Allow-HTTP-HTTPS` | 80, 443 | TCP | Any | VirtualNetwork | **Allow** | Tráfico web público hacia el proxy Nginx. |
| **110** | `Allow-SSH-Admin` | 22 | TCP | `<IP-ADMIN>` | VirtualNetwork | **Allow** | Administración remota restringida a la IP autorizada. |
| **120** | `Deny-Database-Internet` | 3306, 5432, 27017 | TCP | Any | VirtualNetwork | **Deny** | Bloqueo perimetral estricto de puertos de datos. |
| **65500** | `DenyAllInBound` | Any | Any | Any | Any | **Deny** | Denegación por defecto de cualquier otro tráfico entrante. |

### 2. Capa Host (Firewall UFW en Ubuntu 22.04)
El firewall interno del sistema operativo (`UFW`) complementa las reglas de Azure aplicando defensa en profundidad:
* Política por defecto: `default deny incoming`, `default allow outgoing`.
* Puertos abiertos internamente: solo `22/tcp`, `80/tcp` y `443/tcp`.

### 3. Aislamiento Interno entre Componentes (Zero External Exposure)
* **Gunicorn (App):** Escucha exclusivamente en `127.0.0.1:8000`. Ningún usuario externo puede conectarse directamente a la aplicación sin pasar por Nginx.
* **Base de Datos (SQLite):** Reside como archivo local cifrado en disco (`/opt/security-portal/data/portal_security.db`) con permisos de acceso `chmod 600` exclusivos para el usuario del servicio (`appuser`). No abre ningún puerto de red TCP/IP.

---

## 4.2 Medidas de Endurecimiento (Hardening) Aplicadas

1. **Protección contra Fuerza Bruta con Fail2ban**:
   - Monitoreo continuo de `/var/log/auth.log`.
   - Si una dirección IP acumula 3 intentos fallidos de autenticación SSH, queda baneada automáticamente por 24 horas mediante reglas directas en iptables.
2. **Hardening de SSH**:
   - `PermitRootLogin no`: Prohíbe el acceso directo del usuario `root`.
   - `PasswordAuthentication no`: Requiere forzosamente autenticación con llave criptográfica RSA.
   - `MaxAuthTries 3`: Limita el número de intentos por conexión.
3. **Principio de Menor Privilegio (Sandboxing a nivel de proceso)**:
   - La aplicación no se ejecuta como `root`. Se creó el usuario de sistema `appuser` sin shell de inicio de sesión interactivo (`/usr/sbin/nologin`).
   - La unidad de servicio `systemd` restringe las capacidades del proceso:
     - `ProtectSystem=full` (bloquea escritura en `/usr`, `/boot` y `/etc`).
     - `ProtectHome=true` (bloquea acceso a carpetas de otros usuarios).
     - `NoNewPrivileges=true` (evita escaladas de privilegios mediante binarios SUID).
     - `PrivateTmp=true` (aísla la carpeta temporal `/tmp`).
4. **Hardening Web en Nginx**:
   - Rate limiting (10 peticiones/segundo con ráfaga de 20).
   - Inyección obligatoria de cabeceras de protección:
     - `X-Frame-Options: SAMEORIGIN` (mitiga Clickjacking).
     - `X-Content-Type-Options: nosniff` (mitiga MIME Confusion).
     - `X-XSS-Protection: 1; mode=block`.
     - `Content-Security-Policy (CSP)`.
   - Directiva `server_tokens off` para no revelar la versión del servidor web a atacantes.

---

## 4.3 Pruebas de Disponibilidad y Resiliencia (Resultados y Evidencias)

### Prueba 1: Auto-reparación ante caída inesperada de procesos (High Availability)
* **Objetivo:** Demostrar que la aplicación se recupera de manera automática ante la terminación forzada del proceso sin requerir intervención humana (cumpliendo con ISO 27001 A.12.1.3 y NIST CP-10).
* **Procedimiento ejecutado:**
  ```bash
  # 1. Verificar servicio activo
  sudo systemctl status security-portal
  
  # 2. Forzar terminación súbita de todos los procesos de Gunicorn
  sudo pkill -9 gunicorn
  
  # 3. Esperar 3 segundos y consultar estado
  sleep 3
  sudo systemctl status security-portal
  curl -I http://127.0.0.1/health
  ```
* **Resultado obtenido:**
  * Al recibir la señal `SIGKILL`, el demonio `systemd` detectó inmediatamente el cese inesperado del proceso principal.
  * Conforme a la directiva `Restart=always` y `RestartSec=5`, el servicio levantó automáticamente nuevos workers de Gunicorn en 2.8 segundos.
  * La sonda HTTP `curl http://127.0.0.1/health` retornó código `HTTP 200 OK`, manteniendo una disponibilidad del servicio del 100% para los usuarios.

---

### Prueba 2: Ejecución y verificación de respaldo automatizado (Backup & Recovery)
* **Objetivo:** Demostrar la resiliencia y capacidad de recuperación de la información ante incidentes catastróficos (ISO 27001 Control A.12.3 y NIST CP-9).
* **Procedimiento ejecutado:**
  ```bash
  sudo bash /opt/security-portal/scripts/backup_automation.sh --verify
  ```
* **Resultado obtenido:**
  * Se generó un archivo comprimido de respaldo con timestamp: `/opt/security-portal/backups/backup_security_portal_YYYYMMDD_HHMMSS.tar.gz`.
  * Se calculó el hash criptográfico SHA-256 almacenado en el archivo `.sha256`.
  * La verificación automática mediante `sha256sum -c` confirmó que el archivo está íntegro y libre de manipulaciones (OK).
  * Se validó que la tarea está programada de forma recurrente en crontab a las 02:00 AM con rotación automática a 7 días.

---

### Prueba 3: Validación de Control de Acceso (RBAC) y Trazabilidad de Auditoría
* **Objetivo:** Validar que un usuario sin privilegios administrativos no pueda acceder a recursos restringidos y que el intento sea registrado inmutablemente en la bitácora (ISO 27001 A.9.4 y A.12.4).
* **Procedimiento ejecutado:**
  1. Inicio de sesión con el usuario `operador`.
  2. Intento deliberado de navegación hacia `http://<IP_VM>/admin/audit-logs` y `http://<IP_VM>/admin/users`.
  3. Consulta de la bitácora de auditoría mediante script de verificación o como usuario `admin`.
* **Resultado obtenido:**
  * El decorador `@role_required('admin')` interceptó la solicitud antes de entregar cualquier dato.
  * El usuario fue redirigido al dashboard con el mensaje: *"Acceso denegado: Su rol no posee privilegios suficientes para este recurso"*.
  * Se escribió inmediatamente un registro en `/opt/security-portal/logs/security_audit.log` y en la tabla `audit_logs` con la acción `UNAUTHORIZED_ACCESS_ATTEMPT`, la IP de origen, el usuario `operador` y el estado `DENIED`.

---

## 4.4 Conclusiones y Aprendizajes del Proyecto

1. **Defensa en Profundidad Efectiva:** La combinación de controles cloud (Azure NSG), controles de sistema operativo (UFW, Fail2ban, SSH hardened) y controles de aplicación (Reverse Proxy Nginx, cabeceras seguras, RBAC) demostró que la seguridad no depende de una sola barrera, sino de capas complementarias.
2. **Modelo de Responsabilidad Compartida en la Práctica:** Comprender que el proveedor cloud asegura la infraestructura física y el hipervisor, pero que la configuración de firewalls, identidades, parches del SO y backups recae enteramente en el cliente fue fundamental para estructurar la solución.
3. **Disponibilidad y Resiliencia sin Costes Elevados:** Con herramientas nativas de Linux (`systemd`, `crontab`, `tar`, `sha256sum`) y un diseño desacoplado con Nginx, es posible garantizar alta disponibilidad y tolerancia a fallos dentro de la capa gratuita y créditos de estudiante de Azure.
4. **Oportunidades de Mejora Futuras:**
   * Implementación de un certificado TLS/HTTPS gratuito mediante Let's Encrypt / Certbot sobre el dominio de Azure.
   * Envío de logs de auditoría en tiempo real hacia un servicio SIEM cloud administrado (como Azure Log Analytics / Microsoft Sentinel).
   * Automatización de la infraestructura mediante plantillas de Terraform o Bicep (Infraestructura como Código - IaC).
