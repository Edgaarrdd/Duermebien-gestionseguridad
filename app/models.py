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
            role TEXT NOT NULL CHECK(role IN ('admin', 'encargado')),
            full_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabla de Habitaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'DISPONIBLE' CHECK(status IN ('DISPONIBLE', 'OCUPADA', 'MANTENIMIENTO', 'LIMPIEZA')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabla de Huéspedes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabla de Reservas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            guest_id INTEGER NOT NULL,
            check_in_date DATE NOT NULL,
            check_out_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK(status IN ('PENDIENTE', 'CONFIRMADA', 'CANCELADA', 'COMPLETADA')),
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (guest_id) REFERENCES guests(id)
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
                "Administrador General"
            ),
            (
                "encargado",
                generate_password_hash("EncargadoSecurity2024!"),
                "encargado",
                "Encargado de Recepción"
            )
        ]
        cursor.executemany(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            default_users
        )

        # Sembrado inicial de habitaciones
        sample_rooms = [
            ("101", "Sencilla", 50000.0, "DISPONIBLE"),
            ("102", "Doble", 80000.0, "DISPONIBLE"),
            ("201", "Suite", 150000.0, "DISPONIBLE"),
            ("202", "Doble", 80000.0, "LIMPIEZA")
        ]
        cursor.executemany(
            "INSERT INTO rooms (number, type, price_per_night, status) VALUES (?, ?, ?, ?)",
            sample_rooms
        )

        # Sembrado inicial de huéspedes
        sample_guests = [
            ("Juan Pérez", "juan.perez@email.com", "+56912345678"),
            ("María Gómez", "maria.gomez@email.com", "+56987654321")
        ]
        cursor.executemany(
            "INSERT INTO guests (full_name, email, phone) VALUES (?, ?, ?)",
            sample_guests
        )

        # Registro inicial de auditoría
        cursor.execute(
            "INSERT INTO audit_logs (username, role, action, ip_address, status, details) VALUES (?, ?, ?, ?, ?, ?)",
            ("system", "SYSTEM", "INIT_DB", "127.0.0.1", "SUCCESS", "Base de datos Hostify inicializada con usuarios y políticas RBAC")
        )

    conn.commit()
    conn.close()
