import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def get_db_connection(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Tabla de Usuarios (RBAC)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'operador')),
            full_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabla de Incidentes de Seguridad
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL CHECK(severity IN ('CRITICO', 'ALTO', 'MEDIO', 'BAJO')),
            status TEXT NOT NULL DEFAULT 'ABIERTO' CHECK(status IN ('ABIERTO', 'EN_ANALISIS', 'RESUELTO', 'CERRADO')),
            reported_by TEXT NOT NULL,
            assigned_to TEXT DEFAULT 'Sin asignar',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabla de Logs de Auditoría (Trazabilidad e ISO 27001 A.12.4)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            username TEXT NOT NULL,
            role TEXT,
            action TEXT NOT NULL,
            ip_address TEXT,
            status TEXT NOT NULL,
            details TEXT
        );
    """)

    # Sembrado inicial de usuarios si no existen
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            (
                "admin",
                generate_password_hash("AdminSecurity2024!"),
                "admin",
                "Oficial de Seguridad (CISO)"
            ),
            (
                "operador",
                generate_password_hash("OperatorSecurity2024!"),
                "operador",
                "Analista de Ciberseguridad SOC"
            )
        ]
        cursor.executemany(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            default_users
        )

        # Sembrado inicial de incidentes de prueba para evaluación
        sample_incidents = [
            (
                "Intento de fuerza bruta detectado en puerto SSH",
                "Se registraron múltiples intentos de autenticación fallida desde IP 198.51.100.45. Fail2ban bloqueó la IP automáticamente.",
                "ALTO",
                "RESUELTO",
                "operador",
                "admin"
            ),
            (
                "Alerta de consumo inusual de CPU en servidor",
                "Posible proceso anómalo consumiendo 85% de CPU durante la ventana nocturna.",
                "MEDIO",
                "EN_ANALISIS",
                "operador",
                "admin"
            ),
            (
                "Detección de escaneo de puertos en perímetro",
                "Sondeo SYN hacia puertos no expuestos bloqueado por Network Security Group de Azure.",
                "BAJO",
                "CERRADO",
                "admin",
                "operador"
            )
        ]
        cursor.executemany(
            "INSERT INTO incidents (title, description, severity, status, reported_by, assigned_to) VALUES (?, ?, ?, ?, ?, ?)",
            sample_incidents
        )

        # Registro inicial de auditoría
        cursor.execute(
            "INSERT INTO audit_logs (username, role, action, ip_address, status, details) VALUES (?, ?, ?, ?, ?, ?)",
            ("system", "SYSTEM", "INIT_DB", "127.0.0.1", "SUCCESS", "Base de datos inicializada con usuarios y políticas RBAC")
        )

    conn.commit()
    conn.close()
