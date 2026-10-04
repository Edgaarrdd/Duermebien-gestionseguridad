import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secure-key-cloud-security-evaluation-3-iso27001")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "data", "portal_security.db"))
    
    # Configuraciones de seguridad para cookies y sesiones (OWASP / ISO 27001 A.9)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Permitir sesiones sobre HTTP (puerto 80) sin SSL
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutos de inactividad
