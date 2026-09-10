# Hostify - Sistema de Gestión Hotelera (Seguro)
### Proyecto Integrador: Gestión de Seguridad de la Información - Evaluación 3

Solución web para gestión hotelera (basada en el diseño de Hostify) segura, disponible y alineada con los marcos **ISO/IEC 27001**, **NIST SP 800-53/800-61**, **Cloud Security Alliance (CSA)** y el **Modelo de Responsabilidad Compartida**.

---

## 📂 Estructura del Proyecto

```
Evaluación 3/
├── app/                              # Código fuente de la aplicación Flask
│   ├── __init__.py                   # Fábrica de aplicación e inyección de cabeceras HTTP
│   ├── config.py                     # Variables de configuración y cookies seguras
│   ├── models.py                     # Esquema SQLite, tablas RBAC y sembrado inicial
│   ├── auth.py                       # Decoradores RBAC y módulo de auditoría estructurada
│   ├── routes.py                     # Controladores (Dashboard, Habitaciones, Huéspedes, Reservas)
│   └── templates/                    # Interfaz HTML5 + Tailwind CSS (Diseño SOC Dark Mode / Hostify)
│       ├── base.html                 # Layout maestro con navegación por roles
│       ├── login.html                # Login seguro con aviso de auditoría ISO 27001
│       ├── dashboard.html            # Panel de KPIs, estado de habitaciones y reservas
│       ├── rooms.html                # Listado de habitaciones y cambio de estados
│       ├── guests.html               # Formulario de registro y listado de huéspedes
│       ├── reservations.html         # Creación y gestión de reservas
│       ├── admin_users.html          # Directorio y provisión de usuarios (Solo Admin)
│       └── audit_logs.html           # Bitácora centralizada de eventos (Solo Admin)
├── deploy/                           # Archivos de despliegue en VM Azure
│   ├── nginx.conf                    # Proxy inverso con rate limiting y cabeceras de seguridad
│   ├── security-portal.service       # Demonio Systemd con auto-restart para alta disponibilidad
│   └── setup_vm.sh                   # Script automatizado de despliegue en un solo paso
├── scripts/                          # Scripts de seguridad y disponibilidad
│   ├── hardening.sh                  # Endurecimiento Ubuntu 22.04 (UFW, Fail2ban, SSH, Sysctl)
│   └── backup_automation.sh          # Respaldo automatizado diario con hash SHA-256 en crontab
├── tests/                            # Pruebas unitarias y de integración automatizadas
│   ├── __init__.py
│   └── test_app.py                   # Pruebas de RBAC, login, headers y endpoints
├── docs/                             # Informes técnicos y anexos para la entrega
│   ├── guia_paso_a_paso_configuracion_vm.md # Manual detallado comando a comando y Azure NSG
│   ├── 1_descripcion_y_arquitectura.md
│   ├── 2_matriz_de_riesgos_iso27001_nist_csa.md
│   ├── 3_configuracion_iam_azure.md
│   └── 4_seguridad_red_hardening_y_pruebas_disponibilidad.md
├── Hostify/                          # Código fuente Next.js original de Hostify usado como plantilla/referencia
├── .gitignore                        # Prevención de fuga de credenciales (.pem, .db, .env)
├── .env.example                      # Plantilla de variables de entorno
├── requirements.txt                  # Dependencias de Python
└── run.py                            # Punto de entrada de la aplicación
```

---

## 📖 Manual de Despliegue Paso a Paso

Para ver la **guía detallada comando por comando**, la configuración del **Network Security Group (NSG)** en Azure y el procedimiento para capturar las evidencias del informe, consulta:
👉 **[guia_paso_a_paso_configuracion_vm.md](docs/guia_paso_a_paso_configuracion_vm.md)**

---

## 🚀 Despliegue Rápido en la Máquina Virtual de Azure (`vm-database-azure`)

### 1. Conectar por SSH
Desde PowerShell:
```powershell
ssh -i "C:\Users\Edgard\.ssh\duermebienvm.pem" azureuser@64.236.183.223
```

### 2. Clonar desde GitHub y ejecutar
```bash
git clone https://github.com/Edgaarrdd/Duermebien-gestionseguridad.git evaluacion3
cd evaluacion3
sudo bash deploy/setup_vm.sh
```

El script configurará automáticamente:
1. Instalación de paquetes base (`python3`, `nginx`, `ufw`, `fail2ban`, `curl`).
2. Creación del usuario de servicio no privilegiado `appuser`.
3. Creación del entorno virtual y descarga de dependencias.
4. Inicialización de la base de datos con usuarios y eventos de prueba.
5. Puesta en marcha del servicio `systemd` con reinicio automático ante caídas.
6. Configuración de Nginx como proxy inverso y cabeceras de seguridad.
7. Aplicación de reglas de firewall UFW y protección de SSH con Fail2ban.
8. Programación de la tarea de respaldos automáticos diarios con verificación SHA-256 en cron.

---

## 🔐 Credenciales de Acceso Demostrativas (RBAC)

| Rol | Usuario | Contraseña | Capacidades |
| :--- | :--- | :--- | :--- |
| **Administrador (CISO)** | `admin` | `AdminSecurity2024!` | Gestión de usuarios, consulta de bitácora de auditoría ISO 27001, resolución de incidentes, cambio estado de habitaciones. |
| **Encargado (Recepción)** | `encargado` | `EncargadoSecurity2024!` | Gestión de reservas, huéspedes y visualización del panel general (acceso denegado a funciones administrativas). |

---

## 🧪 Ejecución de Pruebas Automatizadas
Para verificar el correcto funcionamiento local:
```bash
python -m unittest discover tests
```
*Resultado: 7 pruebas ejecutadas con éxito (Health, Security Headers, Login, RBAC Encargado Denied, RBAC Admin Allowed, Creación de Huéspedes).*
