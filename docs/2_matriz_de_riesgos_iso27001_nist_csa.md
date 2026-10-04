# 2. Matriz de Gestión de Riesgos (ISO/IEC 27001, NIST SP 800-30 y CSA CCM)

## 2.1 Criterios de Evaluación y Metodología
La gestión de riesgos de seguridad de la información para el sistema **Hostify Lite** se desarrolló tomando como base los lineamientos de la norma **ISO/IEC 27005** y la guía metodológica **NIST SP 800-30 Rev. 1**:

* **Probabilidad de Ocurrencia (P):**
  * `1` - Muy Baja (Casi improbable; requiere capacidades altamente sofisticadas).
  * `2` - Baja (Poco probable que ocurra en el corto o mediano plazo).
  * `3` - Media (Factible; existen vectores de ataque conocidos y automatizados).
  * `4` - Alta (Muy probable; amenazas frecuentes en servicios cloud públicos).
  * `5` - Muy Alta (Inminente; ataques recurrentes diarios en internet).

* **Impacto Operacional y de Negocio (I):**
  * `1` - Insignificante (Sin impacto en la operación del hostal ni daño a la privacidad).
  * `2` - Menor (Molestias operativas menores sin pérdida financiera ni de datos).
  * `3` - Moderado (Interrupción temporal de la recepción; datos recuperables).
  * `4` - Grave (Paralización de check-in/check-out; filtración de PII de huéspedes).
  * `5` - Catastrófico (Pérdida definitiva de reservas, sanción legal por Ley 19.628 o quiebra).

* **Nivel de Riesgo (NR = P × I):**
  * **1 a 6:** `Bajo` (Riesgo Aceptable; monitoreo periódico).
  * **8 a 12:** `Medio` (Riesgo Tolerable con controles preventivos).
  * **15 a 25:** `Alto / Crítico` (Inaceptable; requiere mitigación obligatoria antes de operar).

---

## 2.2 Matriz de Riesgos y Controles de Mitigación para Hostify Lite

| ID | Amenaza / Escenario de Riesgo | Activo Afectado | P | I | NR (Inicial) | Control ISO/IEC 27001 (Anexo A) | Control NIST SP 800-53 / CSF | Control CSA CCM v4 | Medida Técnica Implementada en Hostify Lite | P_res | I_res | NR (Residual) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **R-01** | **Compromiso de cuenta raíz / propietario en Azure:** Uso de credenciales maestras de suscripción en la administración diaria de la infraestructura del hostal. | Suscripción Azure y Recursos Cloud | 3 | 5 | **15 (Alto)** | **A.9.2.3** Gestión de derechos de acceso privilegiado | **AC-2, AC-6** (Principle of Least Privilege) | **IAM-01** Identity & Access Management | Se prohíbe el uso de la cuenta Owner en la operación cotidiana. Creación de grupos RBAC en Azure Entra ID con permisos delegados (`Virtual Machine Contributor`, `Reader`). | 1 | 4 | **4 (Bajo)** |
| **R-02** | **Ataque de fuerza bruta contra el puerto de gestión SSH:** Escaneo masivo y ataques automatizados contra el puerto 22 de la máquina virtual del hostal. | Servidor Host (Ubuntu 22.04) | 5 | 4 | **20 (Crítico)** | **A.9.4.2** Procedimientos de inicio de sesión seguro | **AC-7** (Unsuccessful Logon Attempts) | **IAM-09** Authentication & Password Policy | Bloqueo absoluto de autenticación por contraseña (`PasswordAuthentication no`). Autenticación obligatoria por llave RSA y jaula Fail2ban que banea por 24h tras 3 intentos. | 1 | 3 | **3 (Bajo)** |
| **R-03** | **Caída de servicio durante turnos de recepción y horas punta:** Error en código o sobrecarga de peticiones que paralice el check-in / check-out de huéspedes. | Disponibilidad de la Aplicación | 4 | 4 | **16 (Crítico)** | **A.12.1.3** Gestión de capacidad y disponibilidad | **CP-2, CP-10** (Contingency Plan / Recovery) | **BCR-02** Business Continuity & Resiliency | Watchdog de Systemd con auto-reinicio inmediato (`Restart=always`, reinicio en < 5s) y Rate Limiting en Nginx (10 req/s con ráfaga) para mitigar sobrecarga DoS. | 1 | 2 | **2 (Bajo)** |
| **R-04** | **Pérdida o corrupción de la base de datos del hostal:** Fallo de almacenamiento, eliminación accidental o secuestro de datos (ransomware). | Base de Datos (Reservas y Huéspedes) | 3 | 5 | **15 (Alto)** | **A.12.3.1** Copias de seguridad de la información | **CP-9** (Information System Backup) | **DSP-05** Data Resiliency & Backup | Script automatizado diario en crontab (`0 2 * * *`) que empaqueta la base de datos, calcula suma criptográfica SHA-256 (anti-tampering) y rota respaldos a 7 días. | 1 | 2 | **2 (Bajo)** |
| **R-05** | **Acceso no autorizado o escalada de privilegios a la gestión de usuarios:** Recepcionista intenta acceder a auditoría de seguridad o crear usuarios con privilegios. | Confidencialidad y Trazabilidad | 4 | 4 | **16 (Crítico)** | **A.9.4.1** Restricción del acceso a la información | **AC-3** (Access Enforcement) | **IAM-05** User Authorization | Aplicación de decorador RBAC `@role_required('admin')` en Flask. Cualquier intento denegado registra evento `UNAUTHORIZED_ACCESS_ATTEMPT` en bitácora de auditoría. | 1 | 2 | **2 (Bajo)** |
| **R-06** | **Exposición y filtración de datos personales de huéspedes (PII):** Conexión no autorizada desde internet hacia el almacenamiento de datos del hostal. | Privacidad de Huéspedes (Ley 19.628) | 4 | 5 | **20 (Crítico)** | **A.13.1.1** Controles de redes y segregación | **SC-7** (Boundary Protection) | **IVS-06** Network Security & Boundary | Base de datos SQLite local sin socket de red TCP expuesto, permisos de sistema `chmod 600` exclusivos para `appuser` y bloqueo explícito de puertos en NSG y UFW. | 1 | 3 | **3 (Bajo)** |
| **R-07** | **Ataques web por cabeceras inseguras (Clickjacking / MIME Confusion):** Inserción del sistema de reservas en iframes maliciosos o interpretación indebida de MIME. | Integridad de la Interfaz Web | 3 | 3 | **9 (Medio)** | **A.14.2.5** Principios de ingeniería de sistemas seguros | **SI-10** (Information Input Validation) | **AAC-03** Application Security | Inyección mandatoria de cabeceras HTTP de endurecimiento en Nginx y Flask: `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection` y `CSP`. | 1 | 1 | **1 (Bajo)** |

---

## 2.3 Resumen de Efectividad de la Mitigación y Alineamiento con Gobierno TI
* **Efectividad Global:** El 100% de los riesgos catalogados como **Críticos (20/25)** y **Altos (15/25)** fueron mitigados exitosamente, logrando un riesgo residual máximo de **4/25 (Bajo / Aceptable)**.
* **Alineamiento con Estrategias de Gobierno TI:** La implementación garantiza el cumplimiento de los tres pilares de la seguridad de la información:
  1. **Confidencialidad:** Protección de datos personales de clientes del hostal mediante aislamiento local y RBAC estricto.
  2. **Integridad:** Trazabilidad inmutable mediante bitácora de auditoría y firmas hash SHA-256 en respaldos.
  3. **Disponibilidad:** Supervisión continua con auto-recuperación de Systemd y política de copias de seguridad probadas.
