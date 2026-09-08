# 2. Matriz de Gestión de Riesgos (ISO/IEC 27001, NIST SP 800-30 y CSA CCM)

## 2.1 Criterios de Evaluación
La evaluación de riesgos se realiza siguiendo la metodología de **ISO/IEC 27005** y la guía **NIST SP 800-30**:
* **Probabilidad (P):** 1 (Muy Baja), 2 (Baja), 3 (Media), 4 (Alta), 5 (Muy Alta).
* **Impacto (I):** 1 (Insignificante), 2 (Menor), 3 (Moderado), 4 (Grave), 5 (Catastrófico).
* **Nivel de Riesgo (NR = P × I):**
  * **1 - 6:** Bajo (Aceptable)
  * **8 - 12:** Medio (Monitoreo y controles recomendados)
  * **15 - 25:** Alto / Crítico (Mitigación prioritaria obligatoria)

---

## 2.2 Matriz de Riesgos y Controles de Mitigación

| ID | Amenaza / Escenario de Riesgo | Activo Afectado | P | I | NR (Inicial) | Control ISO/IEC 27001 (Anexo A) | Control NIST SP 800-53 / CSF | Control CSA CCM | Medida Técnica Implementada en el Proyecto | P_res | I_res | NR (Residual) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **R-01** | **Compromiso de cuenta raíz / propietario cloud:** Uso de credenciales maestras de suscripción en operaciones diarias. | Cuenta Azure / Suscripción | 3 | 5 | **15 (Alto)** | **A.9.2.3** Gestión de derechos de acceso privilegiado | **AC-2, AC-6** (Principle of Least Privilege) | **IAM-01** Identity & Access Mgt | Creación de roles RBAC en Azure Entra ID; restricción de cuenta Owner/Global Admin para uso exclusivo de contingencias. | 1 | 4 | **4 (Bajo)** |
| **R-02** | **Ataque de fuerza bruta contra SSH:** Intentos masivos automatizados de autenticación hacia el puerto 22. | Sistema Operativo (Ubuntu) | 4 | 4 | **16 (Crítico)** | **A.9.4.2** Procedimientos de inicio de sesión seguro | **AC-7** (Unsuccessful Logon Attempts) | **IAM-09** Authentication | Deshabilitación total de passwords (`disablePasswordAuthentication: true`), solo claves RSA, y jaula Fail2ban (bloqueo por 24h tras 3 intentos). | 1 | 3 | **3 (Bajo)** |
| **R-03** | **Caída del servicio por fallo no controlado o degradación:** Error en aplicación o sobrecarga que cause indisponibilidad. | Disponibilidad del Portal Web | 4 | 4 | **16 (Crítico)** | **A.12.1.3** Gestión de capacidad y disponibilidad | **CP-2, CP-10** (Contingency Plan / Recovery) | **BCR-02** Business Continuity | Auto-reinicio automático con `systemd` (`Restart=always`, reinicio en <5s) y Rate Limiting en Nginx (10 req/s). | 1 | 2 | **2 (Bajo)** |
| **R-04** | **Pérdida o corrupción de datos de la base de datos:** Fallo en disco, ataque de ransomware o eliminación accidental. | Base de Datos (SQLite) | 3 | 5 | **15 (Alto)** | **A.12.3.1** Copias de seguridad de la información | **CP-9** (Information System Backup) | **DSP-05** Data Resiliency / Backup | Script automatizado diario en crontab (`0 2 * * *`) con empaquetado, rotación a 7 días y verificación de integridad mediante SHA-256. | 1 | 2 | **2 (Bajo)** |
| **R-05** | **Elevación de privilegios o acceso no autorizado a datos confidenciales:** Usuario con rol de operador intenta acceder a auditoría o modificar usuarios. | Confidencialidad y Trazabilidad | 4 | 4 | **16 (Crítico)** | **A.9.4.1** Restricción del acceso a la información | **AC-3** (Access Enforcement) | **IAM-05** User Authorization | Implementación de decoradores RBAC en Flask (`@role_required('admin')`) que interceptan peticiones y registran alerta en log de auditoría. | 1 | 2 | **2 (Bajo)** |
| **R-06** | **Exposición externa no autorizada de la base de datos:** Conexión directa desde internet a puertos de bases de datos (3306/5432). | Confidencialidad de la Información | 4 | 5 | **20 (Crítico)** | **A.13.1.1** Controles de redes | **SC-7** (Boundary Protection) | **IVS-06** Network Security | Base de datos encapsulada en bucle local sin socket externo y reglas UFW que deniegan explícitamente puertos de bases de datos. | 1 | 3 | **3 (Bajo)** |
| **R-07** | **Ataques web por cabeceras inseguras (Clickjacking / MIME Sniffing):** Inserción del sitio en iframes o interpretación errónea de contenidos. | Integridad de la Aplicación | 3 | 3 | **9 (Medio)** | **A.14.2.5** Principios de ingeniería de sistemas seguros | **SI-10** (Information Input Validation) | **AAC-03** Application Security | Configuración de cabeceras HTTP estrictas en Nginx y Flask: `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `CSP`. | 1 | 1 | **1 (Bajo)** |

---

## 2.3 Resumen de Efectividad de la Mitigación
Tras la implementación de los controles de la norma **ISO/IEC 27001**, las directrices del **NIST** y la matriz de la **Cloud Security Alliance (CSA)**, **el 100% de los riesgos críticos y altos fueron reducidos a niveles de riesgo residual Aceptable (Bajo)**, garantizando la confidencialidad, integridad y disponibilidad del entorno de producción.
