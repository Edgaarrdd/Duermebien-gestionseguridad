# Guía Didáctica Paso a Paso: Configuración de Infraestructura en Azure, Despliegue Seguro y Pruebas de Disponibilidad

> **Asignatura:** Gestión de Seguridad de la Información — Evaluación 3 (Proyecto Integrador)  
> **Servidor Destino:** `vm-database-azure` (Ubuntu 22.04 LTS / North Central US)  
> **Dirección IP Pública (Estática):** `64.236.183.223`  
> **Usuario SSH:** `azureuser`  
> **Llave Privada SSH:** `C:\uermebien\duermebienvm.pem` (o `~/.ssh/duermebienvm.pem`)  
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

Antes de iniciar la instalación de software, debemos configurar el perímetro de red en la nube mediante el **Network Security Group (NSG)** de Azure. De fábrica, Azure bloquea todo el tráfico entrante salvo el puerto 22 (SSH). Si no habilitamos los puertos web en Azure, el navegador no podrá conectarse a la aplicación.

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
4. En la casilla **Etiqueta de nombre DNS (opcional)** (*DNS name label*), escribe un identificador único (ej: `secportal-edgard`).
5. Haz clic en **Guardar** (*Save*).
   * Tu aplicación tendrá ahora una URL fija: `http://secportal-edgard.northcentralus.cloudapp.azure.com`.

### Paso 1.3: Confirmar Parámetros de Seguridad de la VM (Para el Informe)
1. Vuelve a la máquina virtual y en el menú izquierdo ve a **Seguridad** (*Security*).
2. Verifica que figure activo el tipo de seguridad **Trusted Launch**, con **Secure Boot** y **vTPM** habilitados.  
   *(Toma una captura de pantalla de esta sección para el anexo de arquitectura de tu informe final)*.

---

## Fase 2: Preparación y Subida del Proyecto a GitHub (DevSecOps)

Para cumplir con las directrices de codificación segura (**ISO/IEC 27001 Control A.8.28**) y prevención de fuga de información sensible (**Control A.8.12**), el repositorio debe estructurarse sin credenciales planas ni bases de datos.

### Paso 2.1: Verificar que los Archivos Sensibles estén Protegidos
El proyecto incluye un archivo `.gitignore` estricto que ignora:
* Archivos de claves privadas (`*.pem`, `*.key`).
* Bases de datos locales (`*.db`, `*.sqlite3`).
* Archivos de entorno y logs (`.env`, `logs/*.log`, `backups/`).

### Paso 2.2: Inicializar Git y Subir el Proyecto
Abre **PowerShell** en tu equipo local dentro de la carpeta del proyecto (`Evaluación 3`) y ejecuta:

```powershell
# 1. Inicializar el repositorio Git local
git init

# 2. Agregar todos los archivos permitidos por .gitignore
git add .

# 3. Realizar el primer commit de la solución segura
git commit -m "feat: implementacion inicial del portal de seguridad, RBAC, hardening y documentacion ISO 27001"

# 4. Renombrar la rama principal a main
git branch -M main

# 5. Conectar tu repositorio remoto de GitHub (crea un repo vacio en github.com previamente)
# Reemplaza la URL por la de tu propio repositorio:
git remote add origin https://github.com/Edgaarrdd/Duermebien-gestionseguridad.git

# 6. Subir los archivos a GitHub
git push -u origin main
```

---

## Fase 3: Conexión y Despliegue en la Máquina Virtual (Comando por Comando)

A continuación, nos conectaremos a la máquina virtual y ejecutaremos cada instrucción paso a paso. Cada comando viene acompañado de su justificación técnica para que comprendas su función y puedas incluirla en el informe.

### Paso 3.1: Conectarse por SSH a la Máquina Virtual
Abre **PowerShell** en tu computadora y ejecuta:

```powershell
ssh -i "C:\Users\Edgard\.ssh\duermebienvm.pem" azureuser@64.236.183.223
```

