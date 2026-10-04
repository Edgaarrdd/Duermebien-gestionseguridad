# Manual Integral: Creación de VM en Azure, Despliegue de Hostify Lite y Captura de Evidencias

> **Asignatura:** Gestión de Seguridad de la Información (TI3V62)  
> **Proyecto:** Hostify Lite - Sistema de Gestión de Hostales Seguro y de Alta Disponibilidad  
> **Objetivo:** Guiar paso a paso desde la creación de la máquina virtual en Microsoft Azure hasta la puesta en marcha de la aplicación y la captura sistemática de todas las evidencias requeridas para el informe final.

---

## 📑 Contenido del Manual
1. [Módulo 1: Creación y Configuración de la VM en Microsoft Azure](#módulo-1-creación-y-configuración-de-la-vm-en-microsoft-azure)
2. [Módulo 2: Configuración Perimetral de Red y Dirección IP Estática (NSG)](#módulo-2-configuración-perimetral-de-red-y-dirección-ip-estática-nsg)
3. [Módulo 3: Conexión SSH y Despliegue Automatizado de Hostify Lite](#módulo-3-conexión-ssh-y-despliegue-automatizado-de-hostify-lite)
4. [Módulo 4: Guía de Captura de Evidencias Paso a Paso (Para el Informe)](#módulo-4-guía-de-captura-de-evidencias-paso-a-paso-para-el-informe)
5. [Módulo 5: Resumen de Comandos Útiles y Solución de Problemas](#módulo-5-resumen-de-comandos-útiles-y-solución-de-problemas)

---

## Módulo 1: Creación y Configuración de la VM en Microsoft Azure

Sigue estos pasos dentro del [Portal de Azure (portal.azure.com)](https://portal.azure.com/):

### Paso 1.1: Iniciar el Asistente de Creación
1. En la barra de búsqueda superior, escribe **Máquinas virtuales** (*Virtual machines*) y haz clic en el servicio.
2. Haz clic en **+ Crear** (*+ Create*) y selecciona **Máquina virtual de Azure** (*Azure virtual machine*).

### Paso 1.2: Pestaña "Datos básicos" (*Basics*)
Configura los siguientes campos:
* **Suscripción (*Subscription*):** Selecciona tu suscripción activa (ej: *Azure for Students* o suscripción de evaluación).
* **Grupo de recursos (*Resource group*):** Haz clic en **Crear nuevo** y nómbralo `rg-hostify-cloud` (o selecciona uno existente).
* **Nombre de la máquina virtual (*Virtual machine name*):** `vm-hostify-azure`
* **Región (*Region*):** `(US) North Central US` (o `East US` / `South Central US`).
* **Opciones de disponibilidad (*Availability options*):** *No se requiere redundancia de la infraestructura* (*No infrastructure redundancy required*).
* **Tipo de seguridad (*Security type*):** **Inicio de confianza (*Trusted Launch*)**.  
  *(Asegúrate de que queden marcadas las casillas de **Arranque seguro (Secure Boot)** y **vTPM**; esto cumple con el estándar de aislamiento del hardware).*
* **Imagen (*Image*):** **Ubuntu Server 22.04 LTS - x64 Gen2**.
* **Arquitectura de máquina virtual (*VM architecture*):** `x64`.
* **Tamaño (*Size*):** **Standard_B1s** (1 vCPU, 1 GiB de memoria RAM).  
  *(Este tamaño es 100% elegible para la capa gratuita y suficiente para Hostify Lite).*

### Paso 1.3: Cuenta de Administrador (*Administrator account*)
* **Tipo de autenticación (*Authentication type*):** **Clave pública SSH (*SSH public key*)**.
* **Nombre de usuario (*Username*):** `azureuser`
* **Origen de clave pública SSH (*SSH public key source*):**
  * Si ya tienes una clave: Selecciona *Usar clave pública existente* y pega tu clave.
  * Si vas a generar una nueva: Selecciona **Generar nuevo par de claves (*Generate new key pair*)** y dale el nombre `hostifyvm-key`.

### Paso 1.4: Reglas de Puertos de Entrada Básicas (*Inbound port rules*)
* **Puertos de entrada públicos (*Public inbound ports*):** Selecciona **Permitir los puertos seleccionados**.
* **Seleccionar puertos de entrada (*Select inbound ports*):** Marca únicamente **SSH (22)**.

### Paso 1.5: Pestaña "Discos" (*Disks*)
* **Tipo de disco de SO (*OS disk type*):** **SSD Estándar** (Standard SSD) o **HDD Estándar** (para optimizar créditos).
* Deja las demás opciones predeterminadas.

### Paso 1.6: Pestaña "Redes" (*Networking*)
* **Red virtual (*Virtual network*):** Se creará automáticamente (ej: `rg-hostify-cloud-vnet`).
* **Subred (*Subnet*):** `default (10.0.0.0/24)`.
* **IP pública (*Public IP*):** Deja la opción de crear nueva IP pública (ej: `vm-hostify-azure-ip`).
* **Grupo de seguridad de red de NIC (*NIC network security group*):** Selecciona **Básico (*Basic*)** o **Avanzado**.

### Paso 1.7: Revisar y Crear (*Review + Create*)
1. Haz clic en el botón azul **Revisar y crear**.
2. Azure validará los parámetros. Haz clic en **Crear**.
3. *Si generaste un nuevo par de claves, se abrirá una ventana emergente:* Haz clic en **Descargar la clave privada y crear el recurso**.  
   *Guarda el archivo descargado (ej: `hostifyvm-key.pem`) en una carpeta segura de tu equipo (por ejemplo: `C:\Users\Edgard\.ssh\hostifyvm-key.pem`).*
4. Espera 1 a 2 minutos hasta que Azure confirme: **Se completó la implementación**. Haz clic en **Ir al recurso**.

---

## Módulo 2: Configuración Perimetral de Red y Dirección IP Estática (NSG)

Para que el hostal pueda recibir tráfico web en el puerto 80 y mantener una IP fija que no cambie al apagar la máquina:

### Paso 2.1: Fijar la IP Pública como Estática y Asignar Nombre DNS
1. En el menú de la VM, ve a la sección **Redes** (*Networking*) en el menú lateral izquierdo.
2. Haz clic sobre el enlace azul de tu **Dirección IP pública** (ej: `20.xxx.xxx.xxx`).
3. En el menú izquierdo de la IP, haz clic en **Configuración** (*Configuration*).
4. En **Asignación (*Assignment*)**, cambia de Dinámica a **Estática (*Static*)**.
5. En **Etiqueta de nombre DNS (opcional)** (*DNS name label*), escribe un nombre único en minúsculas (ej: `hostify-edgard-inacap`).
6. Haz clic en **Guardar** (*Save*).  
   *Anota la IP pública y tu dominio asignado: `http://hostify-edgard-inacap.northcentralus.cloudapp.azure.com`.*

### Paso 2.2: Configurar las Reglas de Entrada en el Network Security Group (NSG)
Vuelve a la pantalla de la máquina virtual y en el menú izquierdo entra a **Redes** (*Networking*):
1. En la pestaña **Reglas de puerto de entrada** (*Inbound port rules*), haz clic en **+ Agregar regla de puerto de entrada** (*Add inbound rule*).
2. **Regla para Tráfico Web (HTTP):**
   * **Origen (*Source*):** `Any`
   * **Intervalos de puertos de origen:** `*`
   * **Destino (*Destination*):** `Any`
   * **Servicio (*Service*):** Selecciona `HTTP` (puerto `80`, protocolo `TCP`).
   * **Acción (*Action*):** `Allow`
   * **Prioridad (*Priority*):** `100`
   * **Nombre (*Name*):** `Allow-HTTP-Inbound`
   * Haz clic en **Agregar**.
3. *(Opcional / Recomendado)* **Regla para Tráfico Seguro (HTTPS):**
   * Repite el proceso para el servicio `HTTPS` (puerto `443`), Prioridad `110`, Nombre `Allow-HTTPS-Inbound`.
4. **Regla de Bloqueo Perimetral de Bases de Datos:**
   * Haz clic en **+ Agregar regla de puerto de entrada**.
   * **Intervalos de puertos de destino:** `3306, 5432, 27017`
   * **Protocolo:** `TCP`
   * **Acción:** `Deny`
   * **Prioridad:** `120`
   * **Nombre:** `Deny-Database-Internet`
   * Haz clic en **Agregar**.

---

## Módulo 3: Conexión SSH y Despliegue Automatizado de Hostify Lite

### Paso 3.1: Ajustar Permisos de la Llave SSH en Windows (PowerShell)
Abre **PowerShell** en tu computadora. Si descargaste una llave `.pem` nueva, Windows requiere restringir sus permisos para que SSH la acepte:

```powershell
# Ubícate donde guardaste tu llave (ejemplo: C:\Users\Edgard\.ssh\)
cd C:\Users\Edgard\.ssh\

# Restringir permisos en Windows (equivalente a chmod 400 en Linux)
icacls.exe hostifyvm-key.pem /reset
icacls.exe hostifyvm-key.pem /grant:r "$($env:USERNAME):(R)"
icacls.exe hostifyvm-key.pem /inheritance:r
```

### Paso 3.2: Conectarse a la Máquina Virtual
Reemplaza con tu archivo `.pem` y la IP pública de tu VM:

```powershell
ssh -i "C:\Users\Edgard\.ssh\hostifyvm-key.pem" azureuser@<TU_IP_PUBLICA_AZURE>
```
*(Si te pregunta `Are you sure you want to continue connecting (yes/no)?`, escribe `yes` y presiona Enter).*

Verás el prompt de Ubuntu: `azureuser@vm-hostify-azure:~$`

### Paso 3.3: Clonar el Repositorio de Hostify Lite
Dentro de la sesión SSH en la VM, ejecuta:

```bash
cd ~
git clone https://github.com/Edgaarrdd/Duermebien-gestionseguridad.git evaluacion3
cd evaluacion3
```

### Paso 3.4: Ejecutar el Despliegue Automatizado en Un Solo Paso
Ejecuta el script maestro con permisos de superusuario:

```bash
sudo bash deploy/setup_vm.sh
```

El script realizará de forma 100% autónoma en menos de 2 minutos:
1. Actualización del sistema e instalación de paquetes base (`python3`, `nginx`, `ufw`, `fail2ban`, `curl`, `tar`).
2. Creación del usuario de servicio no privilegiado `appuser` (sin consola de login).
3. Preparación del entorno de producción en `/opt/security-portal/`.
4. Creación del entorno virtual Python e instalación de librerías.
5. Inicialización de la base de datos SQLite con inventario de habitaciones, cuentas RBAC y logs.
6. Puesta en marcha de la unidad de servicio `systemd` con auto-reinicio inmediato (`Restart=always`).
7. Configuración de Nginx como proxy inverso con limitación de tasa (*Rate Limiting*) y cabeceras de endurecimiento HTTP.
8. Configuración del firewall local UFW y protección contra fuerza bruta con Fail2ban.
9. Instalación de la tarea programada de respaldo automático con hash SHA-256 en crontab a las 02:00 AM.
10. Comprobación de la sonda de salud local (`curl http://127.0.0.1/health`).

Al finalizar, verás el mensaje: `[+] DESPLIEGUE COMPLETADO EXITOSAMENTE`.

---

## Módulo 4: Guía de Captura de Evidencias Paso a Paso (Para el Informe)

A continuación se detalla la lista de capturas de pantalla exactas que debes tomar para adjuntar en las secciones del informe final:

---

### 📸 Evidencia 1: Seguridad de la Infraestructura en Azure (Trusted Launch y NSG)
* **Dónde ir en el Portal de Azure:**
  1. En tu máquina virtual, ve al menú izquierdo **Seguridad (*Security*)**:
     * **Qué capturar:** La pantalla donde se observe el tipo de seguridad **Trusted Launch**, con **Secure Boot: Enabled** y **vTPM: Enabled**.  
       *(Demuestra cumplimiento del criterio 4.1.2 y modelo de responsabilidad compartida).*
  2. En el menú izquierdo ve a **Redes (*Networking*)**:
     * **Qué capturar:** La tabla de reglas del NSG donde figuren las reglas `Allow-HTTP-Inbound` (puerto 80), `Allow-SSH-Admin` (puerto 22) y `Deny-Database-Internet` (puertos 3306, 5432).  
       *(Demuestra cumplimiento del criterio 4.1.4 y segmentación de red).*

---

### 📸 Evidencia 2: Aplicación Hostify Lite y Control de Acceso RBAC

#### A. Inicio de Sesión y Dashboard Operativo (Rol Encargado)
1. Abre tu navegador web e ingresa a: `http://<TU_IP_PUBLICA>/` (o tu DNS de Azure).
2. Inicia sesión con las credenciales del recepcionista:
   * **Usuario:** `encargado`
   * **Contraseña:** `EncargadoSecurity2024!`
3. **Qué capturar:** El **Dashboard principal de Hostify**, mostrando las estadísticas de habitaciones (Disponibles, Ocupadas, Reservas Pendientes, Huéspedes) y el menú superior con las opciones *Dashboard*, *Habitaciones*, *Huéspedes* y *Reservas*.

#### B. Registro de Huésped y Creación de Reserva (Rol Encargado)
1. Haz clic en **Huéspedes** (`/guests`), completa el formulario con un nuevo pasajero (ej: *Carlos Valenzuela*, *carlos@email.com*, *+56911223344*) y haz clic en **Guardar Huésped**.
2. Haz clic en **Reservas** (`/reservations`), selecciona una habitación disponible y el huésped recién creado, e ingresa fechas de check-in / check-out.
3. **Qué capturar:** La tabla de reservas actualizada con el registro activo.

#### C. Demostración de Acceso Denegado (Violación RBAC Control A.9.4)
1. Estando conectado como `encargado`, escribe manualmente en la barra de direcciones del navegador:  
   `http://<TU_IP_PUBLICA>/admin/audit-logs` (o `/admin/users`).
2. Presiona Enter.
3. **Qué capturar:** El banner de alerta rojo en pantalla que indica:  
   **"Acceso denegado: Su rol no posee privilegios suficientes para este recurso (ISO 27001 A.9.4)."**  
   *(Evidencia crucial de que un usuario operativo no puede escalar privilegios).*

#### D. Bitácora de Auditoría Forense (Rol Administrador CISO)
1. Cierra sesión e inicia sesión con el rol de administración:
   * **Usuario:** `admin`
   * **Contraseña:** `AdminSecurity2024!`
2. En la barra de navegación, haz clic en **Auditoría (ISO 27001)** (`/admin/audit-logs`).
3. **Qué capturar:** La tabla de auditoría donde se visualiza el registro inmutable con acción:  
   `UNAUTHORIZED_ACCESS_ATTEMPT` con estado `DENIED`, usuario `encargado` y la IP de origen.

---

### 📸 Evidencia 3: Prueba de Alta Disponibilidad y Resiliencia (Auto-reinicio)
* **Objetivo:** Demostrar que el sistema se autorepara sin intervención humana (ISO 27001 A.12.1.3 y NIST CP-10).
* **Procedimiento:** En la terminal SSH de la VM, copia y pega el siguiente bloque de comandos:

```bash
# 1. Verificar estado activo
sudo systemctl status security-portal --no-pager

# 2. Forzar caída catastrófica matando violentamente los procesos de Gunicorn
sudo pkill -9 gunicorn

# 3. Esperar 3 segundos para que Systemd actúe
sleep 3

# 4. Verificar recuperación automática y respuesta de la sonda de salud
sudo systemctl status security-portal --no-pager
curl -I http://127.0.0.1/health
```

* **Qué capturar:** La salida de la terminal donde se aprecia:
  1. `Main process exited, code=killed, status=9/KILL`
  2. `Scheduled restart job, restart counter is at 1... Started Hostify`
  3. `HTTP/1.1 200 OK` (Recuperación en menos de 3 segundos).

---

### 📸 Evidencia 4: Respaldo Automatizado y Verificación Criptográfica SHA-256
* **Objetivo:** Demostrar la resiliencia de los datos y el control anti-manipulación (ISO 27001 Control A.12.3 y NIST CP-9).
* **Procedimiento:** En la terminal SSH de la VM, ejecuta:

```bash
# Ejecutar verificación de respaldo
sudo bash /opt/security-portal/scripts/backup_automation.sh --verify

# Verificar tarea programada en crontab
sudo crontab -l | grep backup_automation
```

* **Qué capturar:** La salida de la terminal mostrando:
  1. `[✓] Respaldo generado con éxito: /opt/security-portal/backups/backup_security_portal_...tar.gz`
  2. `[✓] Hash de Integridad SHA-256: <HASH_HEX>`
  3. `backup_security_portal_...tar.gz: CORRECTO (OK)`
  4. La línea de crontab: `0 2 * * * /bin/bash /opt/security-portal/scripts/backup_automation.sh...`

---

### 📸 Evidencia 5: Bitácora de Auditoría en Archivo (Logging SIEM)
* **Objetivo:** Demostrar que los registros de eventos son inmutables y quedan preservados en disco para análisis forense (ISO 27001 Control A.12.4).
* **Procedimiento:** En la terminal SSH de la VM, ejecuta:

```bash
sudo tail -n 15 /opt/security-portal/logs/security_audit.log
```

* **Qué capturar:** Los eventos estructurados en formato JSON con marca de tiempo, usuario, rol, IP y acción (`LOGIN_SUCCESS`, `UNAUTHORIZED_ACCESS_ATTEMPT`, `GUEST_CREATED`, `RESERVATION_CREATED`).

---

### 📸 Evidencia 6: Batería de Pruebas Unitarias Automatizadas
* **Procedimiento:** En la terminal SSH de la VM (o en tu equipo local), ejecuta:

```bash
python3 -m unittest discover tests
```

* **Qué capturar:** La salida de la terminal con las 7 pruebas aprobadas:
  ```text
  .......
  ----------------------------------------------------------------------
  Ran 7 tests in 2.255s

  OK
  ```

---

## Módulo 5: Resumen de Comandos Útiles y Solución de Problemas

### 1. ¿Cómo ver los registros de la aplicación en tiempo real?
```bash
sudo journalctl -u security-portal -f
```

### 2. ¿Cómo reiniciar manualmente los servicios?
```bash
sudo systemctl restart security-portal
sudo systemctl restart nginx
```

### 3. ¿Cómo revisar el estado del firewall y Fail2ban?
```bash
sudo ufw status verbose
sudo fail2ban-client status sshd
```

### 4. ¿Qué hacer si el navegador muestra "No se puede acceder a este sitio"?
* Comprueba que la regla `Allow-HTTP-Inbound` en el puerto 80 de tu NSG en Azure esté en estado `Allow`.
* Comprueba que Nginx esté corriendo con `sudo systemctl status nginx`.
* Comprueba que UFW tenga abierto el puerto 80 con `sudo ufw status`.

### 5. ¿Cómo apagar la VM al terminar para no consumir créditos?
* Entra al [Portal de Azure](https://portal.azure.com/), busca `vm-hostify-azure` y haz clic en **Detener (*Stop*)**.
* Al haber configurado la IP como **Estática**, conservará la misma IP y al darle **Iniciar (*Start*)** todo se levantará automáticamente sin tener que reconfigurar nada.
