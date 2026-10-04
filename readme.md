# Hostify Lite - Sistema de Gestión de Hostales (Cloud Seguro y Disponible)
### Proyecto Integrador: Gestión de Seguridad de la Información (TI3V62) — Evaluación 3 / 4

Solución web para gestión operativa de hostales basada en el diseño de **Hostify**, simplificada para cumplir rigurosamente con los requisitos del **Proyecto Integrador** en la nube de **Microsoft Azure**, alineada con **ISO/IEC 27001**, **NIST SP 800-53 / CSF**, **Cloud Security Alliance (CSA)** y el **Modelo de Responsabilidad Compartida**.

---

## 🏨 ¿Qué es Hostify Lite?
**Hostify Lite** es una versión ágil, segura y optimizada de la plataforma de gestión hotelera Hostify. Resuelve la problemática de hostales y alojamientos turísticos independientes que gestionan reservas y datos de huéspedes de forma manual o vulnerable, eliminando sobrecargas innecesarias y concentrándose en los módulos clave del negocio:
1. **Control de Habitaciones:** Monitoreo y cambio de estados en tiempo real (`DISPONIBLE`, `OCUPADA`, `LIMPIEZA`, `MANTENIMIENTO`) y control de tarifas por noche.
2. **Directorio de Huéspedes:** Registro seguro y protegido de información personal de clientes (PII) bajo la Ley Nº 19.628 y estándares de privacidad.
3. **Gestión de Reservas:** Asignación de habitaciones con fechas de check-in / check-out y seguimiento de ciclo de vida (`PENDIENTE`, `CONFIRMADA`, `CANCELADA`, `COMPLETADA`).
4. **Dashboard de Ocupación:** Visualización en tiempo real de disponibilidad, habitaciones ocupadas y reservas activas.
5. **Control de Acceso Basado en Roles (RBAC):** Privilegios diferenciados entre el personal de recepción (`encargado`) y la gerencia / administración (`admin`).
6. **Bitácora Inmutable de Auditoría:** Trazabilidad de cada inicio de sesión, cambio de habitación y registro inmediato de intentos no autorizados conforme al control **A.12.4 de ISO 27001**.

---

## 📂 Estructura del Proyecto

```
Duermebien-gestionseguridad/
├── app/                              # Código fuente de Hostify Lite (Python / Flask)
│   ├── __init__.py                   # Fábrica de aplicación e inyección de cabeceras de seguridad
│   ├── config.py                     # Configuración de producción, llaves secretas y cookies seguras
│   ├── models.py                     # Esquema SQLite, tablas RBAC (users, rooms, guests, reservations, audit_logs)
│   ├── auth.py                       # Decoradores RBAC y logger estructurado de auditoría (JSON)
│   ├── routes.py                     # Controladores y endpoints de Hostify
│   └── templates/                    # Interfaz web responsiva (Hostify Dark Theme + Tailwind CSS)
│       ├── base.html                 # Plantilla base con menú contextual según rol
│       ├── login.html                # Formulario de inicio de sesión seguro con aviso legal
│       ├── dashboard.html            # Panel de control de KPIs de ocupación y reservas
│       ├── rooms.html                # Catálogo de habitaciones y cambio de estados (Solo Admin)
│       ├── guests.html               # Formulario de registro y listado de huéspedes
│       ├── reservations.html         # Creación y gestión del ciclo de reservas
│       ├── admin_users.html          # Gestión y provisión de usuarios del sistema (Solo Admin)
│       └── audit_logs.html           # Bitácora centralizada de eventos y alertas (Solo Admin)
├── deploy/                           # Archivos de aprovisionamiento en Azure VM (Ubuntu 22.04)
│   ├── nginx.conf                    # Proxy inverso con Rate Limiting y cabeceras de endurecimiento
│   ├── security-portal.service       # Demonio Systemd con auto-restart (< 5s) para Alta Disponibilidad
│   └── setup_vm.sh                   # Script automatizado de despliegue en un solo paso
├── scripts/                          # Automatización de resiliencia y endurecimiento
│   ├── hardening.sh                  # Endurecimiento del sistema (UFW, Fail2ban, SSH RSA, Sysctl)
│   └── backup_automation.sh          # Respaldo automatizado diario con firma criptográfica SHA-256 en crontab
├── tests/                            # Batería de pruebas automatizadas (100% aprobadas)
│   ├── __init__.py
│   └── test_app.py                   # Pruebas unitarias de RBAC, headers, auth y CRUD
├── docs/                             # Documentación técnica completa para la entrega académica
│   ├── 1_descripcion_y_arquitectura.md                     # Descripción, problemática y arquitectura 5 capas
│   ├── 2_matriz_de_riesgos_iso27001_nist_csa.md            # Matriz de riesgos, impacto, controles y residuales
│   ├── 3_configuracion_iam_azure.md                        # Azure Entra ID, Managed Identity y RBAC de Hostify
│   ├── 4_seguridad_red_hardening_y_pruebas_disponibilidad.md# Red, segmentación, hardening y pruebas
│   └── guia_paso_a_paso_configuracion_vm.md                # Manual detallado de despliegue y Azure NSG
├── Hostify/                          # Repositorio de referencia UI/UX original
├── requirements.txt                  # Dependencias de Python (Flask, Gunicorn, Werkzeug, python-docx)
├── run.py                            # Punto de entrada de ejecución
└── Proyecto_integrador.docx          # Informe formal completo para entrega académica
```