> **¿Qué hace este comando?**  
> Establece un túnel criptográfico SSH (puerto 22) autenticándose mediante la llave RSA asimétrica contra la cuenta no-root `azureuser`. Cumple con el estándar **NIST AC-17 (Remote Access)**.

Una vez dentro, verás el prompt de la terminal de Linux:  
`azureuser@vm-database-azure:~$`

---

### Paso 3.2: Actualizar los Repositorios y Parches del Sistema Operativo
Ejecuta:

```bash
sudo apt-get update -y && sudo apt-get upgrade -y
```

> **¿Por qué se ejecuta?**  
> Descarga la lista actualizada de paquetes y aplica los últimos parches de seguridad del kernel y librerías de Ubuntu.  
> **Control ISO 27001 asociado:** A.12.6 Gestión de vulnerabilidades técnicas.

---

### Paso 3.3: Instalar Paquetes y Herramientas del Servidor
Ejecuta:

```bash
sudo apt-get install -y python3 python3-pip python3-venv nginx ufw fail2ban git curl tar
```

> **¿Qué instala cada paquete?**
> * `python3`, `python3-pip`, `python3-venv`: Motor de ejecución y gestor de entornos aislados para la aplicación.
> * `nginx`: Servidor web de alto rendimiento que actuará como Reverse Proxy y escudo contra ataques DoS.
> * `ufw`: Firewall interno para defensa en profundidad (*Uncomplicated Firewall*).
> * `fail2ban`: Sistema de prevención de intrusiones (IPS) contra fuerza bruta SSH.
> * `git`, `curl`, `tar`: Utilidades para clonar código, sondas de salud y respaldos.

---

### Paso 3.4: Clonar el Proyecto desde GitHub
Clonamos el proyecto en la carpeta personal de `azureuser`:

```bash
cd ~
git clone https://github.com/Edgaarrdd/Duermebien-gestionseguridad.git evaluacion3
cd evaluacion3
```

*(Reemplaza la URL por la de tu repositorio de GitHub)*.

---

### Paso 3.5: Crear el Usuario de Servicio no Privilegiado (`appuser`)
Ejecuta:

```bash
sudo useradd -r -s /usr/sbin/nologin -d /opt/security-portal appuser
```

> **¿Por qué se ejecuta?**  
> Por el **Principio de Menor Privilegio (NIST AC-6 / ISO 27001 A.9.2)**, una aplicación web **jamás** debe ejecutarse como `root` ni como un usuario con acceso interactivo. `appuser` es un usuario de sistema sin consola de inicio de sesión (`/usr/sbin/nologin`). Si un atacante lograra vulnerar la aplicación web, quedaría atrapado en este usuario sin privilegios.

---

### Paso 3.6: Preparar la Carpeta del Sistema `/opt/security-portal`
Copiamos los archivos al directorio estándar de aplicaciones en Linux y creamos las carpetas operativas:

```bash
# Crear directorio principal
sudo mkdir -p /opt/security-portal

# Copiar archivos del proyecto
sudo cp -r app scripts deploy run.py requirements.txt /opt/security-portal/

# Crear carpetas para datos, logs y respaldos
sudo mkdir -p /opt/security-portal/data
sudo mkdir -p /opt/security-portal/logs
sudo mkdir -p /opt/security-portal/backups

# Dar permisos de ejecución a los scripts bash
sudo chmod +x /opt/security-portal/scripts/*.sh
```

---

### Paso 3.7: Configurar el Entorno Virtual de Python y Dependencias
Ejecuta:

```bash
# Crear entorno virtual aislado
sudo python3 -m venv /opt/security-portal/venv

# Instalar dependencias requeridas (Flask, Gunicorn, python-dotenv)
sudo /opt/security-portal/venv/bin/pip install --upgrade pip
sudo /opt/security-portal/venv/bin/pip install -r /opt/security-portal/requirements.txt
```

> **¿Por qué un entorno virtual (`venv`)?**  
> Evita la contaminación de librerías globales del sistema operativo y asegura reproducibilidad exacta e inmutabilidad de dependencias.

