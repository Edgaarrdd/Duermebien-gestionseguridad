# Hostify Lite - Sistema de Gestión de Hostales (Cloud Seguro y Disponible)

## Proyecto Integrador: Gestión de Seguridad de la Información (TI3V62)

Hostify Lite es una solución web para la gestión operativa de hostales, diseñada para cumplir con los requisitos del proyecto integrador en Microsoft Azure y con estándares de seguridad como ISO/IEC 27001, NIST CSF, CSA y el modelo de responsabilidad compartida.

Este repositorio incluye la aplicación, el despliegue automatizado en máquina virtual Ubuntu 22.04, la documentación técnica y la evidencia capturada para la entrega académica.

---

## ¿Qué incluye este proyecto?

- Gestión de habitaciones con estados y tarifas.
- Directorio de huéspedes con información sensible protegida.
- Gestión de reservas y ciclo de vida.
- Dashboard operativo con indicadores de ocupación.
- Control de acceso basado en roles (RBAC).
- Auditoría y registro de eventos para detección de accesos no autorizados.
- Endurecimiento del sistema y despliegue seguro en Azure.
- Evidencias y documentación para la evaluación final.

---

## Estructura del proyecto

```text
Duermebien-gestionseguridad/
├── app/                               # Código fuente de la aplicación Flask
│   ├── __init__.py                    # Fábrica de la app e inyección de cabeceras de seguridad
│   ├── auth.py                        # Lógica de autenticación y validaciones RBAC
│   ├── config.py                      # Configuración general y secretos
│   ├── models.py                      # Modelos de base de datos y esquema del sistema
│   ├── routes.py                      # Endpoints principales de la aplicación
│   └── templates/                     # Vistas HTML del sistema
│       ├── admin_users.html
│       ├── audit_logs.html
│       ├── base.html
│       ├── dashboard.html
│       ├── guests.html
│       ├── login.html
│       ├── reservations.html
│       └── rooms.html
├── deploy/                            # Archivos de despliegue en Azure VM
│   ├── nginx.conf
│   ├── security-portal.service
│   └── setup_vm.sh
├── scripts/                           # Hardening, respaldos y automatización operativa
│   ├── backup_automation.sh
│   └── hardening.sh
├── tests/                             # Pruebas automatizadas
│   ├── __init__.py
│   └── test_app.py
├── docs/                              # Documentación y evidencias del proyecto
│   ├── 1_descripcion_y_arquitectura.md
│   ├── 2_matriz_de_riesgos_iso27001_nist_csa.md
│   ├── 3_configuracion_iam_azure.md
│   ├── 4_seguridad_red_hardening_y_pruebas_disponibilidad.md
│   ├── guia_paso_a_paso_configuracion_vm.md
│   ├── manual_creacion_vm_y_evidencias.md
│   ├── capturas y evidencias/
│   ├── Informe_Final_Proyecto_Integrador_Hostify.docx
│   └── Proyecto_integrador_pauta_original.docx
├── Hostify/                           # Repositorio de referencia UI/UX original
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
└── Proyecto_integrador.docx
```

---

## Usuarios y credenciales demo

- Administrador: `admin` / `AdminSecurity2024!`
- Encargado: `encargado` / `EncargadoSecurity2024!`

Estas credenciales están pensadas para demostración del modelo RBAC y para la validación de accesos no autorizados.

---

## Requisitos

- Python 3.10+
- Dependencias definidas en `requirements.txt`
- Sistema operativo Linux para despliegue real en Azure VM
- Acceso a Microsoft Azure para la creación de la VM

---

## Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Luego accede a la aplicación desde el navegador en:

```text
http://localhost:5000
```

---

## Despliegue automatizado en Azure

Se incluye un script de automatización para preparar la máquina virtual y dejar la aplicación operativa en un paso:

```bash
cd ~
git clone https://github.com/Edgaarrdd/Duermebien-gestionseguridad.git evaluacion3
cd evaluacion3
sudo bash deploy/setup_vm.sh
```

El despliegue realiza, entre otras tareas:

- Instalación de dependencias del sistema
- Configuración de usuarios y permisos
- Preparación del entorno virtual Python
- Inicialización de la base de datos
- Configuración de Nginx como proxy inverso
- Habilitación del servicio de la app con Systemd
- Hardening de seguridad con UFW y Fail2ban
- Copias de seguridad automáticas con validación SHA-256
- Recuperación automática ante fallo del servicio

---

## Pruebas automatizadas

Ejecuta la validación del sistema con:

```bash
python -m unittest discover tests
```

Resultado esperado: pruebas de seguridad, RBAC, autenticación, auditoría y control de acceso aprobadas.

---

## Documentación del proyecto

Se encuentra toda la documentación técnica y la evidencia para la entrega final en la carpeta `docs/`:

- [1. Descripción y arquitectura](docs/1_descripcion_y_arquitectura.md)
- [2. Matriz de riesgos ISO 27001 / NIST / CSA](docs/2_matriz_de_riesgos_iso27001_nist_csa.md)
- [3. Configuración IAM en Azure](docs/3_configuracion_iam_azure.md)
- [4. Seguridad de red, hardening y pruebas de disponibilidad](docs/4_seguridad_red_hardening_y_pruebas_disponibilidad.md)
- [Guía paso a paso de configuración en VM Azure](docs/guia_paso_a_paso_configuracion_vm.md)
- [Manual integral de creación de VM y evidencias](docs/manual_creacion_vm_y_evidencias.md)
- [Carpeta de capturas y evidencias](docs/capturas%20y%20evidencias)

---

## Evidencias y entrega académica

El proyecto incluye una ruta documental completa para justificar la implementación y la seguridad operativa del sistema. En particular, el manual de creación de VM y evidencias describe:

- Creación de la máquina virtual en Microsoft Azure
- Configuración de red y reglas NSG
- Conexión SSH segura
- Despliegue automatizado de Hostify Lite
- Captura de evidencias de acceso, RBAC y auditoría
- Verificación de alta disponibilidad y respaldo automático

---

## Resumen

Hostify Lite combina una interfaz simple, control de acceso por roles, hardening de infraestructura y documentación integral para cumplir con una arquitectura segura en la nube. El proyecto está preparado para demostración, despliegue en Azure y entrega como evidencia académica para la evaluación de gestión de seguridad de la información.
