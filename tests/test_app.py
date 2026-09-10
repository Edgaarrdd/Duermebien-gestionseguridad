import unittest
import tempfile
import os
from app import create_app
from app.models import get_db_connection

class SecurityPortalTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.app = create_app({
            "TESTING": True,
            "DATABASE_PATH": self.db_path,
            "SECRET_KEY": "test-key-for-security-evaluation"
        })
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def login(self, username, password):
        return self.client.post("/login", data={
            "username": username,
            "password": password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data["status"], "UP")
        self.assertIn("ISO 27001", json_data["compliance"])

    def test_security_headers(self):
        response = self.client.get("/health")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(response.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertIn("Content-Security-Policy", response.headers)

    def test_login_success_admin(self):
        response = self.login("admin", "AdminSecurity2024!")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Bienvenido", response.data)
        self.assertIn(b"admin", response.data.lower())

    def test_login_failed_invalid_credentials(self):
        response = self.login("admin", "WrongPassword123!")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Credenciales", response.data)

    def test_rbac_encargado_restricted_from_admin_areas(self):
        # Iniciar sesión como encargado
        self.login("encargado", "EncargadoSecurity2024!")

        # Intento de entrar a logs de auditoría (solo admin)
        resp_audit = self.client.get("/admin/audit-logs", follow_redirects=True)
        self.assertEqual(resp_audit.status_code, 200)
        self.assertIn(b"Acceso denegado", resp_audit.data)

        # Intento de entrar a gestión de usuarios (solo admin)
        resp_users = self.client.get("/admin/users", follow_redirects=True)
        self.assertEqual(resp_users.status_code, 200)
        self.assertIn(b"Acceso denegado", resp_users.data)

        # Verificar que el intento no autorizado quedó registrado en la tabla de auditoría
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs WHERE action = 'UNAUTHORIZED_ACCESS_ATTEMPT'")
        logs = cursor.fetchall()
        conn.close()
        self.assertGreaterEqual(len(logs), 1)

    def test_rbac_admin_allowed_in_admin_areas(self):
        # Iniciar sesión como admin
        self.login("admin", "AdminSecurity2024!")

        # Debe poder acceder a logs de auditoría
        resp_audit = self.client.get("/admin/audit-logs")
        self.assertEqual(resp_audit.status_code, 200)
        self.assertIn(b"centralizada de auditor", resp_audit.data.lower())

        # Debe poder acceder a gestión de usuarios
        resp_users = self.client.get("/admin/users")
        self.assertEqual(resp_users.status_code, 200)
        self.assertIn(b"directorio de cuentas", resp_users.data.lower())

    def test_guest_creation_and_audit(self):
        self.login("encargado", "EncargadoSecurity2024!")
        post_data = {
            "full_name": "Usuario Prueba Test",
            "email": "test@prueba.com",
            "phone": "+56999999999"
        }
        response = self.client.post("/guests", data=post_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Usuario Prueba Test", response.data)

        # Verificar registro en base de datos
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guests WHERE full_name = ?", ("Usuario Prueba Test",))
        guest = cursor.fetchone()
        self.assertIsNotNone(guest)
        self.assertEqual(guest["email"], "test@prueba.com")
        conn.close()

if __name__ == "__main__":
    unittest.main()