---

### Paso 3.8: Inicializar la Base de Datos SQLite y Permisos Restrictivos
Ejecuta:

```bash
# Inicializar la base de datos con las tablas RBAC y usuarios de prueba
sudo /opt/security-portal/venv/bin/python -c "from app import create_app; app = create_app(); print('Base de datos inicializada correctamente')"

# Asignar la propiedad completa de los archivos a appuser
sudo chown -R appuser:appuser /opt/security-portal

# Establecer permisos estrictos (chmod 700: solo appuser puede leer/escribir sus datos)
sudo chmod 750 /opt/security-portal
sudo chmod 700 /opt/security-portal/data
sudo chmod 700 /opt/security-portal/logs
sudo chmod 700 /opt/security-portal/backups
```

> **Control ISO 27001 asociado:** A.9.4.1 Restricción del acceso a la información. La base de datos queda inaccesible para otros usuarios del servidor.

---

### Paso 3.9: Configurar el Servicio Systemd con Auto-reinicio (Alta Disponibilidad)
Ejecuta:

```bash
# Copiar archivo de servicio a systemd
sudo cp /opt/security-portal/deploy/security-portal.service /etc/systemd/system/

# Recargar el demonio de systemd para reconocer el nuevo servicio
sudo systemctl daemon-reload

# Habilitar el servicio para que inicie automáticamente al encender la VM
sudo systemctl enable security-portal

# Iniciar el servicio
sudo systemctl start security-portal

# Verificar estado activo (debe mostrar active (running) en color verde)
sudo systemctl status security-portal --no-pager
```

> **¿Cómo garantiza Alta Disponibilidad este paso?**  
> El archivo `security-portal.service` contiene las directivas `Restart=always` y `RestartSec=5`. Si la aplicación se cae por consumo de memoria, un fallo imprevisto o un error fatal, `systemd` la relanza automáticamente en 5 segundos sin necesidad de que nadie intervenga.  
> **Estándar:** ISO 27001 Control A.12.1.3 y NIST CP-10.

---

### Paso 3.10: Configurar Nginx como Proxy Inverso y Cabeceras de Seguridad
Ejecuta:

```bash
# Copiar configuración endurecida de Nginx
sudo cp /opt/security-portal/deploy/nginx.conf /etc/nginx/sites-available/security-portal

# Habilitar el sitio mediante enlace simbólico
sudo ln -sf /etc/nginx/sites-available/security-portal /etc/nginx/sites-enabled/security-portal

# Eliminar la página por defecto de Nginx
sudo rm -f /etc/nginx/sites-enabled/default

# Validar sintaxis de configuración de Nginx (debe decir: syntax is ok, test is successful)
sudo nginx -t

# Reiniciar y habilitar Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

> **¿Qué logramos aquí?**  
> 1. **Ocultamiento de tecnología:** `server_tokens off;` evita que atacantes conozcan la versión exacta del servidor.  
> 2. **Mitigación de DoS:** Aplica un límite de 10 peticiones por segundo por IP (`rate limiting`).  
> 3. **Defensa contra Clickjacking y XSS:** Inyecta cabeceras `X-Frame-Options: SAMEORIGIN` y `X-Content-Type-Options: nosniff`.  
> 4. **Aislamiento:** Nginx escucha en el puerto público 80 y redirige internamente a `127.0.0.1:8000`.

---

### Paso 3.11: Aplicar el Hardening del Sistema (Firewall UFW y Fail2ban)
Ejecuta:

```bash
sudo bash /opt/security-portal/scripts/hardening.sh
```

> **¿Qué hace este script?**  
> 1. Configura el firewall local `UFW`: Bloquea todo el tráfico entrante por defecto (`deny incoming`) y solo abre estrictamente el puerto 22 (SSH) y el puerto 80 (HTTP).  
> 2. Bloquea explícitamente los puertos estándar de bases de datos (3306, 5432, 27017) para que nadie pueda intentar conexiones directas.  
> 3. Configura `Fail2ban`: Si alguien comete 3 intentos fallidos de contraseña SSH, su IP queda baneada automáticamente por 24 horas.  
> 4. Aplica parámetros del Kernel de Linux en `/etc/sysctl.d/` para prevenir ataques de suplantación de rutas (*ICMP Redirects*) y saturación (*SYN Flood*).

---

### Paso 3.12: Configurar la Tarea de Respaldos Automáticos (Crontab)
Ejecuta:

```bash
# Registrar la tarea en el cron del sistema
sudo bash /opt/security-portal/scripts/backup_automation.sh --install-cron

