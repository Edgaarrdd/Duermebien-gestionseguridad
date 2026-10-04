# 1. Descripción de la Solución y Arquitectura de Seguridad

## 1.1 Descripción de la Solución
### ¿Qué problema resuelve la aplicación y para quién?
En el rubro del turismo y hospedaje —especialmente en hostales independientes y hoteles boutique—, la administración operativa suele llevarse a cabo mediante procesos manuales, libretas de papel o planillas de cálculo compartidas sin cifrado ni control de acceso. Según estudios del **Cloud Security Alliance (CSA)** y la **Agencia de la Unión Europea para la Ciberseguridad (ENISA)**, los sistemas de gestión hotelera desactualizados o informales son blanco recurrente de filtración de datos, secuestro de información (ransomware) y pérdidas de disponibilidad en horas de alta concurrencia.

Esta falta de madurez tecnológica ocasiona tres riesgos críticos:
1. **Fuga y compromiso de Datos de Carácter Personal (PII):** Los datos de contacto, identificación y estancia de los huéspedes quedan expuestos a accesos no autorizados, violando la **Ley Chilena Nº 19.628 sobre Protección de la Vida Privada** y marcos internacionales como el **RGPD**.
2. **Indisponibilidad y sobreventa (Overbooking):** La pérdida de conexión o la caída de los servidores durante los turnos de check-in/check-out paraliza la recepción y genera pérdidas económicas y reputacionales directas.
3. **Ausencia de separación de funciones y trazabilidad:** El personal de recepción y la administración suelen usar credenciales genéricas compartidas, impidiendo identificar quién modificó una tarifa, quién alteró el estado de una habitación o quién manipuló una reserva.

### La Solución: Hostify Lite (Sistema de Gestión de Hostales Seguro)
**Hostify Lite** es una aplicación web de gestión hostelera simplificada, modular y segura, diseñada específicamente para resolver las necesidades operativas de recepcionistas y administradores, cumpliendo estrictamente con los requerimientos de seguridad, disponibilidad y auditoría del **Proyecto Integrador (Evaluación 3 - TI3V62)**.

A diferencia de soluciones comerciales sobrecargadas, Hostify Lite implementa únicamente la funcionalidad esencial del negocio:
* **Control de Inventario de Habitaciones:** Registro de número, tipo (Sencilla, Doble, Suite), tarifa por noche y control de estado en tiempo real (`DISPONIBLE`, `OCUPADA`, `LIMPIEZA`, `MANTENIMIENTO`).
* **Directorio de Huéspedes:** Registro protegido de datos personales con validación de entradas.
* **Gestión de Reservas:** Asignación de habitaciones con cálculo de estancias (check-in / check-out) y estados de ciclo de vida (`PENDIENTE`, `CONFIRMADA`, `CANCELADA`, `COMPLETADA`).
* **Dashboard de Ocupación:** Métricas clave en tiempo real para la toma de decisiones del personal de turno.
* **Control de Acceso Basado en Roles (RBAC):** Privilegios estrictamente diferenciados entre el rol de **Encargado de Recepción** y el rol de **Administrador General**.
* **Bitácora Inmutable de Auditoría (Logging ISO 27001 / NIST):** Registro estructurado de cada autenticación, cambio de estado de habitación y cualquier intento de escalada o acceso denegado.

---

## 1.2 Modelo de Responsabilidad Compartida (CSA / Microsoft Azure)
El despliegue de Hostify Lite se realiza bajo el modelo **IaaS (Infraestructura como Servicio)** sobre una máquina virtual en **Microsoft Azure (Ubuntu 22.04 LTS - `vm-database-azure`)**:

