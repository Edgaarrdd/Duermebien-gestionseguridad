# 1. Descripción de la Solución y Arquitectura de Seguridad

## 1.1 Descripción de la Solución
### ¿Qué problema resuelve la aplicación y para quién?
En organizaciones modernas que operan en entornos de nube, la falta de visibilidad sobre incidentes de seguridad y el uso inadecuado de privilegios administrativos representan dos de las principales causas de brechas de datos (según reportes de ENISA y el Cloud Security Alliance - CSA).

El **Portal de Gestión de Incidentes de Seguridad (SOC Portal)** es una solución web diseñada para equipos de operaciones de TI y seguridad informática (SOC / CISO). La aplicación permite:
* Centralizar el reporte y seguimiento de incidentes de seguridad clasificados por nivel de criticidad (Crítico, Alto, Medio, Bajo).
* Aplicar un **Control de Acceso Basado en Roles (RBAC)** estricto, separando las funciones operativas de las funciones de auditoría y administración de identidades.
* Garantizar trazabilidad completa (logging inmutable) de eventos de autenticación, cambios de estado y accesos no autorizados, conforme al control **A.12.4 de ISO/IEC 27001** y la guía **NIST SP 800-92**.

---

## 1.2 Modelo de Responsabilidad Compartida (CSA / Microsoft Azure)
El despliegue se fundamenta en el modelo de responsabilidad compartida para **Infraestructura como Servicio (IaaS)**:

| Capa / Dominio | Responsable | Medidas Aplicadas en el Proyecto |
| :--- | :--- | :--- |
| **Seguridad Física y Datacenter** | Microsoft Azure | Seguridad de instalaciones físicas en la región `northcentralus`. |
| **Hipervisor y Hardware Virtual** | Microsoft Azure | Trusted Launch, Secure Boot y vTPM habilitados en la VM `vm-database-azure`. |
| **Perímetro de Red Cloud** | Compartida | Network Security Group (NSG) con reglas restrictivas que bloquean puertos no autorizados. |
| **Sistema Operativo (Guest OS)** | Cliente (Nosotros) | Parcheo continuo, firewall UFW, protección SSH con Fail2ban y configuración sysctl. |
| **Gestión de Identidades (IAM)** | Cliente (Nosotros) | Azure RBAC sin uso de credenciales de propietario/raíz para tareas cotidianas. |
| **Aplicación y Datos** | Cliente (Nosotros) | Sanitización, contraseñas con hash PBKDF2/SHA-256, cabeceras HTTP y respaldo diario. |

---

## 1.3 Diagrama de Arquitectura de Seguridad (Defensa en Profundidad)

```
                       [ USUARIO / AUDITOR ]
                                 │
                 (Petición HTTP/HTTPS vía Internet)
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│ 1. PERÍMETRO CLOUD (Azure Virtual Network / NSG)               │
│    - Puerto 80 / 443: Permitido para tráfico Web               │
│    - Puerto 22 (SSH): Restringido a IP de administración        │
│    - Puertos BD (5432, 3306): DENEGADOS hacia Internet         │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│ 2. SISTEMA OPERATIVO (Ubuntu 22.04 LTS - Trusted Launch)       │
│    - Firewall interno UFW activo                               │
│    - Fail2ban mitigando ataques de fuerza bruta                │
│    - SSH Hardened (sin passwords, solo claves RSA)             │
│    - Parámetros de Kernel sysctl (anti SYN Flood)              │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│ 3. CAPA PROXY INVERSO & WEB (Nginx)                             │
│    - Rate Limiting (10 req/s con burst) contra DoS             │
│    - Cabeceras HTTP: X-Frame-Options, X-Content-Type, CSP       │
│    - Ocultación de cabeceras de versión (server_tokens off)    │
└────────────────────────────────┬────────────────────────────────┘
                                 │ (Proxy Pass: 127.0.0.1:8000)
┌────────────────────────────────▼────────────────────────────────┐
│ 4. CAPA DE APLICACIÓN (Gunicorn + Flask / appuser)             │
│    - Ejecución en aislamiento sin privilegios de root           │
│    - Control de Acceso RBAC (Admin vs Operador)                │
│    - Módulo de auditoría estructurada (JSON)                   │
│    - Systemd Daemon con auto-reinicio (Restart=always)         │
└────────────────────────────────┬────────────────────────────────┘
                                 │ (Lectura / Escritura Local)
┌────────────────────────────────▼────────────────────────────────┐
│ 5. CAPA DE DATOS Y DISPONIBILIDAD (SQLite Encapsulada)         │
│    - Base de datos local protegida (permisos chmod 600)        │
│    - Sin socket de red expuesto                                │
│    - Cron automatizado: Respaldos diarios + Checksum SHA-256   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1.4 Descripción de Componentes
1. **Perímetro Cloud (Azure NSG)**: Filtra el tráfico antes de que alcance la interfaz de red (`vm-database-azure624`).
2. **Reverse Proxy (Nginx)**: Recibe las conexiones entrantes, aplica limitación de tasa (*rate limiting*) para mitigar denegación de servicio (DoS) e inyecta directivas de seguridad para proteger a los clientes contra *Clickjacking*, *MIME sniffing* y *Cross-Site Scripting (XSS)*.
3. **Servidor de Aplicaciones (Gunicorn)**: Maneja múltiples procesos de trabajo (*workers*) de Python enlazados exclusivamente a la interfaz de bucle local (`127.0.0.1`), garantizando que la aplicación no exponga puertos no controlados.
4. **Módulo de Trazabilidad y Auditoría**: Registra de forma inmediata cada intento de autenticación y cambio de estado, tanto en la base de datos como en un archivo de log local inmutable (`/opt/security-portal/logs/security_audit.log`).
5. **Mecanismo de Resiliencia (Systemd + Cron)**:
   - **Systemd**: Vigila el proceso de la aplicación y lo reinicia automáticamente en menos de 5 segundos si ocurre un fallo no controlado.
   - **Cron de Respaldo**: Ejecuta diariamente a las 02:00 AM el empaquetado de la base de datos y genera un hash SHA-256 para verificar la no alteración del respaldo.