# Ejecutar una prueba inmediata de respaldo con verificación de integridad
sudo bash /opt/security-portal/scripts/backup_automation.sh --verify
```

> **¿Qué logramos aquí?**  
> Se programa una tarea recurrente en Linux (`0 2 * * *`) que se ejecuta todos los días a las 02:00 AM. Comprime la base de datos y configuraciones, genera una firma hash criptográfica **SHA-256** para validar que nadie haya alterado el archivo de respaldo, y elimina automáticamente copias con más de 7 días de antigüedad.  
> **Estándar:** ISO 27001 Control A.12.3.1 (Copias de seguridad) y NIST CP-9.

---

> [!TIP]
> **Atajo Automatizado Opcional:**  
> Si en el futuro formateas la VM o necesitas reinstalar todo en un solo paso, puedes ejecutar directamente:  
> `sudo bash deploy/setup_vm.sh`  
> Este script ejecuta automáticamente todos los pasos 3.2 al 3.12 en menos de 2 minutos.

---

## Fase 4: Ejecución de Pruebas de Disponibilidad y Captura de Evidencias

Para la sección de **"Pruebas de disponibilidad y evidencias"** requerida en tu informe final, ejecuta los siguientes 4 escenarios de prueba y captura las pantallas correspondientes:

---

### Prueba 1: Acceso Web y Validación de Roles RBAC
* **Acción:** Abre tu navegador web e ingresa a:  
  `http://64.236.183.223/` (o tu dominio `http://secportal-edgard.northcentralus.cloudapp.azure.com/`).
* **Prueba con Rol Operador:**
  1. Inicia sesión con `operador` y clave `OperatorSecurity2024!`.
  2. Comprueba que puedes ver las estadísticas generales y reportar un nuevo incidente mediante el botón **Reportar Incidente**.
  3. Ahora intenta acceder manualmente en la barra de direcciones a la URL de auditoría:  
     `http://64.236.183.223/admin/audit-logs`
  4. **Resultado esperado (Captura de pantalla):** La pantalla muestra un banner rojo con el mensaje: *"Acceso denegado: Su rol no posee privilegios suficientes para este recurso (ISO 27001 A.9.4)"*.
* **Prueba con Rol Administrador (CISO):**
  1. Cierra sesión e ingresa con `admin` y clave `AdminSecurity2024!`.
  2. Haz clic en **Auditoría (ISO 27001)**.
  3. **Resultado esperado (Captura de pantalla):** Acceso concedido a la bitácora centralizada. Podrás ver reflejado el intento de intrusión o acceso no autorizado que acabas de realizar con el usuario operador bajo la acción `UNAUTHORIZED_ACCESS_ATTEMPT` con estado `DENIED`.

---

### Prueba 2: Prueba de Disponibilidad y Auto-recuperación de Servicio
* **Objetivo:** Demostrar que la aplicación se autorepara ante fallos críticos inesperados (Requisito de Disponibilidad / NIST CP-10).
* **Procedimiento:** En la terminal SSH de la VM, ejecuta:

```bash
# 1. Comprobar que el servicio está activo
sudo systemctl status security-portal --no-pager

# 2. Simular una caída catastrófica matando a la fuerza el proceso de Gunicorn
sudo pkill -9 gunicorn

# 3. Esperar 3 segundos y consultar nuevamente el estado del servicio
sleep 3
sudo systemctl status security-portal --no-pager

# 4. Probar que el servicio responde inmediatamente
curl -I http://127.0.0.1/health
```