| Capa / Dominio | Responsable | Medidas Aplicadas en Hostify Lite | Marco de Referencia |
| :--- | :--- | :--- | :--- |
| **Seguridad Física y Datacenter** | Microsoft Azure | Control de acceso físico, climatización y redundancia de energía en la región `northcentralus`. | CSA CCM DC-01 |
| **Hipervisor y Hardware Virtual** | Microsoft Azure | Habilitación de arquitectura **Trusted Launch**, con **Secure Boot** y **vTPM** activados en la VM. | NIST SP 800-145 |
| **Perímetro de Red Cloud** | Compartida | Reglas de entrada y salida estrictas en el **Network Security Group (NSG)** de Azure, bloqueando puertos de BD y permitiendo solo HTTP/HTTPS y SSH restringido. | ISO 27001 A.13.1 / CSA IVS-06 |
| **Sistema Operativo (Guest OS)** | Cliente (Nosotros) | Parcheo continuo de seguridad, firewall host `UFW`, prevención de fuerza bruta con `Fail2ban`, llaves SSH RSA (sin passwords) y hardening de kernel con `sysctl`. | NIST SP 800-123 / ISO 27001 A.12.1 |
| **Gestión de Identidades (IAM)** | Cliente (Nosotros) | Azure RBAC sin uso de la cuenta raíz/propietario para la operación cotidiana. Uso de identidades no privilegiadas. | NIST AC-6 (Least Privilege) / ISO 27001 A.9.2 |
| **Capa de Aplicación y Software** | Cliente (Nosotros) | Aplicación Hostify con control RBAC (`@role_required`), inyección de cabeceras HTTP de seguridad (`X-Frame-Options`, `CSP`, `nosniff`), y ejecución sin privilegios de root (`appuser`). | ISO 27001 A.14.2 / OWASP Top 10 |
| **Datos y Resiliencia** | Cliente (Nosotros) | Base de datos local aislada con permisos `chmod 600`, contraseñas con hash criptográfico PBKDF2/SHA-256, y respaldos diarios automatizados con verificación SHA-256 en crontab. | ISO 27001 A.12.3 / NIST CP-9 |

---

## 1.3 Diagrama de Arquitectura de Seguridad (Defensa en Profundidad)

