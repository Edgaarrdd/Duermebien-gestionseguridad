# Guía Didáctica Paso a Paso: Configuración de Infraestructura en Azure, Despliegue de Hostify Lite y Pruebas de Disponibilidad

> **Asignatura:** Gestión de Seguridad de la Información — Evaluación 3 / Proyecto Integrador (TI3V62)  
> **Servidor Destino:** `vm-database-azure` (Ubuntu 22.04 LTS / North Central US)  
> **Dirección IP Pública (Estática):** `64.236.183.223`  
> **Usuario SSH:** `azureuser`  
> **Llave Privada SSH:** `C:\Users\Edgard\.ssh\duermebienvm.pem` (o `~/.ssh/duermebienvm.pem`)  
> **Marcos de Referencia:** ISO/IEC 27001:2022, NIST SP 800-53, Cloud Security Alliance (CSA)

---

## Índice General
1. [Fase 1: Configuración en el Portal de Microsoft Azure (Perímetro Cloud)](#fase-1-configuración-en-el-portal-de-microsoft-azure-perímetro-cloud)
2. [Fase 2: Preparación y Subida del Proyecto a GitHub (DevSecOps)](#fase-2-preparación-y-subida-del-proyecto-a-github-devsecops)
3. [Fase 3: Conexión y Despliegue en la Máquina Virtual (Comando por Comando)](#fase-3-conexión-y-despliegue-en-la-máquina-virtual-comando-por-comando)
4. [Fase 4: Ejecución de Pruebas de Disponibilidad y Captura de Evidencias](#fase-4-ejecución-de-pruebas-de-disponibilidad-y-captura-de-evidencias)
5. [Fase 5: Preguntas Frecuentes y Solución de Problemas (Troubleshooting)](#fase-5-preguntas-frecuentes-y-solución-de-problemas-troubleshooting)

---

## Fase 1: Configuración en el Portal de Microsoft Azure (Perímetro Cloud)

Antes de iniciar la instalación de software, debemos configurar el perímetro de red en la nube mediante el **Network Security Group (NSG)** de Azure. De fábrica, Azure bloquea todo el tráfico entrante salvo el puerto 22 (SSH). Si no habilitamos los puertos web en Azure, el navegador no podrá conectarse a la aplicación Hostify.

### Paso 1.1: Habilitar Reglas de Entrada para el Tráfico Web (Puertos 80 y 443)
1. Inicia sesión en el [Portal de Azure](https://portal.azure.com/).
2. En la barra superior, busca y selecciona **Máquinas virtuales** y entra a **`vm-database-azure`**.
3. En el menú lateral izquierdo, haz clic en **Redes** (*Networking*).
4. En la pestaña **Reglas de puerto de entrada** (*Inbound port rules*), haz clic en el botón **+ Agregar regla de puerto de entrada** (*Add inbound rule*).
5. Completa el formulario con los siguientes valores:
   * **Origen (*Source*):** `Any` (Cualquiera).
   * **Intervalos de puertos de origen (*Source port ranges*):** `*`
   * **Destino (*Destination*):** `Any` (o `IP Addresses` con la IP de tu VM).
   * **Servicio (*Service*):** Selecciona `HTTP` en la lista desplegable (se autocompletará el puerto `80` y protocolo `TCP`).
   * **Acción (*Action*):** `Allow` (Permitir).
   * **Prioridad (*Priority*):** `100` (o un valor menor a 65000).
   * **Nombre (*Name*):** `Allow-HTTP-Inbound`
   * Haz clic en **Agregar** (*Add*).
6. *(Opcional / Recomendado)* Repite el paso para el servicio **HTTPS** (puerto `443`) con prioridad `110` y nombre `Allow-HTTPS-Inbound`.

### Paso 1.2: Asignar Nombre DNS de Estudiante Gratuito
1. En la misma pantalla de **Redes**, haz clic sobre el enlace de tu **Dirección IP pública** (`64.236.183.223`).
2. En el menú izquierdo de la IP pública, ve a **Configuración** (*Configuration*).
3. Verifica que la asignación esté en **Estática** (*Static*).
4. En la casilla **Etiqueta de nombre DNS (opcional)** (*DNS name label*), escribe un identificador único (ej: `hostify-edgard`).
5. Haz clic en **Guardar** (*Save*).
   * Tu aplicación Hostify tendrá ahora una URL fija: `http://hostify-edgard.northcentralus.cloudapp.azure.com`.

### Paso 1.3: Confirmar Parámetros de Seguridad de la VM (Para el Informe)
1. Vuelve a la máquina virtual y en el menú izquierdo ve a **Seguridad** (*Security*).
2. Verifica que figure activo el tipo de seguridad **Trusted Launch**, con **Secure Boot** y **vTPM** habilitados.  
   *(Toma una captura de pantalla de esta sección para el anexo de arquitectura de tu informe final)*.

---

## Fase 2: Preparación y Subida del Proyecto a GitHub (DevSecOps)

Para cumplir con las directrices de codificación segura (**ISO/IEC 27001 Control A.8.28**) y prevención de fuga de información sensible (**Control A.8.12**), el repositorio debe estructurarse sin credenciales planas ni bases de datos locales.

### Paso 2.1: Verificar que los Archivos Sensibles estén Protegidos
El proyecto incluye un archivo `.gitignore` estricto que ignora:
* Archivos de claves privadas (`*.pem`, `*.key`).
* Bases de datos locales (`*.db`, `*.sqlite3`).
* Archivos de entorno y logs (`.env`, `logs/*.log`, `backups/`).

### Paso 2.2: Inicializar Git y Subir el Proyecto
Abre **PowerShell** en tu equipo local dentro de la carpeta del proyecto y ejecuta:

```powershell
# 1. Verificar estado de git
git status

# 2. Agregar todos los archivos permitidos por .gitignore
git add .

# 3. Realizar commit de los cambios de la solución Hostify Lite
git commit -m "feat: implementacion de Hostify Lite, RBAC, hardening y documentacion ISO 27001"

# 4. Asegurar rama main
git branch -M main

# 5. Subir los archivos a GitHub
git push origin main
```

---

## Fase 3: Conexión y Despliegue en la Máquina Virtual (Comando por Comando)

A continuación, nos conectaremos a la máquina virtual y ejecutaremos cada instrucción paso a paso.

### Paso 3.1: Conectarse por SSH a la Máquina Virtual
Abre **PowerShell** en tu computadora y ejecuta:

```powershell
ssh -i "C:\Users\Edgard\.ssh\duermebienvm.pem" azureuser@64.236.183.223
```

> **¿Qué hace este comando?**  
> Establece un túnel criptográfico SSH (puerto 22) autenticándose mediante la llave RSA asimétrica contra la cuenta no-root `azureuser`. Cumple con el estándar **NIST AC-17 (Remote Access)**.

---

### Paso 3.2: Actualizar los Repositorios y Parches del Sistema Operativo
Ejecuta:

```bash
sudo apt-get update -y && sudo apt-get upgrade -y
```

> **Control ISO 27001 asociado:** A.12.6 Gestión de vulnerabilidades técnicas.

---

### Paso 3.3: Instalar Paquetes y Herramientas del Servidor
Ejecuta:

```bash
sudo apt-get install -y python3 python3-pip python3-venv nginx ufw fail2ban git curl tar
```

---

### Paso 3.4: Clonar el Proyecto desde GitHub
Clonamos el proyecto en la carpeta personal de `azureuser`:

```bash
cd ~
git clone https://github.com/Edgaarrdd/Duermebien-gestionseguridad.git evaluacion3
cd evaluacion3
```

---

### Paso 3.5: Crear el Usuario de Servicio no Privilegiado (`appuser`)
Ejecuta:

```bash
sudo useradd -r -s /usr/sbin/nologin -d /opt/security-portal appuser
```

> **Principio de Menor Privilegio (NIST AC-6 / ISO 27001 A.9.2):** `appuser` es un usuario de sistema sin consola de inicio de sesión (`/usr/sbin/nologin`). Si un atacante lograra vulnerar la aplicación web, quedaría confinado sin privilegios de administración.

---

### Paso 3.6: Preparar la Carpeta del Sistema `/opt/security-portal`
Copiamos los archivos al directorio estándar de aplicaciones en Linux y creamos las carpetas operativas:

```bash
sudo mkdir -p /opt/security-portal
sudo cp -r app scripts deploy run.py requirements.txt /opt/security-portal/
sudo mkdir -p /opt/security-portal/data
sudo mkdir -p /opt/security-portal/logs
sudo mkdir -p /opt/security-portal/backups
sudo chmod +x /opt/security-portal/scripts/*.sh
```

---

### Paso 3.7: Configurar el Entorno Virtual de Python y Dependencias
Ejecuta:

```bash
sudo python3 -m venv /opt/security-portal/venv
sudo /opt/security-portal/venv/bin/pip install --upgrade pip
sudo /opt/security-portal/venv/bin/pip install -r /opt/security-portal/requirements.txt
```

---

### Paso 3.8: Inicializar la Base de Datos SQLite y Permisos Restrictivos
Ejecuta:

```bash
# Inicializar la base de datos con las tablas de Hostify (habitaciones, huespedes, reservas, auditoria)
sudo /opt/security-portal/venv/bin/python -c "from app import create_app; app = create_app(); print('Base de datos inicializada correctamente')"

# Asignar la propiedad completa de los archivos a appuser
sudo chown -R appuser:appuser /opt/security-portal

# Establecer permisos estrictos (chmod 700: solo appuser puede leer/escribir sus datos)
sudo chmod 750 /opt/security-portal
sudo chmod 700 /opt/security-portal/data
sudo chmod 700 /opt/security-portal/logs
sudo chmod 700 /opt/security-portal/backups
```

---

### Paso 3.9: Configurar el Servicio Systemd con Auto-reinicio (Alta Disponibilidad)
Ejecuta:

```bash
sudo cp /opt/security-portal/deploy/security-portal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable security-portal
sudo systemctl start security-portal
sudo systemctl status security-portal --no-pager
```

> **¿Cómo garantiza Alta Disponibilidad este paso?**  
> Directivas `Restart=always` y `RestartSec=5`. Si la aplicación se cae, `systemd` la relanza automáticamente en 5 segundos sin intervención humana (**ISO 27001 A.12.1.3 y NIST CP-10**).

---

### Paso 3.10: Configurar Nginx como Proxy Inverso y Cabeceras de Seguridad
Ejecuta:

```bash
sudo cp /opt/security-portal/deploy/nginx.conf /etc/nginx/sites-available/security-portal
sudo ln -sf /etc/nginx/sites-available/security-portal /etc/nginx/sites-enabled/security-portal
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

### Paso 3.11: Aplicar el Hardening del Sistema (Firewall UFW y Fail2ban)
Ejecuta:

```bash
sudo bash /opt/security-portal/scripts/hardening.sh
```

---

### Paso 3.12: Configurar la Tarea de Respaldos Automáticos (Crontab)
Ejecuta:

```bash
sudo bash /opt/security-portal/scripts/backup_automation.sh --install-cron
sudo bash /opt/security-portal/scripts/backup_automation.sh --verify
```

> [!TIP]
> **Atajo Automatizado Opcional:**  
> También puedes ejecutar en un solo paso:  
> `sudo bash deploy/setup_vm.sh`

---

## Fase 4: Ejecución de Pruebas de Disponibilidad y Captura de Evidencias

Para la sección de evidencias de tu informe final, ejecuta los siguientes 4 escenarios de prueba y captura las pantallas correspondientes:

---

### Prueba 1: Acceso Web y Validación de Roles RBAC en Hostify
* **Acción:** Abre tu navegador web e ingresa a:  
  `http://64.236.183.223/` (o tu DNS público de Azure).
* **Prueba con Rol Encargado (Recepción):**
  1. Inicia sesión con usuario `encargado` y contraseña `EncargadoSecurity2024!`.
  2. Comprueba que puedes ver el Dashboard con las habitaciones disponibles/ocupadas, registrar un huésped en `/guests` y crear una reserva en `/reservations`.
  3. Ahora intenta acceder manualmente en la barra de direcciones a la URL de auditoría:  
     `http://64.236.183.223/admin/audit-logs`
  4. **Resultado esperado (Captura de pantalla):** La pantalla muestra un banner rojo con el mensaje: *"Acceso denegado: Su rol no posee privilegios suficientes para este recurso (ISO 27001 A.9.4)"*.
* **Prueba con Rol Administrador:**
  1. Cierra sesión e ingresa con `admin` y contraseña `AdminSecurity2024!`.
  2. Haz clic en **Auditoría (ISO 27001)**.
  3. **Resultado esperado (Captura de pantalla):** Acceso concedido a la bitácora centralizada. Podrás ver reflejado el intento de acceso no autorizado del recepcionista bajo la acción `UNAUTHORIZED_ACCESS_ATTEMPT` con estado `DENIED`.

---

### Prueba 2: Prueba de Disponibilidad y Auto-recuperación de Servicio
* **Objetivo:** Demostrar que Hostify se autorepara ante fallos críticos inesperados (Requisito de Disponibilidad / NIST CP-10).
* **Procedimiento:** En la terminal SSH de la VM, ejecuta:

```bash
sudo systemctl status security-portal --no-pager
sudo pkill -9 gunicorn
sleep 3
sudo systemctl status security-portal --no-pager
curl -I http://127.0.0.1/health
```

* **Resultado esperado (Captura de pantalla):**
  * `systemd` registra la auto-recuperación: `Scheduled restart job, restart counter is at 1... Started Portal de Seguridad`.
  * La consulta `curl -I http://127.0.0.1/health` responde inmediatamente `HTTP/1.1 200 OK`.

---

### Prueba 3: Ejecución y Verificación de Integridad de Respaldos (Backup)
* **Objetivo:** Demostrar la resiliencia de la información de reservas y huéspedes (ISO 27001 Control A.12.3).
* **Procedimiento:** En la terminal SSH de la VM, ejecuta:

```bash
sudo bash /opt/security-portal/scripts/backup_automation.sh --verify
```

* **Resultado esperado (Captura de pantalla):**
  * Salida por pantalla:
    ```text
    [✓] Respaldo generado con éxito: /opt/security-portal/backups/backup_security_portal_YYYYMMDD_HHMMSS.tar.gz
    [✓] Hash de Integridad SHA-256: ...
    [+] Verificando integridad del respaldo recién creado...
    backup_security_portal_...tar.gz: CORRECTO (OK)
    [✓] Prueba de recuperación y verificación de respaldo EXITOSA.
    ```

---

### Prueba 4: Inspección de la Bitácora de Auditoría en Archivo (Logging SIEM)
* **Objetivo:** Demostrar que los registros de eventos son inmutables y quedan preservados en disco para análisis forense (ISO 27001 Control A.12.4).
* **Procedimiento:** En la terminal SSH de la VM, ejecuta:

```bash
sudo tail -n 10 /opt/security-portal/logs/security_audit.log
```

* **Resultado esperado (Captura de pantalla):**
  * Registros estructurados en formato JSON con marcas de tiempo, usuario, rol, IP de origen y acción (ej: `LOGIN_SUCCESS`, `UNAUTHORIZED_ACCESS_ATTEMPT`, `GUEST_CREATED`, `RESERVATION_CREATED`).

---

## Fase 5: Preguntas Frecuentes y Solución de Problemas (Troubleshooting)

### 1. ¿Qué hago si el navegador dice "No se puede acceder a este sitio" o "Tiempo de espera agotado"?
* **Causa principal:** Falta abrir la regla del puerto 80 en el Network Security Group (NSG) en el Portal de Azure.
* **Solución:** Revisa la **Fase 1 (Paso 1.1)** de esta guía y asegúrate de que la regla `Allow-HTTP-Inbound` en el puerto 80 tenga Acción: `Allow`.

### 2. ¿Cómo ver los errores de la aplicación si algo falla?
* Registros de la aplicación Hostify en tiempo real:
  ```bash
  sudo journalctl -u security-portal -f
  ```
* Registros de Nginx:
  ```bash
  sudo tail -f /var/log/nginx/security_portal_error.log
  ```

### 3. ¿Cómo detener la máquina para no consumir créditos?
* Cuando termines tus pruebas o sesiones de trabajo, entra al **Portal de Azure** y haz clic en el botón **Detener** (*Stop*).
* Al estar configurada con IP **Estática**, conservará la misma IP (`64.236.183.223`) y todos los servicios arrancarán solos al iniciar.