---

## 🔐 Credenciales de Acceso Demostrativas (RBAC)

| Rol | Usuario | Contraseña | Capacidades y Alcance |
| :--- | :--- | :--- | :--- |
| **Administrador General (CISO / Gerente)** | `admin` | `AdminSecurity2024!` | Gestión de usuarios, cambio de estado de habitaciones (mantenimiento/limpieza), consulta de bitácora central de auditoría ISO 27001 y control global. |
| **Encargado de Recepción (Front Desk)** | `encargado` | `EncargadoSecurity2024!` | Visualización de disponibilidad, registro de huéspedes, creación de reservas y dashboard operativo. *(Acceso bloqueado a módulos administrativos con registro automático de alertas)*. |

---

## 🚀 Despliegue Rápido en Máquina Virtual Azure (`vm-database-azure`)

### 1. Conexión SSH
```powershell
ssh -i "C:\Users\Edgard\.ssh\duermebienvm.pem" azureuser@64.236.183.223
```

### 2. Clonar y Desplegar
```bash
git clone https://github.com/Edgaarrdd/Duermebien-gestionseguridad.git evaluacion3
cd evaluacion3
sudo bash deploy/setup_vm.sh
```

El script configurará de forma automatizada:
1. Instalación de paquetes base (`python3`, `nginx`, `ufw`, `fail2ban`, `curl`, `tar`).
2. Creación del usuario de servicio no privilegiado `appuser` (sin shell interactivo).
3. Entorno virtual Python con dependencias instaladas.
4. Inicialización de la base de datos de Hostify con inventario y cuentas preconfiguradas.
5. Unidad de servicio Systemd con directiva de auto-reinicio (`Restart=always`).
6. Configuración de Nginx como proxy inverso, rate limiting y cabeceras de seguridad.
7. Aplicación de reglas de firewall UFW y protección contra fuerza bruta con Fail2ban.
8. Tarea diaria en crontab a las 02:00 AM para copias de seguridad con hash SHA-256.

---

## 🧪 Ejecución de Pruebas Unitarias Automatizadas

Para validar los controles de seguridad y disponibilidad localmente o en el servidor:
```bash
python -m unittest discover tests
```
*Resultado: **7 de 7 pruebas exitosas** (`test_health_check`, `test_security_headers`, `test_login_success_admin`, `test_login_failed_invalid_credentials`, `test_rbac_encargado_restricted_from_admin_areas`, `test_rbac_admin_allowed_in_admin_areas`, `test_guest_creation_and_audit`).*

---

## 📖 Documentación Completa del Proyecto Integrador
Para consultar en detalle cada sección del informe exigido por la pauta docente, revisa:
* 👉 **[1. Descripción y Arquitectura de Seguridad](docs/1_descripcion_y_arquitectura.md)**
* 👉 **[2. Matriz de Riesgos (ISO 27001 / NIST / CSA)](docs/2_matriz_de_riesgos_iso27001_nist_csa.md)**
* 👉 **[3. Configuración IAM en Azure y Hostify](docs/3_configuracion_iam_azure.md)**
* 👉 **[4. Seguridad de Red, Hardening y Pruebas de Disponibilidad](docs/4_seguridad_red_hardening_y_pruebas_disponibilidad.md)**
* 👉 **[Guía Paso a Paso de Configuración en VM Azure](docs/guia_paso_a_paso_configuracion_vm.md)**