```
                       [ RECEPCIÓN / ADMINISTRACIÓN / HUÉSPED ]
                                         │
                         (Petición HTTP vía Internet - Puerto 80)
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────┐
│ 1. PERÍMETRO CLOUD (Azure Virtual Network / Network Security Group - NSG)       │
│    - Puerto 80 (HTTP): Permitido para acceso a la aplicación Hostify            │
│    - Puerto 22 (SSH): Permitido para gestión de administración autorizada       │
│    - Puertos de Bases de Datos (3306, 5432, 27017): DENEGADOS hacia Internet    │
│    - Regla DenyAllInbound por defecto para cualquier otro puerto                │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────┐
│ 2. SISTEMA OPERATIVO Y RED HOST (Ubuntu 22.04 LTS - Trusted Launch vTPM)        │
│    - Firewall UFW interno (Default Deny Incoming / Puertos 80, 22 abiertos)     │
│    - Fail2ban activo (Jail sshd: bloqueo por 24h tras 3 intentos fallidos)      │
│    - SSH Hardened (PermitRootLogin no, PasswordAuthentication no, solo RSA)     │
│    - Parámetros de Kernel sysctl (Protección anti-SYN Flood, ICMP drops)        │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────┐
│ 3. CAPA PROXY INVERSO & MITIGACIÓN DoS (Nginx 1.18)                            │
│    - Rate Limiting (10 req/s con ráfaga de 20 por IP) para mitigar saturación   │
│    - Ocultación de huella tecnológica (server_tokens off)                       │
│    - Cabeceras de seguridad inyectadas: X-Frame-Options, X-Content-Type, CSP    │
│    - Bloqueo de archivos ocultos y rutas no autorizadas (dotfiles)              │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ (Proxy Pass local a 127.0.0.1:8000)
┌────────────────────────────────────────▼────────────────────────────────────────┐
│ 4. CAPA DE APLICACIÓN WEB HOSTIFY (Gunicorn WSGI + Flask Python 3)              │
│    - Ejecución aislada bajo el usuario de sistema 'appuser' (sin shell interactivo)│
│    - Sandboxing Systemd: ProtectSystem=full, ProtectHome=true, PrivateTmp=true │
│    - Control RBAC en rutas: Encargado (Recepción) vs Administrador (General)   │
│    - Generador de bitácora de auditoría inmutable (security_audit.log + DB)     │
│    - Resiliencia Systemd: Restart=always (Auto-reinicio automático en < 5s)     │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ (I/O Local en Disco Protegido)
┌────────────────────────────────────────▼────────────────────────────────────────┐
│ 5. CAPA DE DATOS Y RESPALDOS (SQLite Encapsulada + Crontab)                     │
│    - Archivo /opt/security-portal/data/portal_security.db (Permisos chmod 600)  │
│    - Cero sockets TCP abiertos (inmune a escaneos y ataques de red remotos)     │
│    - Contraseñas almacenadas exclusivamente con PBKDF2/SHA-256 + Salt           │
│    - Respaldo diario en Crontab (02:00 AM) con firma criptográfica SHA-256      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.4 Descripción de Componentes y Mecanismos de Seguridad

1. **Perímetro Cloud (Azure NSG `vm-database-azure-nsg`):** Filtra todo el tráfico entrante a nivel perimetral de Azure antes de que los paquetes alcancen la interfaz de red virtual `vm-database-azure624`.
2. **Reverse Proxy (Nginx):** Recibe las solicitudes HTTP públicas, absorbe picos de tráfico mediante *rate limiting*, mitiga ataques de denegación de servicio (DoS) y añade cabeceras HTTP de protección contra ataques de cliente (*Clickjacking*, *MIME Sniffing* y *XSS*).
3. **Servidor de Aplicaciones (Gunicorn WSGI):** Administra 3 procesos *workers* enlazados exclusivamente al bucle local (`127.0.0.1:8000`). La aplicación Hostify jamás expone puertos directos a redes públicas.
4. **Sandboxing de Sistema Operativo (`appuser` + Systemd):** La aplicación corre bajo un usuario sin privilegios administrativos (`appuser`) que no posee consola de inicio de sesión (`/usr/sbin/nologin`). Systemd bloquea modificaciones sobre el sistema operativo mediante directivas de contención (`ProtectSystem=full`, `NoNewPrivileges=true`).
5. **Módulo de Trazabilidad y Auditoría:** Cada intento de login, creación de reserva, cambio de estado de habitación y denegación de acceso genera un evento JSON en `/opt/security-portal/logs/security_audit.log` y en la tabla `audit_logs` de la base de datos, cumpliendo con **ISO/IEC 27001 (A.12.4)** y **NIST SP 800-92**.
6. **Mecanismo de Resiliencia y Recuperación (Alta Disponibilidad):**
   * **Systemd Watchdog:** Supervisa el proceso de Hostify. Si se presenta un fallo imprevisto, caída o sobrecarga, el servicio es relanzado de forma autónoma en 5 segundos.
   * **Crontab de Respaldo Criptográfico:** A las 02:00 AM, empaqueta la base de datos y configuraciones, genera una firma hash **SHA-256** para certificar su integridad (anti-tampering) y purga copias mayores a 7 días.

---

## 1.5 Pertinencia Tecnológica e Ingeniería de Software (Criterios 4.1.1 y 4.1.2)
* **¿Por qué Flask + SQLite + Nginx para Hostify Lite?**  
  Para hostales pequeños y medianos, una arquitectura de microservicios con múltiples contenedores y clústeres orquestados resulta sobredimensionada, costosa y genera una superficie de ataque innecesariamente grande.  
  La arquitectura monolítica ligera de Hostify Lite opera con menos de 180 MB de memoria RAM, garantizando tiempos de respuesta inferiores a 40 ms sobre la capa gratuita de Azure (**Standard B1s**: 1 vCPU, 1 GiB RAM), alcanzando máxima eficiencia de costos, alta disponibilidad y un perfil de seguridad sumamente robusto.
