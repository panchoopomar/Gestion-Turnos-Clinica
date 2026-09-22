import unittest
import sqlite3
import hashlib

# =============================================================
# FUNCIONES A PROBAR (EXTRAÍDAS DE LA LÓGICA DEL SISTEMA)
# =============================================================

def hashear_password(password_plana):
    """Convierte una contraseña plana en hash SHA-256."""
    return hashlib.sha256(password_plana.encode()).hexdigest()

def generar_bloques_horarios(horario_str):
    """Divide rangos horarios en bloques discretos de 30 minutos."""
    bloques = []
    texto = horario_str.lower().strip()
    rangos = texto.replace('y', ',').split(',')

    for rango in rangos:
        if 'a' in rango:
            partes = rango.split('a')
            if len(partes) == 2:
                try:
                    inicio_str = partes[0].strip()
                    fin_str = partes[1].strip()

                    h_in, m_in = map(int, inicio_str.split(':'))
                    h_fin, m_fin = map(int, fin_str.split(':'))

                    min_inicio = h_in * 60 + m_in
                    min_fin = h_fin * 60 + m_fin

                    actual = min_inicio
                    while actual + 30 <= min_fin:
                        h1, m1 = divmod(actual, 60)
                        h2, m2 = divmod(actual + 30, 60)
                        slot = f"{h1:02d}:{m1:02d} - {h2:02d}:{m2:02d}"
                        bloques.append(slot)
                        actual += 30
                except Exception:
                    pass
    if not bloques:
        bloques = [horario_str]
    return bloques


class TestClinicaBackend(unittest.TestCase):

    def setUp(self):
        """Configura una base de datos SQLite en memoria antes de cada prueba."""
        self.conexion = sqlite3.connect(":memory:")
        self.cursor = self.conexion.cursor()

        # Creación de tablas equivalentes al sistema real
        self.cursor.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL, 
                password TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE medicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                dias_atencion TEXT NOT NULL,
                horarios TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente TEXT NOT NULL,
                medico TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                dia TEXT NOT NULL,
                horario TEXT NOT NULL
            )
        ''')
        self.conexion.commit()

    def tearDown(self):
        """Cierra la conexión de base de datos después de cada prueba."""
        self.conexion.close()

    # -------------------------------------------------------------
    # 1. PRUEBAS DE SEGURIDAD Y HASHEO
    # -------------------------------------------------------------
    def test_hashear_password_consistencia(self):
        """Verifica que el mismo texto genere exactamente el mismo hash."""
        pass_plana = "admin123"
        hash_esperado = hashlib.sha256(pass_plana.encode()).hexdigest()
        self.assertEqual(hashear_password(pass_plana), hash_esperado)

    def test_hashear_password_unicidad(self):
        """Verifica que dos claves distintas generen hashes totalmente diferentes."""
        self.assertNotEqual(hashear_password("claveA"), hashear_password("claveB"))

    # -------------------------------------------------------------
    # 2. PRUEBAS DEL ALGORITMO DE BLOQUES DE 30 MINUTOS
    # -------------------------------------------------------------
    def test_generar_bloques_horarios_simple(self):
        """Verifica la fragmentación de un rango corrido."""
        horario_input = "08:00 a 10:00"
        bloques = generar_bloques_horarios(horario_input)
        esperado = [
            "08:00 - 08:30",
            "08:30 - 09:00",
            "09:00 - 09:30",
            "09:30 - 10:00"
        ]
        self.assertEqual(bloques, esperado)

    def test_generar_bloques_horarios_doble_turno(self):
        """Verifica la fragmentación con rangos divididos (mañana y tarde)."""
        horario_input = "08:00 a 09:00 y 16:00 a 17:00"
        bloques = generar_bloques_horarios(horario_input)
        esperado = [
            "08:00 - 08:30",
            "08:30 - 09:00",
            "16:00 - 16:30",
            "16:30 - 17:00"
        ]
        self.assertEqual(bloques, esperado)

    # -------------------------------------------------------------
    # 3. PRUEBAS DE USUARIOS Y AUTENTICACIÓN
    # -------------------------------------------------------------
    def test_registro_usuario_exitoso(self):
        """Valida que un usuario paciente pueda guardarse en la BD."""
        pass_hash = hashear_password("paciente123")
        self.cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                            ("paciente@test.com", pass_hash, "paciente"))
        self.conexion.commit()

        self.cursor.execute("SELECT username, rol FROM usuarios WHERE username = ?", ("paciente@test.com",))
        usuario = self.cursor.fetchone()
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario[0], "paciente@test.com")
        self.assertEqual(usuario[1], "paciente")

    def test_registro_usuario_duplicado_falla(self):
        """Valida la restricción UNIQUE del campo email/username."""
        pass_hash = hashear_password("pass123")
        self.cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                            ("duplicado@test.com", pass_hash, "paciente"))
        self.conexion.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                                ("duplicado@test.com", pass_hash, "paciente"))

    # -------------------------------------------------------------
    # 4. PRUEBAS DE DISPONIBILIDAD Y TURNOS
    # -------------------------------------------------------------
    def test_reserva_turno_exitosa(self):
        """Prueba la inserción exitosa de un turno de 30 minutos."""
        self.cursor.execute(
            "INSERT INTO turnos (paciente, medico, especialidad, dia, horario) VALUES (?, ?, ?, ?, ?)",
            ("paciente1@test.com", "Dr. Perez", "Pediatría", "Lunes", "08:00 - 08:30")
        )
        self.conexion.commit()

        self.cursor.execute("SELECT COUNT(*) FROM turnos WHERE medico = ? AND dia = ? AND horario = ?",
                            ("Dr. Perez", "Lunes", "08:00 - 08:30"))
        self.assertEqual(self.cursor.fetchone()[0], 1)

    def test_deteccion_horario_ocupado(self):
        """Valida la detección de horarios previamente ocupados."""
        self.cursor.execute(
            "INSERT INTO turnos (paciente, medico, especialidad, dia, horario) VALUES (?, ?, ?, ?, ?)",
            ("paciente1@test.com", "Dr. Perez", "Pediatría", "Lunes", "08:00 - 08:30")
        )
        self.conexion.commit()

        # Consulta de verificación de conflicto
        self.cursor.execute("SELECT COUNT(*) FROM turnos WHERE medico = ? AND dia = ? AND horario = ?",
                            ("Dr. Perez", "Lunes", "08:00 - 08:30"))
        esta_ocupado = self.cursor.fetchone()[0] > 0
        self.assertTrue(esta_ocupado)

    def test_cancelacion_turno_exitoso(self):
        """Valida que un turno reservado sea eliminado correctamente al cancelarse."""
        self.cursor.execute(
            "INSERT INTO turnos (paciente, medico, especialidad, dia, horario) VALUES (?, ?, ?, ?, ?)",
            ("paciente1@test.com", "Dr. Perez", "Pediatría", "Lunes", "08:00 - 08:30")
        )
        self.conexion.commit()
        turno_id = self.cursor.lastrowid

        # Cancelar el turno
        self.cursor.execute("DELETE FROM turnos WHERE id = ? AND paciente = ?", (turno_id, "paciente1@test.com"))
        self.conexion.commit()

        # Verificar que la base de datos ya no posee el turno
        self.cursor.execute("SELECT COUNT(*) FROM turnos WHERE id = ?", (turno_id,))
        self.assertEqual(self.cursor.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()