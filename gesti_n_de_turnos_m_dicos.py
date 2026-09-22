import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import hashlib

# ==========================================
# TURNOS MÉDICOS - LOGIN Y REGISTRO
# ==========================================

class ClinicaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Turnos Médicos")
        self.root.geometry("400x350")
        self.root.config(padx=20, pady=20)
        self.usuario_actual = None
        
        self.inicializar_base_datos()
        self.crear_pantalla_login()

    def hashear_password(self, password_plana):
        """Convierte una contraseña en texto plano a un hash SHA-256 por seguridad."""
        return hashlib.sha256(password_plana.encode()).hexdigest()

    def inicializar_base_datos(self):
        """Crea la BD y pre-carga 5 administradores si está vacía."""
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL, 
                password TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                dias_atencion TEXT NOT NULL,
                horarios TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente TEXT NOT NULL,
                medico TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                dia TEXT NOT NULL,
                horario TEXT NOT NULL
            )
        ''')

        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='administrador'")
        if cursor.fetchone()[0] == 0:
            admins_por_defecto = [
                ("admin1@clinica.com", "admin123"),
                ("admin2@clinica.com", "admin123"),
                ("admin3@clinica.com", "admin123"),
                ("admin4@clinica.com", "admin123"),
                ("admin5@clinica.com", "admin123")
            ]
            
            for admin_user, admin_pass in admins_por_defecto:
                pass_hash = self.hashear_password(admin_pass)
                cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                               (admin_user, pass_hash, 'administrador'))
            conexion.commit()

        conexion.close()

    def generar_bloques_horarios(self, horario_str):
        """
        Parsea textos de rango de horarios (ej: '8:00 a 12:30 y 15:00 a 19:30')
        y los divide en intervalos exactos de 30 minutos.
        """
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

    # !!!!!!!!!!!!!!!! PANTALLA DE LOGIN !!!!!!!!!!!!!!!!!
    def crear_pantalla_login(self):
        self.limpiar_ventana()
        self.root.geometry("400x350")
        self.poner_imagen_fondo_login()
        
        btn_estilo_titulo = {
            "bg": "#003B76",
            "fg": "white",
            "font": ("Times New Roman", 16, "roman"),
            "relief": "flat",
            "padx": 15,
            "pady": 15
        }

        tk.Label(self.root, text="Bienvenido a la Clínica", **btn_estilo_titulo).pack(pady=10)

        tk.Label(self.root, text="Email / Usuario:").pack()
        self.entry_usuario = tk.Entry(self.root)
        self.entry_usuario.pack(pady=5)

        tk.Label(self.root, text="Contraseña:").pack()
        self.entry_password = tk.Entry(self.root, show="*")
        self.entry_password.pack(pady=5)

        tk.Button(self.root, text="Ingresar", command=self.validar_login, width=20).pack(pady=10)
        tk.Button(self.root, text="Registrarse como paciente", command=self.crear_pantalla_registro, width=25).pack(pady=5)

    def validar_login(self):
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        if not usuario or not password:
            messagebox.showwarning("Error", "Por favor, complete todos los campos.")
            return
        
        pass_hash = self.hashear_password(password)

        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT rol FROM usuarios WHERE username = ? AND password = ?", (usuario, pass_hash))
        resultado = cursor.fetchone()
        conexion.close()

        if resultado:
            rol = resultado[0]
            if rol == "administrador":
                messagebox.showinfo("Éxito", f"Bienvenido Administrador: {usuario}")
                self.crear_pantalla_admin()  
            else:
                messagebox.showinfo("Éxito", f"Bienvenido Paciente: {usuario}")
                self.usuario_actual = usuario
                self.crear_pantalla_paciente()
        else:
            messagebox.showerror("Error", "Email/Usuario o contraseña incorrectos.")

    # !!!!!!!!!!! PANTALLA DE REGISTRO DE PACIENTE !!!!!!!!!!!!
    def crear_pantalla_registro(self):
        self.limpiar_ventana()
        self.root.geometry("400x380")
        self.poner_imagen_fondo_login()
        
        btn_estilo_titulo = {
            "bg": "#003B76",
            "fg": "white",
            "font": ("Times New Roman", 16, "roman"),
            "relief": "flat",
            "padx": 15,
            "pady": 15
        }

        tk.Label(self.root, text="Registro de Nuevo Paciente", **btn_estilo_titulo).pack(pady=10)

        tk.Label(self.root, text="Email:").pack()
        self.entry_reg_email = tk.Entry(self.root)
        self.entry_reg_email.pack(pady=5)

        tk.Label(self.root, text="Contraseña:").pack()
        self.entry_reg_pass = tk.Entry(self.root, show="*")
        self.entry_reg_pass.pack(pady=5)

        tk.Label(self.root, text="Repetir Contraseña:").pack()
        self.entry_reg_pass_conf = tk.Entry(self.root, show="*")
        self.entry_reg_pass_conf.pack(pady=5)

        tk.Button(self.root, text="Crear Cuenta", command=self.registrar_paciente, width=20).pack(pady=10)
        tk.Button(self.root, text="Volver al Login", command=self.crear_pantalla_login, width=20).pack()

    def registrar_paciente(self):
        email = self.entry_reg_email.get().strip()
        password = self.entry_reg_pass.get().strip()
        pass_conf = self.entry_reg_pass_conf.get().strip()

        if not email or not password or not pass_conf:
            messagebox.showwarning("Error", "Todos los campos son obligatorios.")
            return
        
        if password != pass_conf:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        pass_hash = self.hashear_password(password)

        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        
        try:
            cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                           (email, pass_hash, 'paciente'))
            conexion.commit()
            messagebox.showinfo("Éxito", "Paciente registrado correctamente. Ya puede iniciar sesión.")
            self.crear_pantalla_login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ese email ya se encuentra registrado.")
        finally:
            conexion.close()

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # !!!!!!!!!!! PANTALLA DE ADMINISTRADOR !!!!!!!!!!
    def crear_pantalla_admin(self):
        self.limpiar_ventana()
        self.root.geometry("950x700")
        self.poner_imagen_fondo_pac_y_admin()

        tk.Label(self.root, text="Panel de Administrador - Gestión de Médicos", font=("Arial", 14, "bold")).pack(pady=10)

        frame_form = tk.Frame(self.root)
        frame_form.pack(pady=10)

        tk.Label(frame_form, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_med_nombre = tk.Entry(frame_form)
        self.entry_med_nombre.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_form, text="Especialidad:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_med_especialidad = tk.Entry(frame_form)
        self.entry_med_especialidad.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(frame_form, text="Días:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_med_dias = tk.Entry(frame_form)
        self.entry_med_dias.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame_form, text="Horarios (ej: 8:00 a 12:30 y 15:00 a 19:30):").grid(row=1, column=2, padx=5, pady=5)
        self.entry_med_horarios = tk.Entry(frame_form)
        self.entry_med_horarios.grid(row=1, column=3, padx=5, pady=5)

        frame_botones = tk.Frame(self.root)
        frame_botones.pack(pady=10)
        
        tk.Button(frame_botones, text="Agregar", command=self.agregar_medico, width=15).grid(row=0, column=0, padx=10)
        tk.Button(frame_botones, text="Modificar", command=self.modificar_medico, width=15).grid(row=0, column=1, padx=10)
        tk.Button(frame_botones, text="Eliminar", command=self.eliminar_medico, width=15).grid(row=0, column=2, padx=10)
        tk.Button(frame_botones, text="Cerrar Sesión", command=self.crear_pantalla_login, width=15).grid(row=0, column=3, padx=10)
        
        frame_reinicio = tk.LabelFrame(self.root, text="Gestión y Reinicio de Turnos", padx=10, pady=10)
        frame_reinicio.pack(pady=10, fill="x", padx=20)

        tk.Label(frame_reinicio, text="Médico (o dejar en blanco para TODOS):").pack(anchor="w")
        self.entry_admin_medico = tk.Entry(frame_reinicio, width=30)
        self.entry_admin_medico.pack(anchor="w", pady=2)

        tk.Label(frame_reinicio, text="Día de la semana a reiniciar (ej: Miércoles / Lunes):").pack(anchor="w")
        self.entry_admin_dia = tk.Entry(frame_reinicio, width=20)
        self.entry_admin_dia.pack(anchor="w", pady=2)
        
        tk.Button(frame_reinicio, text="Reiniciar Turnos Filtrados", command=self.admin_reiniciar_turnos_especifico, bg="#fff3cd", width=30).pack(pady=8)

        self.tabla_medicos = ttk.Treeview(self.root, columns=("ID", "Nombre", "Especialidad", "Días", "Horarios"), show="headings")
        self.tabla_medicos.heading("ID", text="ID")
        self.tabla_medicos.heading("Nombre", text="Nombre")
        self.tabla_medicos.heading("Especialidad", text="Especialidad")
        self.tabla_medicos.heading("Días", text="Días")
        self.tabla_medicos.heading("Horarios", text="Horarios")
        
        self.tabla_medicos.column("ID", width=30)
        self.tabla_medicos.column("Nombre", width=150)
        self.tabla_medicos.column("Especialidad", width=150)
        self.tabla_medicos.column("Días", width=120)
        self.tabla_medicos.column("Horarios", width=200)
        
        self.tabla_medicos.pack(pady=10, fill="x", padx=20)
        self.tabla_medicos.bind("<ButtonRelease-1>", self.seleccionar_medico)
        
        self.cargar_medicos()
        
    def cargar_medicos(self):
        for fila in self.tabla_medicos.get_children():
            self.tabla_medicos.delete(fila)
        
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM medicos")
        filas = cursor.fetchall()
        conexion.close()

        for fila in filas:
            self.tabla_medicos.insert("", tk.END, values=fila)
            
    def limpiar_campos_medico(self):
        self.entry_med_nombre.delete(0, tk.END)
        self.entry_med_especialidad.delete(0, tk.END)
        self.entry_med_dias.delete(0, tk.END)
        self.entry_med_horarios.delete(0, tk.END)

    def agregar_medico(self):
        nombre = self.entry_med_nombre.get().strip()
        especialidad = self.entry_med_especialidad.get().strip()
        dias = self.entry_med_dias.get().strip()
        horarios = self.entry_med_horarios.get().strip()

        if not nombre or not especialidad or not dias or not horarios:
            messagebox.showwarning("Error", "Todos los campos son obligatorios.")
            return

        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO medicos (nombre, especialidad, dias_atencion, horarios) VALUES (?, ?, ?, ?)",
                       (nombre, especialidad, dias, horarios))
        conexion.commit()
        conexion.close()

        messagebox.showinfo("Éxito", "Médico agregado correctamente.")
        self.limpiar_campos_medico()
        self.cargar_medicos()

    def seleccionar_medico(self, event):
        item_seleccionado = self.tabla_medicos.focus()
        if not item_seleccionado:
            return
        
        valores = self.tabla_medicos.item(item_seleccionado, "values")
        self.limpiar_campos_medico()
        self.entry_med_nombre.insert(0, valores[1])
        self.entry_med_especialidad.insert(0, valores[2])
        self.entry_med_dias.insert(0, valores[3])
        self.entry_med_horarios.insert(0, valores[4])

    def modificar_medico(self):
        item_seleccionado = self.tabla_medicos.focus()
        if not item_seleccionado:
            messagebox.showwarning("Error", "Seleccione un médico de la tabla para modificar.")
            return

        id_medico = self.tabla_medicos.item(item_seleccionado, "values")[0]
        nombre = self.entry_med_nombre.get().strip()
        especialidad = self.entry_med_especialidad.get().strip()
        dias = self.entry_med_dias.get().strip()
        horarios = self.entry_med_horarios.get().strip()

        if not nombre or not especialidad or not dias or not horarios:
            messagebox.showwarning("Error", "Todos los campos son obligatorios.")
            return

        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute('''
            UPDATE medicos 
            SET nombre=?, especialidad=?, dias_atencion=?, horarios=? 
            WHERE id=?
        ''', (nombre, especialidad, dias, horarios, id_medico))
        conexion.commit()
        conexion.close()

        messagebox.showinfo("Éxito", "Datos actualizados correctamente.")
        self.limpiar_campos_medico()
        self.cargar_medicos()

    def eliminar_medico(self):
        item_seleccionado = self.tabla_medicos.focus()
        if not item_seleccionado:
            messagebox.showwarning("Error", "Seleccione un médico de la tabla para eliminar.")
            return

        valores = self.tabla_medicos.item(item_seleccionado, "values")
        id_medico = valores[0]
        nombre_medico = valores[1]

        respuesta = messagebox.askyesno("Confirmar", f"¿Está seguro que desea eliminar al Dr./Dra. {nombre_medico}?")
        if respuesta:
            conexion = sqlite3.connect("clinica.db")
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM medicos WHERE id = ?", (id_medico,))
            conexion.commit()
            conexion.close()
            
            self.limpiar_campos_medico()
            self.cargar_medicos()
            messagebox.showinfo("Éxito", "Médico eliminado.")

    def admin_reiniciar_turnos_especifico(self):
        medico_filtro = self.entry_admin_medico.get().strip()
        dia_filtro = self.entry_admin_dia.get().strip()

        if not dia_filtro:
            messagebox.showwarning("Atención", "Por lo menos debés indicar el día de la semana a reiniciar (ej: Lunes).")
            return

        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()

        if medico_filtro:
            confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar los turnos del Dr./Dra. {medico_filtro} para el día {dia_filtro}?")
            if confirmacion:
                cursor.execute("DELETE FROM turnos WHERE medico LIKE ? AND dia = ?", ('%' + medico_filtro + '%', dia_filtro))
                conexion.commit()
                messagebox.showinfo("Éxito", f"Se reiniciaron los turnos de {medico_filtro} para el día {dia_filtro}.")
        else:
            confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar los turnos de TODOS los médicos para el día {dia_filtro}?")
            if confirmacion:
                cursor.execute("DELETE FROM turnos WHERE dia = ?", (dia_filtro,))
                conexion.commit()
                messagebox.showinfo("Éxito", f"Se reiniciaron los turnos de todos los médicos para el día {dia_filtro}.")

        conexion.close()
        self.entry_admin_medico.delete(0, tk.END)
        self.entry_admin_dia.delete(0, tk.END)

    # !!!!!!!!!!!!!!!!!!! PANTALLA DE PACIENTE - BÚSQUEDA, SELECCIÓN DE TURNO Y CANCELACIÓN !!!!!!!!!!!!!!!!!!

    def crear_pantalla_paciente(self):
        self.limpiar_ventana()
        self.root.geometry("950x730")
        self.poner_imagen_fondo_pac_y_admin()

        tk.Label(self.root, text="Panel de Paciente - Solicitar o Cancelar Turnos", font=("Arial", 16, "bold")).pack(pady=10)

        # Filtro por especialidad
        frame_filtro = tk.Frame(self.root)
        frame_filtro.pack(pady=5)

        tk.Label(frame_filtro, text="Filtrar por Especialidad:").pack(side=tk.LEFT, padx=5)
        self.entry_filtro_esp = tk.Entry(frame_filtro, width=20)
        self.entry_filtro_esp.pack(side=tk.LEFT, padx=5)

        tk.Button(frame_filtro, text="Buscar", command=self.buscar_medicos_especialidad, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_filtro, text="Ver Todos", command=self.cargar_medicos_paciente, width=12).pack(side=tk.LEFT, padx=5)

        # Tabla de médicos
        tk.Label(self.root, text="Médicos Disponibles:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=5)
        
        self.tabla_medicos_paciente = ttk.Treeview(self.root, columns=("ID", "Nombre", "Especialidad", "Días", "Horarios"), show="headings", height=5)
        self.tabla_medicos_paciente.heading("ID", text="ID")
        self.tabla_medicos_paciente.heading("Nombre", text="Nombre")
        self.tabla_medicos_paciente.heading("Especialidad", text="Especialidad")
        self.tabla_medicos_paciente.heading("Días", text="Días")
        self.tabla_medicos_paciente.heading("Horarios", text="Horarios de Atención")
        
        self.tabla_medicos_paciente.column("ID", width=30)
        self.tabla_medicos_paciente.column("Nombre", width=160)
        self.tabla_medicos_paciente.column("Especialidad", width=160)
        self.tabla_medicos_paciente.column("Días", width=120)
        self.tabla_medicos_paciente.column("Horarios", width=200)
        self.tabla_medicos_paciente.pack(pady=5, fill="x", padx=20)

        # Selectores de Día y Horario de 30 min
        frame_seleccion = tk.Frame(self.root)
        frame_seleccion.pack(pady=10)

        tk.Label(frame_seleccion, text="Día:").pack(side=tk.LEFT, padx=5)
        self.combo_dia_turno = ttk.Combobox(frame_seleccion, width=15, state="readonly")
        self.combo_dia_turno.pack(side=tk.LEFT, padx=5)

        tk.Label(frame_seleccion, text="Horario Disponible (30 min):").pack(side=tk.LEFT, padx=5)
        self.combo_horario_turno = ttk.Combobox(frame_seleccion, width=20, state="readonly")
        self.combo_horario_turno.pack(side=tk.LEFT, padx=5)

        # Eventos para actualizar opciones
        self.tabla_medicos_paciente.bind("<<TreeviewSelect>>", self.actualizar_dias_medico)
        self.combo_dia_turno.bind("<<ComboboxSelected>>", self.actualizar_horarios_disponibles)

        # Botón para solicitar turno
        tk.Button(self.root, text="Reservar Turno En El Horario Seleccionado", command=self.solicitar_turno, bg="#d1e7dd", width=40, font=("Arial", 10, "bold")).pack(pady=5)

        # Sección para ver y cancelar turnos solicitados
        tk.Label(self.root, text="Mis Turnos Reservados:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=5)
        
        self.tabla_mis_turnos = ttk.Treeview(self.root, columns=("ID", "Médico", "Especialidad", "Día", "Horario"), show="headings", height=4)
        self.tabla_mis_turnos.heading("ID", text="ID")
        self.tabla_mis_turnos.heading("Médico", text="Médico")
        self.tabla_mis_turnos.heading("Especialidad", text="Especialidad")
        self.tabla_mis_turnos.heading("Día", text="Día")
        self.tabla_mis_turnos.heading("Horario", text="Horario")
        
        self.tabla_mis_turnos.column("ID", width=30)
        self.tabla_mis_turnos.column("Médico", width=180)
        self.tabla_mis_turnos.column("Especialidad", width=160)
        self.tabla_mis_turnos.column("Día", width=120)
        self.tabla_mis_turnos.column("Horario", width=150)
        self.tabla_mis_turnos.pack(pady=5, fill="x", padx=20)

        # Botones de gestión de mis turnos y salir
        frame_acciones_pac = tk.Frame(self.root)
        frame_acciones_pac.pack(pady=10)

        tk.Button(frame_acciones_pac, text="Cancelar Turno Seleccionado", command=self.cancelar_turno, bg="#f8d7da", fg="#842029", width=28, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_acciones_pac, text="Cerrar Sesión", command=self.crear_pantalla_login, width=20).pack(side=tk.LEFT, padx=10)
        
        self.cargar_medicos_paciente()
        self.cargar_mis_turnos()

    def cargar_medicos_paciente(self):
        for fila in self.tabla_medicos_paciente.get_children():
            self.tabla_medicos_paciente.delete(fila)
        
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM medicos")
        filas = cursor.fetchall()
        conexion.close()

        for fila in filas:
            self.tabla_medicos_paciente.insert("", tk.END, values=fila)

    def buscar_medicos_especialidad(self):
        especialidad_buscada = self.entry_filtro_esp.get().strip()
        
        if not especialidad_buscada:
            messagebox.showwarning("Atención", "Ingrese una especialidad para buscar.")
            return

        for fila in self.tabla_medicos_paciente.get_children():
            self.tabla_medicos_paciente.delete(fila)

        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM medicos WHERE especialidad LIKE ?", ('%' + especialidad_buscada + '%',))
        filas = cursor.fetchall()
        conexion.close()

        if not filas:
            messagebox.showinfo("Sin resultados", "No se encontraron médicos con esa especialidad.")
            self.cargar_medicos_paciente()
        else:
            for fila in filas:
                self.tabla_medicos_paciente.insert("", tk.END, values=fila)

    def actualizar_dias_medico(self, event):
        item_seleccionado = self.tabla_medicos_paciente.focus()
        if not item_seleccionado:
            return

        valores = self.tabla_medicos_paciente.item(item_seleccionado, "values")
        dias_texto = valores[3] 

        lista_dias = [dia.strip() for dia in dias_texto.replace(" y ", ",").split(",") if dia.strip()]

        self.combo_dia_turno['values'] = lista_dias
        
        if lista_dias:
            self.combo_dia_turno.set(lista_dias[0])
            self.actualizar_horarios_disponibles()
        else:
            self.combo_dia_turno.set("")
            self.combo_horario_turno['values'] = []
            self.combo_horario_turno.set("")

    def actualizar_horarios_disponibles(self, event=None):
        item_seleccionado = self.tabla_medicos_paciente.focus()
        dia_elegido = self.combo_dia_turno.get()

        if not item_seleccionado or not dia_elegido:
            self.combo_horario_turno['values'] = []
            self.combo_horario_turno.set("")
            return

        valores = self.tabla_medicos_paciente.item(item_seleccionado, "values")
        nombre_medico = valores[1]
        horarios_string = valores[4]

        # 1. Generar todos los bloques de 30 min posibles según el rango del médico
        todos_los_bloques = self.generar_bloques_horarios(horarios_string)

        # 2. Consultar turnos ya reservados para ese médico en ese día
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT horario FROM turnos WHERE medico = ? AND dia = ?", (nombre_medico, dia_elegido))
        turnos_reservados = [fila[0] for fila in cursor.fetchall()]
        conexion.close()

        # 3. Filtrar los bloques ocupados
        bloques_disponibles = [b for b in todos_los_bloques if b not in turnos_reservados]

        self.combo_horario_turno['values'] = bloques_disponibles
        if bloques_disponibles:
            self.combo_horario_turno.set(bloques_disponibles[0])
        else:
            self.combo_horario_turno.set("Sin horarios dispon.")

    def solicitar_turno(self):
        item_seleccionado = self.tabla_medicos_paciente.focus()
        if not item_seleccionado:
            messagebox.showwarning("Error", "Por favor, seleccione un médico de la tabla.")
            return

        dia_elegido = self.combo_dia_turno.get()
        horario_elegido = self.combo_horario_turno.get()

        if not dia_elegido:
            messagebox.showwarning("Error", "Seleccione un día de atención.")
            return

        if not horario_elegido or horario_elegido == "Sin horarios dispon.":
            messagebox.showwarning("Error", "No hay horarios disponibles para el día seleccionado.")
            return

        valores = self.tabla_medicos_paciente.item(item_seleccionado, "values")
        nombre_medico = valores[1]
        especialidad = valores[2]

        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()

        # Verificar si el horario ya fue ocupado en ese instante
        cursor.execute("SELECT COUNT(*) FROM turnos WHERE medico = ? AND dia = ? AND horario = ?", 
                       (nombre_medico, dia_elegido, horario_elegido))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror("Error", "El horario seleccionado acaba de ser reservado por otro usuario. Por favor elija otro.")
            conexion.close()
            self.actualizar_horarios_disponibles()
            return

        cursor.execute("INSERT INTO turnos (paciente, medico, especialidad, dia, horario) VALUES (?, ?, ?, ?, ?)",
                       (self.usuario_actual, nombre_medico, especialidad, dia_elegido, horario_elegido))
        conexion.commit()
        conexion.close()

        messagebox.showinfo("Éxito", f"¡Turno reservado con éxito!\n\nMédico: Dr./Dra. {nombre_medico}\nEspecialidad: {especialidad}\nDía: {dia_elegido}\nHorario: {horario_elegido}")
        self.cargar_mis_turnos()
        self.actualizar_horarios_disponibles()

    def cancelar_turno(self):
        item_seleccionado = self.tabla_mis_turnos.focus()
        if not item_seleccionado:
            messagebox.showwarning("Atención", "Por favor, seleccione un turno de la lista 'Mis Turnos Reservados' para cancelar.")
            return

        valores = self.tabla_mis_turnos.item(item_seleccionado, "values")
        id_turno = valores[0]
        medico = valores[1]
        dia = valores[3]
        horario = valores[4]

        confirmacion = messagebox.askyesno("Confirmar Cancelación", 
                                           f"¿Está seguro de que desea cancelar su turno?\n\nMédico: {medico}\nDía: {dia}\nHorario: {horario}")
        if confirmacion:
            conexion = sqlite3.connect("clinica.db")
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM turnos WHERE id = ? AND paciente = ?", (id_turno, self.usuario_actual))
            conexion.commit()
            conexion.close()

            messagebox.showinfo("Éxito", "El turno fue cancelado correctamente.")
            self.cargar_mis_turnos()
            self.actualizar_horarios_disponibles()

    def cargar_mis_turnos(self):
        for fila in self.tabla_mis_turnos.get_children():
            self.tabla_mis_turnos.delete(fila)

        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT id, medico, especialidad, dia, horario FROM turnos WHERE paciente = ?", (self.usuario_actual,))
        filas = cursor.fetchall()
        conexion.close()

        for fila in filas:
            self.tabla_mis_turnos.insert("", tk.END, values=fila)

    # !!!!!!!!!!! MANEJO DE IMÁGENES DE FONDO !!!!!!!!!!!
    def poner_imagen_fondo_login(self):
        try:
            self.imagen_fondo = tk.PhotoImage(file="fondo_azul.png")
            self.label_fondo = tk.Label(self.root, image=self.imagen_fondo)
            self.label_fondo.place(x=0, y=0, relwidth=1, relheight=1)
            self.label_fondo.lower()
        except Exception:
            pass

    def poner_imagen_fondo_pac_y_admin(self):
        try:
            self.imagen_fondo = tk.PhotoImage(file="fondo-paciente-admin.png")
            self.label_fondo = tk.Label(self.root, image=self.imagen_fondo)
            self.label_fondo.place(x=0, y=0, relwidth=1, relheight=1)
            self.label_fondo.lower()
        except Exception:
            pass

# !!!!!!!!!!!! Ejecución del programa !!!!!!!!!!
if __name__ == "__main__":
    ventana_principal = tk.Tk()
    app = ClinicaApp(ventana_principal)
    ventana_principal.mainloop()