* **Resultado esperado (Captura de pantalla de la terminal):**
  * El log de `systemctl status` mostrará que el proceso principal terminó con código de error, pero `systemd` inmediatamente registró:  
    `Scheduled restart job, restart counter is at 1... Started Portal de Seguridad`.
  * La consulta `curl -I http://127.0.0.1/health` responde de inmediato `HTTP/1.1 200 OK`.
  * **Conclusión para el informe:** El servicio web se recuperó de forma autónoma en menos de 3 segundos sin requerir intervención humana.

---

### Prueba 3: Ejecución y Verificación de Integridad de Respaldos (Backup)
* **Objetivo:** Demostrar la resiliencia de la información y la protección contra alteración de respaldos (ISO 27001 Control A.12.3).
* **Procedimiento:** En la terminal SSH de la VM, ejecuta:

```bash
sudo bash /opt/security-portal/scripts/backup_automation.sh --verify
```

* **Resultado esperado (Captura de pantalla de la terminal):**
  * Salida por pantalla:
    ```text
    [✓] Respaldo generado con éxito: /opt/security-portal/backups/backup_security_portal_YYYYMMDD_HHMMSS.tar.gz
    [✓] Hash de Integridad SHA-256: 7f83b165...
    [+] Verificando integridad del respaldo recién creado...
    backup_security_portal_...tar.gz: CORRECTO (OK)
    [✓] Prueba de recuperación y verificación de respaldo EXITOSA.
    ```
  * Para comprobar que está programado de forma recurrente, ejecuta:
    ```bash
    sudo crontab -l | grep backup_automation
    ```
    Mostrará: `0 2 * * * /bin/bash /opt/security-portal/scripts/backup_automation.sh...`

---

### Prueba 4: Inspección de la Bitácora de Auditoría en Archivo (Logging SIEM)
* **Objetivo:** Demostrar que los registros de eventos son inmutables y quedan preservados en disco para análisis forense (ISO 27001 Control A.12.4).
* **Procedimiento:** En la terminal SSH de la VM, ejecuta:

```bash
sudo tail -n 10 /opt/security-portal/logs/security_audit.log
```

* **Resultado esperado (Captura de pantalla):**
  * Registros estructurados en formato JSON con marcas de tiempo, usuario, rol, IP de origen y acción (ej: `LOGIN_SUCCESS`, `UNAUTHORIZED_ACCESS_ATTEMPT`, `INCIDENT_REPORTED`).

---

## Fase 5: Preguntas Frecuentes y Solución de Problemas (Troubleshooting)

### 1. ¿Qué hago si el navegador dice "No se puede acceder a este sitio" o "Tiempo de espera agotado"?
* **Causa principal:** Falta abrir la regla del puerto 80 en el Network Security Group (NSG) en el Portal de Azure.
* **Solución:** Revisa la **Fase 1 (Paso 1.1)** de esta guía y asegúrate de que la regla `Allow-HTTP-Inbound` en el puerto 80 tenga Acción: `Allow`.
* **Comprobación rápida en la VM:** Ejecuta `sudo ufw status` para asegurarte de que UFW muestre `80/tcp ALLOW`.

### 2. ¿Cómo ver los errores de la aplicación si algo falla?
* Para ver los registros de la aplicación en tiempo real:
  ```bash
  sudo journalctl -u security-portal -f
  ```
* Para ver los registros de error de Nginx:
  ```bash
  sudo tail -f /var/log/nginx/security_portal_error.log
  ```

### 3. ¿Cómo detener la máquina para no consumir créditos?
* Cuando termines tus pruebas o sesiones de trabajo, entra al **Portal de Azure** y haz clic en el botón **Detener** (*Stop*).
* Al estar configurada con IP **Estática**, cuando vuelvas a hacer clic en **Iniciar** (*Start*), conservará exactamente la misma IP (`64.236.183.223`) y todos los servicios se levantarán solos automáticamente.
