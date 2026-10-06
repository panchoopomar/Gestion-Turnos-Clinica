import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import hashlib

# ==========================================
# TURNOS MÉDICOS - LOGIN Y REGISTRO
# ==========================================
class ClinicaApp:
    """
    Clase principal que contiene toda la lógica de la aplicación de la Clínica.
    Maneja la interfaz gráfica, la conexión a la base de datos y la navegación entre pantallas.
    """
    def __init__(self, root):
        # Inicializamos la ventana principal
        self.root = root
        # Establecemos el título de la ventana
        self.root.title("Sistema de Gestión de Turnos Médicos")
        # Configuramos el tamaño inicial de la ventana
        self.root.geometry("400x350")
        # Añadimos márgenes internos (padding) a la ventana principal
        self.root.config(padx=20, pady=20)
        # Variable para almacenar el usuario que haya iniciado sesión (None por defecto)
        self.usuario_actual = None
        
        # Llamamos a la función que crea la base de datos y sus tablas si no existen
        self.inicializar_base_datos()
        # Llamamos a la función que dibuja la pantalla de inicio de sesión
        self.crear_pantalla_login()

    def hashear_password(self, password_plana):
        """
        Convierte una contraseña en texto plano a un hash SHA-256 por seguridad.
        Esto evita guardar contraseñas legibles en la base de datos.
        Retorna la cadena hexadecimal del hash.
        """
        return hashlib.sha256(password_plana.encode()).hexdigest()

    def inicializar_base_datos(self):
        """
        Crea la BD 'clinica.db' y sus tablas ('usuarios', 'medicos', 'turnos') si están vacías.
        Además, pre-carga 5 usuarios administradores por defecto la primera vez que se ejecuta.
        """
        # Conectamos (o creamos) el archivo de la base de datos SQLite
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        
        # Creamos la tabla 'usuarios' para gestionar logins y roles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL, 
                password TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        ''')
        
        # Creamos la tabla 'medicos' para el panel de administración
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                dias_atencion TEXT NOT NULL,
                horarios TEXT NOT NULL
            )
        ''')
        
        # Creamos la tabla 'turnos' para asociar pacientes con médicos en un día/hora específico
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
        
        # Verificamos si ya existen usuarios administradores en la base de datos
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='administrador'")
        # Si el conteo es 0, insertamos los administradores por defecto
        if cursor.fetchone()[0] == 0:
            admins_por_defecto = [
                ("admin1@clinica.com", "admin123"),
                ("admin2@clinica.com", "admin123"),
                ("admin3@clinica.com", "admin123"),
                ("admin4@clinica.com", "admin123"),
                ("admin5@clinica.com", "admin123")
            ]
            
            # Recorremos la lista y guardamos cada administrador hasheando su clave
            for admin_user, admin_pass in admins_por_defecto:
                pass_hash = self.hashear_password(admin_pass)
                cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                               (admin_user, pass_hash, 'administrador'))
            # Guardamos los cambios en la base de datos
            conexion.commit()
            
        # Cerramos la conexión para liberar recursos
        conexion.close()

    def generar_bloques_horarios(self, horario_str):
        """
        Parsea textos de rango de horarios (ej: '8:00 a 12:30 y 15:00 a 19:30')
        y los divide en intervalos exactos de 30 minutos.
        Retorna una lista de cadenas con los turnos generados.
        """
        bloques = []
        # Convertimos todo a minúsculas y quitamos espacios en los extremos
        texto = horario_str.lower().strip()
        # Reemplazamos la 'y' por coma para separar múltiples rangos (ej: mañana, tarde)
        rangos = texto.replace('y', ',').split(',')
        
        # Procesamos cada rango encontrado
        for rango in rangos:
            if 'a' in rango:
                # Separamos hora de inicio y hora de fin usando la letra 'a'
                partes = rango.split('a')
                if len(partes) == 2:
                    try:
                        inicio_str = partes[0].strip()
                        fin_str = partes[1].strip()
                        
                        # Extraemos horas y minutos de inicio
                        h_in, m_in = map(int, inicio_str.split(':'))
                        # Extraemos horas y minutos de fin
                        h_fin, m_fin = map(int, fin_str.split(':'))
                        
                        # Convertimos ambas horas a minutos totales para facilitar el cálculo
                        min_inicio = h_in * 60 + m_in
                        min_fin = h_fin * 60 + m_fin
                        
                        actual = min_inicio
                        # Iteramos sumando 30 minutos hasta llegar a la hora de fin
                        while actual + 30 <= min_fin:
                            # Re-convertimos los minutos a formato hh:mm
                            h1, m1 = divmod(actual, 60)
                            h2, m2 = divmod(actual + 30, 60)
                            # Formateamos el bloque (ej: "08:00 - 08:30")
                            slot = f"{h1:02d}:{m1:02d} - {h2:02d}:{m2:02d}"
                            bloques.append(slot)
                            # Avanzamos el puntero 30 minutos
                            actual += 30
                    except Exception:
                        # Si hay un error en el formato ingresado por el usuario, lo ignoramos
                        pass
        # Si no se pudo generar ningún bloque, devolvemos el texto original en una lista
        if not bloques:
            bloques = [horario_str]
        return bloques

    # !!!!!!!!!!!!!!!! PANTALLA DE LOGIN !!!!!!!!!!!!!!!!!
    def crear_pantalla_login(self):
        """
        Construye los elementos de la interfaz para que los usuarios (pacientes o administradores)
        puedan iniciar sesión en el sistema.
        """
        # Limpiamos cualquier widget que haya quedado en pantalla
        self.limpiar_ventana()
        # Ajustamos el tamaño específico para el login
        self.root.geometry("400x350")
        # Colocamos el fondo personalizado
        self.poner_imagen_fondo_login()
        
        # Diccionario con estilos comunes para el título de la pantalla
        btn_estilo_titulo = {
            "bg": "#003B76",
            "fg": "white",
            "font": ("Times New Roman", 16, "roman"),
            "relief": "flat",
            "padx": 15,
            "pady": 15
        }
        
        # Título principal
        tk.Label(self.root, text="Bienvenido a la Clínica", **btn_estilo_titulo).pack(pady=10)
        
        # Etiqueta y campo de texto para el Usuario/Email
        tk.Label(self.root, text="Email / Usuario:").pack()
        self.entry_usuario = tk.Entry(self.root)
        self.entry_usuario.pack(pady=5)
        
        # Etiqueta y campo de texto para la Contraseña (con asteriscos)
        tk.Label(self.root, text="Contraseña:").pack()
        self.entry_password = tk.Entry(self.root, show="*")
        self.entry_password.pack(pady=5)
        
        # Botones para ingresar o ir a la pantalla de registro
        tk.Button(self.root, text="Ingresar", command=self.validar_login, width=20).pack(pady=10)
        tk.Button(self.root, text="Registrarse como paciente", command=self.crear_pantalla_registro, width=25).pack(pady=5)

    def validar_login(self):
        """
        Obtiene los datos ingresados en la pantalla de login, los verifica en la BD,
        y redirige al usuario al panel de Administrador o Paciente según corresponda.
        """
        # Obtenemos los valores y quitamos espacios al inicio/fin
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()
        
        # Validamos que no estén vacíos
        if not usuario or not password:
            messagebox.showwarning("Error", "Por favor, complete todos los campos.")
            return
        
        # Hasheamos la contraseña ingresada para compararla con la base de datos
        pass_hash = self.hashear_password(password)
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        
        # Buscamos al usuario que coincida exactamente con el username y password hasheada
        cursor.execute("SELECT rol FROM usuarios WHERE username = ? AND password = ?", (usuario, pass_hash))
        resultado = cursor.fetchone()
        conexion.close()
        
        # Si se encontró un registro, evaluamos el rol
        if resultado:
            rol = resultado[0]
            if rol == "administrador":
                messagebox.showinfo("Éxito", f"Bienvenido Administrador: {usuario}")
                self.crear_pantalla_admin()  # Carga la UI del administrador
            else:
                messagebox.showinfo("Éxito", f"Bienvenido Paciente: {usuario}")
                self.usuario_actual = usuario  # Guardamos quién es el paciente logueado
                self.crear_pantalla_paciente() # Carga la UI del paciente
        else:
            # Si no hay coincidencias, los datos son erróneos
            messagebox.showerror("Error", "Email/Usuario o contraseña incorrectos.")

    # !!!!!!!!!!! PANTALLA DE REGISTRO DE PACIENTE !!!!!!!!!!!!
    def crear_pantalla_registro(self):
        """
        Limpia la pantalla y muestra el formulario de registro para nuevos pacientes.
        """
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
        
        # Campo para ingresar Email
        tk.Label(self.root, text="Email:").pack()
        self.entry_reg_email = tk.Entry(self.root)
        self.entry_reg_email.pack(pady=5)
        
        # Campo para ingresar Contraseña
        tk.Label(self.root, text="Contraseña:").pack()
        self.entry_reg_pass = tk.Entry(self.root, show="*")
        self.entry_reg_pass.pack(pady=5)
        
        # Campo para confirmar Contraseña
        tk.Label(self.root, text="Repetir Contraseña:").pack()
        self.entry_reg_pass_conf = tk.Entry(self.root, show="*")
        self.entry_reg_pass_conf.pack(pady=5)
        
        # Botones de acción: registrar o volver atrás
        tk.Button(self.root, text="Crear Cuenta", command=self.registrar_paciente, width=20).pack(pady=10)
        tk.Button(self.root, text="Volver al Login", command=self.crear_pantalla_login, width=20).pack()

    def registrar_paciente(self):
        """
        Toma los datos de registro, valida que las contraseñas coincidan,
        y guarda al nuevo usuario (paciente) en la BD.
        """
        email = self.entry_reg_email.get().strip()
        password = self.entry_reg_pass.get().strip()
        pass_conf = self.entry_reg_pass_conf.get().strip()
        
        # Validación de campos vacíos
        if not email or not password or not pass_conf:
            messagebox.showwarning("Error", "Todos los campos son obligatorios.")
            return
        
        # Validación de coincidencia de contraseñas
        if password != pass_conf:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return
            
        # Generamos el hash antes de guardarlo
        pass_hash = self.hashear_password(password)
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        
        try:
            # Insertamos el paciente fijando su rol en 'paciente'
            cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                           (email, pass_hash, 'paciente'))
            conexion.commit()
            messagebox.showinfo("Éxito", "Paciente registrado correctamente. Ya puede iniciar sesión.")
            # Si el registro es exitoso, regresamos a la pantalla de login
            self.crear_pantalla_login()
        except sqlite3.IntegrityError:
            # Si el email ya existe en la BD saltará este error por la regla UNIQUE en la tabla
            messagebox.showerror("Error", "Ese email ya se encuentra registrado.")
        finally:
            # Siempre cerramos la conexión a la BD, con o sin error
            conexion.close()

    def limpiar_ventana(self):
        """
        Función de utilidad para destruir todos los widgets (etiquetas, botones, inputs)
        que estén actualmente en la ventana principal, permitiendo cargar una nueva vista limpia.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

    # !!!!!!!!!!! PANTALLA DE ADMINISTRADOR !!!!!!!!!!
    def crear_pantalla_admin(self):
        """
        Renderiza todo el panel de gestión para el administrador: 
        formulario de doctores, botones ABM (Alta, Baja, Modificación), 
        barra de búsqueda, gestión de turnos y tabla (Treeview) de doctores.
        """
        self.limpiar_ventana()
        self.root.geometry("950x700")
        self.poner_imagen_fondo_pac_y_admin()
        
        # Título del panel de administrador
        tk.Label(self.root, text="Panel de Administrador - Gestión de Médicos", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Frame contenedor para el formulario de ingreso de un nuevo médico
        frame_form = tk.Frame(self.root)
        frame_form.pack(pady=10)
        
        # Entradas de texto para Nombre y Especialidad
        tk.Label(frame_form, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_med_nombre = tk.Entry(frame_form)
        self.entry_med_nombre.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame_form, text="Especialidad:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_med_especialidad = tk.Entry(frame_form)
        self.entry_med_especialidad.grid(row=0, column=3, padx=5, pady=5)
        
        # Inicializamos el diccionario que guardará la asignación temporal de horarios
        self.horarios_temporales = {} 
        
        # Botón que abre una ventana secundaria para asignar horarios a este médico
        tk.Label(frame_form, text="Disponibilidad:").grid(row=1, column=0, padx=5, pady=5)
        tk.Button(frame_form, text="Asignar horario a médico", command=self.abrir_ventana_horarios, bg="#cfe2ff").grid(row=1, column=1, columnspan=3, pady=5, sticky="we")
        
        # Frame para botones de acción (Agregar, Modificar, Eliminar, Salir)
        frame_botones = tk.Frame(self.root)
        frame_botones.pack(pady=10)
        
        tk.Button(frame_botones, text="Agregar", command=self.agregar_medico, width=15).grid(row=0, column=0, padx=10)
        tk.Button(frame_botones, text="Modificar", command=self.modificar_medico, width=15).grid(row=0, column=1, padx=10)
        tk.Button(frame_botones, text="Eliminar", command=self.eliminar_medico, width=15).grid(row=0, column=2, padx=10)
        tk.Button(frame_botones, text="Cerrar Sesión", command=self.crear_pantalla_login, width=15).grid(row=0, column=3, padx=10)
        
        # Sección especial para forzar el reinicio/borrado de turnos masivo
        frame_reinicio = tk.LabelFrame(self.root, text="Gestión y Reinicio de Turnos", padx=10, pady=10)
        frame_reinicio.pack(pady=10, fill="x", padx=20)
        
        tk.Label(frame_reinicio, text="Médico (o dejar en blanco para TODOS):").pack(anchor="w")
        self.entry_admin_medico = tk.Entry(frame_reinicio, width=30)
        self.entry_admin_medico.pack(anchor="w", pady=2)
        
        tk.Label(frame_reinicio, text="Día de la semana a reiniciar (ej: Miércoles / Lunes):").pack(anchor="w")
        self.entry_admin_dia = tk.Entry(frame_reinicio, width=20)
        self.entry_admin_dia.pack(anchor="w", pady=2)
        
        tk.Button(frame_reinicio, text="Reiniciar Turnos Filtrados", command=self.admin_reiniciar_turnos_especifico, bg="#fff3cd", width=30).pack(pady=8)
        
        # --- NUEVA BARRA DE BÚSQUEDA POR ESPECIALIDAD ---
        # Frame destinado a filtrar la lista de doctores en el Treeview
        frame_busqueda_admin = tk.Frame(self.root)
        frame_busqueda_admin.pack(pady=5, padx=20, anchor="w")
        
        tk.Label(frame_busqueda_admin, text="Buscar por Especialidad:").pack(side=tk.LEFT, padx=5)
        self.entry_buscar_admin_esp = tk.Entry(frame_busqueda_admin, width=25)
        self.entry_buscar_admin_esp.pack(side=tk.LEFT, padx=5)
        
        # Filtrado dinámico automático al tipear usando evento de teclado
        self.entry_buscar_admin_esp.bind("<KeyRelease>", self.filtrar_medicos_admin)
        
        tk.Button(frame_busqueda_admin, text="Mostrar Todos", command=self.mostrar_todos_medicos_admin).pack(side=tk.LEFT, padx=5)
        # ------------------------------------------------
        
        # Se define dos veces la tabla por error o redundancia en el código original
        self.tabla_medicos = ttk.Treeview(self.root, columns=("ID", "Nombre", "Especialidad", "Días", "Horarios"), show="headings") #[cite: 5]
        self.tabla_medicos = ttk.Treeview(self.root, columns=("ID", "Nombre", "Especialidad", "Días", "Horarios"), show="headings")
        
        # Títulos de las columnas de la tabla
        self.tabla_medicos.heading("ID", text="ID")
        self.tabla_medicos.heading("Nombre", text="Nombre")
        self.tabla_medicos.heading("Especialidad", text="Especialidad")
        self.tabla_medicos.heading("Días", text="Días")
        self.tabla_medicos.heading("Horarios", text="Horarios")
        
        # Anchos de las columnas en píxeles
        self.tabla_medicos.column("ID", width=30)
        self.tabla_medicos.column("Nombre", width=150)
        self.tabla_medicos.column("Especialidad", width=150)
        self.tabla_medicos.column("Días", width=120)
        self.tabla_medicos.column("Horarios", width=200)
        
        self.tabla_medicos.pack(pady=10, fill="x", padx=20)
        # Evento que dispara seleccionar_medico() cuando el admin hace click sobre una fila
        self.tabla_medicos.bind("<ButtonRelease-1>", self.seleccionar_medico)
        
        # Finalmente, cargamos todos los médicos existentes desde la BD
        self.cargar_medicos()
        
    def abrir_ventana_horarios(self):
        """
        Abre una ventana emergente (Toplevel) para configurar qué días y horarios atiende
        el médico que se está registrando o modificando.
        """
        ventana = tk.Toplevel(self.root)
        ventana.title("Asignar Horario a Médico")
        ventana.geometry("400x350")
        ventana.transient(self.root)
        ventana.grab_set()  # Bloquea la interacción con la ventana principal hasta que esta se cierre
        
        tk.Label(ventana, text="Seleccione los días y asigne su horario:", font=("Arial", 11, "bold")).pack(pady=10)
        
        frame_dias = tk.Frame(ventana)
        frame_dias.pack(pady=5, padx=20, fill="both", expand=True)
        
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        # Diccionarios para rastrear los Checkbuttons (var booleana) y Entrys (textos de horarios)
        self.variables_dias = {}
        self.entradas_horarios = {}
        
        # Verificamos si existe la variable temporal, de lo contrario la inicializamos
        if not hasattr(self, 'horarios_temporales'):
            self.horarios_temporales = {}
            
        # Generamos dinámicamente un Checkbutton y un Entry para cada día de la semana
        for i, dia in enumerate(dias_semana):
            # var_chk tomará el valor True si el día ya estaba seleccionado antes
            var_chk = tk.BooleanVar(value=(dia in self.horarios_temporales))
            chk = tk.Checkbutton(frame_dias, text=dia, variable=var_chk)
            chk.grid(row=i, column=0, sticky="w", pady=2)
            
            ent = tk.Entry(frame_dias, width=30)
            # Si ya había horario asignado para ese día, lo restauramos
            if dia in self.horarios_temporales:
                ent.insert(0, self.horarios_temporales[dia])
            else:
                # Si no, mostramos un horario de ejemplo por defecto
                ent.insert(0, "8:00 a 12:00 y 16:00 a 20:30")
            ent.grid(row=i, column=1, padx=10, pady=2)
            
            self.variables_dias[dia] = var_chk
            self.entradas_horarios[dia] = ent
            
        def guardar_horarios():
            """
            Función interna que recolecta los días tildados y sus respectivos textos de horarios,
            los guarda en memoria temporal y cierra la ventana emergente.
            """
            self.horarios_temporales = {}
            for d in dias_semana:
                # Si el checkbox de ese día está marcado (True)
                if self.variables_dias[d].get(): 
                    horario = self.entradas_horarios[d].get().strip()
                    if horario:
                        self.horarios_temporales[d] = horario
            
            # Validación para evitar guardar sin seleccionar al menos un día
            if not self.horarios_temporales:
                messagebox.showwarning("Atención", "No ha seleccionado ningún día.", parent=ventana)
                return
                
            messagebox.showinfo("Éxito", "Horarios asignados. Presione Agregar/Modificar para guardar.", parent=ventana)
            ventana.destroy()
            
        tk.Button(ventana, text="Guardar Horarios", command=guardar_horarios, bg="#d1e7dd").pack(pady=10)
        
    def cargar_medicos(self):
        """
        Consulta la tabla 'medicos' en la BD, vacía el Treeview (tabla visual),
        e inserta todos los médicos nuevamente para mantener la vista actualizada.
        """
        # Limpiar filas existentes en la tabla visual
        for fila in self.tabla_medicos.get_children():
            self.tabla_medicos.delete(fila)
        
        # Traer todos los médicos
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM medicos")
        filas = cursor.fetchall()
        conexion.close()
        
        # Poblamos la tabla visual con las filas traidas de SQLite
        for fila in filas:
            self.tabla_medicos.insert("", tk.END, values=fila)
            
    def limpiar_campos_medico(self):
        """
        Limpia los campos Entry (nombre y especialidad) del formulario administrador
        y reinicia los horarios temporales para prepararlo para un nuevo ingreso.
        """
        self.entry_med_nombre.delete(0, tk.END)
        self.entry_med_especialidad.delete(0, tk.END)
        self.horarios_temporales = {} # Resetea la memoria temporal

    def agregar_medico(self):
        """
        Toma los datos del formulario (y los horarios en memoria temporal)
        e inserta un nuevo médico en la base de datos tras verificar si es válido.
        """
        nombre = self.entry_med_nombre.get().strip() # Obtenemos el nombre ingresado
        especialidad = self.entry_med_especialidad.get().strip() # Obtenemos la especialidad
        
        # Validamos que no haya datos vacíos
        if not nombre or not especialidad: #
            messagebox.showwarning("Error", "El nombre y especialidad son obligatorios.") #[cite: 5]
            return #[cite: 5]
            
        # Validamos que se haya ejecutado el sub-menú de asignación de horarios
        if not hasattr(self, 'horarios_temporales') or not self.horarios_temporales: #[cite: 5]
            messagebox.showwarning("Error", "Debe asignar días y horarios haciendo clic en 'Asignar horario a médico'.") #[cite: 5]
            return #[cite: 5]

        # --- NUEVA VALIDACIÓN: Búsqueda de duplicados ignorando mayúsculas ---
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        # Buscamos si existe ya un registro con ese mismo nombre y especialidad
        cursor.execute("""
            SELECT id FROM medicos 
            WHERE LOWER(nombre) = LOWER(?) AND LOWER(especialidad) = LOWER(?)
        """, (nombre, especialidad))
        
        # Si encuentra un resultado, abortamos la inserción para evitar médicos repetidos
        if cursor.fetchone():
            conexion.close()
            messagebox.showerror("Error", f"El médico '{nombre}' con especialidad '{especialidad}' ya se encuentra registrado.")
            return
        # ---------------------------------------------------------------------
            
        # Armamos el listado de días separándolos por coma (ej: "Lunes, Martes")
        dias = ", ".join(self.horarios_temporales.keys()) #[cite: 5]
        
        # Formateamos el diccionario de horarios a un string (ej: "Lunes=8:00 a 12:00|Martes=...")
        lista_str = [] #[cite: 5]
        for d, h in self.horarios_temporales.items(): #[cite: 5]
            lista_str.append(f"{d}={h}") #[cite: 5]
        horarios_texto = "|".join(lista_str) #[cite: 5]
        
        # La inserción procede normalmente si no hay duplicados
        cursor.execute("INSERT INTO medicos (nombre, especialidad, dias_atencion, horarios) VALUES (?, ?, ?, ?)",
                       (nombre, especialidad, dias, horarios_texto)) #[cite: 5]
        conexion.commit() #[cite: 5]
        conexion.close() #[cite: 5]
        
        messagebox.showinfo("Éxito", "Médico agregado correctamente.") #[cite: 5]
        self.limpiar_campos_medico() #[cite: 5]
        self.cargar_medicos() #[cite: 5]

    def seleccionar_medico(self, event):
        """
        Evento que se activa cuando el administrador hace clic en una fila del Treeview.
        Carga los datos de ese médico en el formulario para poder modificarlo o eliminarlo.
        """
        item_seleccionado = self.tabla_medicos.focus()
        if not item_seleccionado:
            return
        
        valores = self.tabla_medicos.item(item_seleccionado, "values")
        self.limpiar_campos_medico()
        # Insertamos Nombre y Especialidad
        self.entry_med_nombre.insert(0, valores[1])
        self.entry_med_especialidad.insert(0, valores[2])
        
        # --- NUEVO: Leemos el Texto de SQLite y lo volvemos a separar ---
        # Parseamos el string de horarios de vuelta a un diccionario (self.horarios_temporales)
        self.horarios_temporales = {}
        horarios_guardados = valores[4]
        if horarios_guardados:
            # Si el texto tiene el formato nuevo con "|" (pipe)
            if "|" in horarios_guardados or "=" in horarios_guardados:
                pares = horarios_guardados.split("|")
                for par in pares:
                    if "=" in par:
                        dia, hor = par.split("=")
                        self.horarios_temporales[dia] = hor
            else:
                # Para evitar errores si tenías médicos viejos guardados sin formato
                pass 

    def modificar_medico(self):
        """
        Toma los datos actuales en el formulario del panel Admin y realiza un UPDATE 
        sobre el registro en la BD del médico previamente seleccionado en la tabla.
        """
        item_seleccionado = self.tabla_medicos.focus()
        if not item_seleccionado:
            messagebox.showwarning("Error", "Seleccione un médico de la tabla para modificar.")
            return
        
        # Extraemos el ID original de la fila clickeada
        id_medico = self.tabla_medicos.item(item_seleccionado, "values")[0]
        nombre = self.entry_med_nombre.get().strip()
        especialidad = self.entry_med_especialidad.get().strip()
        
        # Validamos obligatoriedad de campos
        if not nombre or not especialidad or not self.horarios_temporales:
            messagebox.showwarning("Error", "Complete nombre, especialidad y asigne horarios.")
            return
            
        # Re-armamos la cadena de días
        dias = ", ".join(self.horarios_temporales.keys())
        
        # --- NUEVO: Convertimos a Texto Plano ---
        # Re-armamos la estructura "Día=Rango Horario|Día2=Rango2"
        lista_str = []
        for d, h in self.horarios_temporales.items():
            lista_str.append(f"{d}={h}")
        horarios_texto = "|".join(lista_str)
        
        # Actualizamos la fila correspondiente mediante su ID
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute('''
            UPDATE medicos 
            SET nombre=?, especialidad=?, dias_atencion=?, horarios=? 
            WHERE id=?
        ''', (nombre, especialidad, dias, horarios_texto, id_medico))
        conexion.commit()
        conexion.close()
        
        messagebox.showinfo("Éxito", "Datos actualizados correctamente.")
        self.limpiar_campos_medico()
        self.cargar_medicos()

    def eliminar_medico(self):
        """
        Elimina por completo el registro de un médico seleccionado en la base de datos
        y refresca la tabla visual.
        """
        item_seleccionado = self.tabla_medicos.focus()
        if not item_seleccionado:
            messagebox.showwarning("Error", "Seleccione un médico de la tabla para eliminar.")
            return
            
        valores = self.tabla_medicos.item(item_seleccionado, "values")
        id_medico = valores[0]
        nombre_medico = valores[1]
        
        # Pedimos confirmación antes de la eliminación definitiva
        respuesta = messagebox.askyesno("Confirmar", f"¿Está seguro que desea eliminar al Dr./Dra. {nombre_medico}?")
        if respuesta:
            conexion = sqlite3.connect("clinica.db")
            cursor = conexion.cursor()
            # Ejecutamos instrucción DELETE
            cursor.execute("DELETE FROM medicos WHERE id = ?", (id_medico,))
            conexion.commit()
            conexion.close()
            
            self.limpiar_campos_medico()
            self.cargar_medicos()
            messagebox.showinfo("Éxito", "Médico eliminado.")

    def admin_reiniciar_turnos_especifico(self):
        """
        Permite al administrador cancelar (borrar) todos los turnos reservados.
        Puede ser filtrado por el nombre de un médico específico y/o un día de la semana.
        """
        medico_filtro = self.entry_admin_medico.get().strip()
        dia_filtro = self.entry_admin_dia.get().strip()
        
        # Requerimos el día como mínimo
        if not dia_filtro:
            messagebox.showwarning("Atención", "Por lo menos debés indicar el día de la semana a reiniciar (ej: Lunes).")
            return
            
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        
        # Si se ingresó un nombre de médico específico
        if medico_filtro:
            confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar los turnos del Dr./Dra. {medico_filtro} para el día {dia_filtro}?")
            if confirmacion:
                # Borramos los turnos asociados al LIKE del médico y que coincidan con el día
                cursor.execute("DELETE FROM turnos WHERE medico LIKE ? AND dia = ?", ('%' + medico_filtro + '%', dia_filtro))
                conexion.commit()
                messagebox.showinfo("Éxito", f"Se reiniciaron los turnos de {medico_filtro} para el día {dia_filtro}.")
        else:
            # Si el campo médico estaba vacío, borramos los turnos de TODOS los médicos en ese día
            confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar los turnos de TODOS los médicos para el día {dia_filtro}?")
            if confirmacion:
                cursor.execute("DELETE FROM turnos WHERE dia = ?", (dia_filtro,))
                conexion.commit()
                messagebox.showinfo("Éxito", f"Se reiniciaron los turnos de todos los médicos para el día {dia_filtro}.")
                
        conexion.close()
        # Limpiamos los campos de reseteo
        self.entry_admin_medico.delete(0, tk.END)
        self.entry_admin_dia.delete(0, tk.END)

    # !!!!!!!!!!!!!!!!!!! PANTALLA DE PACIENTE - BÚSQUEDA, SELECCIÓN DE TURNO Y CANCELACIÓN !!!!!!!!!!!!!!!!!!
    def crear_pantalla_paciente(self):
        """
        Construye la interfaz para los pacientes registrados, permitiendo buscar médicos, 
        seleccionar un turno libre, y visualizar/cancelar los turnos que ya tiene agendados.
        """
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
        
        # Tabla superior que muestra los médicos disponibles
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
        
        # Selectores de Día y Horario de 30 min (combobox)
        frame_seleccion = tk.Frame(self.root)
        frame_seleccion.pack(pady=10)
        tk.Label(frame_seleccion, text="Día:").pack(side=tk.LEFT, padx=5)
        self.combo_dia_turno = ttk.Combobox(frame_seleccion, width=15, state="readonly")
        self.combo_dia_turno.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_seleccion, text="Horario Disponible (30 min):").pack(side=tk.LEFT, padx=5)
        self.combo_horario_turno = ttk.Combobox(frame_seleccion, width=20, state="readonly")
        self.combo_horario_turno.pack(side=tk.LEFT, padx=5)
        
        # Eventos para reaccionar a las elecciones del usuario:
        # Cuando hace click en un médico, carga los días disponibles
        self.tabla_medicos_paciente.bind("<<TreeviewSelect>>", self.actualizar_dias_medico)
        # Cuando elige un día en el combo, calcula los horarios de 30 min vacíos
        self.combo_dia_turno.bind("<<ComboboxSelected>>", self.actualizar_horarios_disponibles)
        
        # Botón central para efectuar la reserva del turno seleccionado
        tk.Button(self.root, text="Reservar Turno En El Horario Seleccionado", command=self.solicitar_turno, bg="#d1e7dd", width=40, font=("Arial", 10, "bold")).pack(pady=5)
        
        # Tabla inferior donde el paciente ve los turnos que él mismo ha agendado
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
        
        # Invocamos la carga inicial de los datos a las tablas
        self.cargar_medicos_paciente()
        self.cargar_mis_turnos()

    def cargar_medicos_paciente(self):
        """
        Carga todos los médicos en la tabla superior del paciente sin aplicar filtros.
        Limpia primero la tabla para evitar duplicados.
        """
        for fila in self.tabla_medicos_paciente.get_children():
            self.tabla_medicos_paciente.delete(fila)
        
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM medicos")
        filas = cursor.fetchall()
        conexion.close()
        for fila in filas:
            self.tabla_medicos_paciente.insert("", tk.END, values=fila)
            
    def filtrar_medicos_admin(self, event=None):
        """
        Permite el filtrado dinámico (tipo live-search) de la tabla de médicos en el panel admin.
        Se activa cada vez que se suelta una tecla en la barra de búsqueda (KeyRelease).
        """
        texto_busqueda = self.entry_buscar_admin_esp.get().strip()
        
        # Vaciamos la tabla de médicos
        for fila in self.tabla_medicos.get_children(): #[cite: 5]
            self.tabla_medicos.delete(fila) #[cite: 5]
        
        conexion = sqlite3.connect("clinica.db") #[cite: 5]
        cursor = conexion.cursor() #[cite: 5]
        
        # Consultamos buscando coincidencias parciales (LIKE) por especialidad (ignorando mayúsculas)
        cursor.execute("SELECT * FROM medicos WHERE LOWER(especialidad) LIKE LOWER(?)", (f"%{texto_busqueda}%",))
        filas = cursor.fetchall() #[cite: 5]
        conexion.close() #[cite: 5]
        
        # Rellenamos la tabla con el nuevo filtro
        for fila in filas: #[cite: 5]
            self.tabla_medicos.insert("", tk.END, values=fila) #[cite: 5]

    def mostrar_todos_medicos_admin(self):
        """
        Limpia la barra de búsqueda en el panel admin y vuelve a renderizar todos los médicos.
        """
        # Limpiamos el entry y volvemos a cargar todo
        self.entry_buscar_admin_esp.delete(0, tk.END)
        self.cargar_medicos() #[cite: 5]

    def buscar_medicos_especialidad(self):
        """
        Ejecuta la búsqueda de médicos por especialidad en la interfaz de Paciente (botón Buscar).
        """
        especialidad_buscada = self.entry_filtro_esp.get().strip()
        
        if not especialidad_buscada:
            messagebox.showwarning("Atención", "Ingrese una especialidad para buscar.")
            return
            
        for fila in self.tabla_medicos_paciente.get_children():
            self.tabla_medicos_paciente.delete(fila)
            
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        # Busca coincidencias usando comodines (%)
        cursor.execute("SELECT * FROM medicos WHERE especialidad LIKE ?", ('%' + especialidad_buscada + '%',))
        filas = cursor.fetchall()
        conexion.close()
        
        if not filas:
            messagebox.showinfo("Sin resultados", "No se encontraron médicos con esa especialidad.")
            self.cargar_medicos_paciente() # Si no hay, se carga todo nuevamente
        else:
            for fila in filas:
                self.tabla_medicos_paciente.insert("", tk.END, values=fila)

    def actualizar_dias_medico(self, event):
        """
        Detecta la selección de un médico por el paciente. Toma la cadena de días de atención
        de ese médico y llena el Combobox (lista desplegable) de días.
        """
        item_seleccionado = self.tabla_medicos_paciente.focus()
        if not item_seleccionado:
            return
            
        valores = self.tabla_medicos_paciente.item(item_seleccionado, "values")
        # El campo 3 son los "Días"
        dias_texto = valores[3] 
        # Separa los días manejando tanto comas como "y" para parsearlos a lista
        lista_dias = [dia.strip() for dia in dias_texto.replace(" y ", ",").split(",") if dia.strip()]
        
        # Poblamos las opciones del combobox de días
        self.combo_dia_turno['values'] = lista_dias
        
        if lista_dias:
            self.combo_dia_turno.set(lista_dias[0]) # Seleccionamos por defecto el primero
            self.actualizar_horarios_disponibles()  # Calculamos sus horas
        else:
            self.combo_dia_turno.set("")
            self.combo_horario_turno['values'] = []
            self.combo_horario_turno.set("")

    def actualizar_horarios_disponibles(self, event=None):
        """
        Basado en el médico y el día seleccionados, calcula los bloques de 30 minutos,
        luego los contrasta con los turnos ya registrados en la base de datos y
        muestra solo los turnos que sigan estando vacíos en el Combobox de Horarios.
        """
        item_seleccionado = self.tabla_medicos_paciente.focus()
        dia_elegido = self.combo_dia_turno.get()
        
        if not item_seleccionado or not dia_elegido:
            self.combo_horario_turno['values'] = []
            self.combo_horario_turno.set("")
            return
            
        valores = self.tabla_medicos_paciente.item(item_seleccionado, "values")
        nombre_medico = valores[1]
        horarios_string = valores[4] # Ej: "Lunes=8:00 a 12:00|Martes=16:00 a 20:30"
        
        # --- NUEVO: Buscamos el horario para el día elegido leyendo el texto ---
        horario_del_dia = ""
        # Verificamos qué estructura tiene guardada
        if "|" in horarios_string or "=" in horarios_string:
            pares = horarios_string.split("|")
            for par in pares:
                if "=" in par:
                    dia_db, hor_db = par.split("=")
                    if dia_db == dia_elegido: # Compara día de BD con el elegido
                        horario_del_dia = hor_db
                        break
        else:
            # Soporte por si quedan médicos viejos guardados de la forma antigua sin formato diccionario
            horario_del_dia = horarios_string
            
        if not horario_del_dia:
            self.combo_horario_turno['values'] = []
            self.combo_horario_turno.set("Sin horarios dispon.")
            return
            
        # 1. Generamos los bloques de 30 min solo con el horario extraído para ese día
        todos_los_bloques = self.generar_bloques_horarios(horario_del_dia)
        
        # 2. Consultar SQLite para ver turnos ya reservados (ocupados) de ese médico en ese día
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT horario FROM turnos WHERE medico = ? AND dia = ?", (nombre_medico, dia_elegido))
        turnos_reservados = [fila[0] for fila in cursor.fetchall()]
        conexion.close()
        
        # 3. Filtrar los disponibles descartando los que existen en 'turnos_reservados'
        bloques_disponibles = [b for b in todos_los_bloques if b not in turnos_reservados]
        self.combo_horario_turno['values'] = bloques_disponibles
        
        if bloques_disponibles:
            self.combo_horario_turno.set(bloques_disponibles[0])
        else:
            self.combo_horario_turno.set("Sin horarios dispon.")

    def solicitar_turno(self):
        """
        Inserta el turno agendado en la BD a nombre del paciente logueado.
        Posee un paso de re-verificación para evitar sobre-escritura/concurrencia
        si otra persona agendó el mismo bloque exacto al mismo tiempo.
        """
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
        
        # Verificar si el horario ya fue ocupado en ese instante (concurrencia de usuarios)
        cursor.execute("SELECT COUNT(*) FROM turnos WHERE medico = ? AND dia = ? AND horario = ?", 
                       (nombre_medico, dia_elegido, horario_elegido))
        
        if cursor.fetchone()[0] > 0:
            # Si alguien nos ganó de mano con el turno, se avisa, se cierra y se recalcula.
            messagebox.showerror("Error", "El horario seleccionado acaba de ser reservado por otro usuario. Por favor elija otro.")
            conexion.close()
            self.actualizar_horarios_disponibles()
            return
            
        # Si el turno sigue libre, procedemos con el alta
        cursor.execute("INSERT INTO turnos (paciente, medico, especialidad, dia, horario) VALUES (?, ?, ?, ?, ?)",
                       (self.usuario_actual, nombre_medico, especialidad, dia_elegido, horario_elegido))
        conexion.commit()
        conexion.close()
        
        messagebox.showinfo("Éxito", f"¡Turno reservado con éxito!\n\nMédico: Dr./Dra. {nombre_medico}\nEspecialidad: {especialidad}\nDía: {dia_elegido}\nHorario: {horario_elegido}")
        # Recargamos la tabla personal para reflejar la novedad y recalculamos horas disponibles.
        self.cargar_mis_turnos()
        self.actualizar_horarios_disponibles()

    def cancelar_turno(self):
        """
        Permite al paciente cancelar uno de sus turnos. 
        Lo borra de la base de datos (BD 'turnos') liberando el espacio para otros pacientes.
        """
        item_seleccionado = self.tabla_mis_turnos.focus()
        if not item_seleccionado:
            messagebox.showwarning("Atención", "Por favor, seleccione un turno de la lista 'Mis Turnos Reservados' para cancelar.")
            return
            
        valores = self.tabla_mis_turnos.item(item_seleccionado, "values")
        id_turno = valores[0]
        medico = valores[1]
        dia = valores[3]
        horario = valores[4]
        
        # Prompts visual confirmando la cancelación
        confirmacion = messagebox.askyesno("Confirmar Cancelación", 
                                           f"¿Está seguro de que desea cancelar su turno?\n\nMédico: {medico}\nDía: {dia}\nHorario: {horario}")
        if confirmacion:
            conexion = sqlite3.connect("clinica.db")
            cursor = conexion.cursor()
            # El filtro por paciente añade una doble validación de seguridad (solo borra su propio turno)
            cursor.execute("DELETE FROM turnos WHERE id = ? AND paciente = ?", (id_turno, self.usuario_actual))
            conexion.commit()
            conexion.close()
            
            messagebox.showinfo("Éxito", "El turno fue cancelado correctamente.")
            self.cargar_mis_turnos()
            self.actualizar_horarios_disponibles()

    def cargar_mis_turnos(self):
        """
        Carga únicamente los turnos que están vinculados al nombre de usuario actual (paciente)
        y los muestra en el Treeview (tabla) inferior.
        """
        # Limpia las filas previas
        for fila in self.tabla_mis_turnos.get_children():
            self.tabla_mis_turnos.delete(fila)
            
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        # Filtra por la columna 'paciente' comparado con 'self.usuario_actual'
        cursor.execute("SELECT id, medico, especialidad, dia, horario FROM turnos WHERE paciente = ?", (self.usuario_actual,))
        filas = cursor.fetchall()
        conexion.close()
        
        for fila in filas:
            self.tabla_mis_turnos.insert("", tk.END, values=fila)

    # !!!!!!!!!!! MANEJO DE IMÁGENES DE FONDO !!!!!!!!!!!
    def poner_imagen_fondo_login(self):
        """
        Intenta cargar y mostrar la imagen 'fondo_azul.png' que servirá como textura 
        de fondo para las pantallas de Login y Registro. Si no la encuentra, ignora el error y usa color liso.
        """
        try:
            self.imagen_fondo = tk.PhotoImage(file="fondo_azul.png")
            self.label_fondo = tk.Label(self.root, image=self.imagen_fondo)
            # Con place definimos que ocupe desde las coordenadas 0,0 a lo ancho y largo de toda la ventana
            self.label_fondo.place(x=0, y=0, relwidth=1, relheight=1)
            # lower() empuja la imagen hacia atrás para no tapar los botones y textos.
            self.label_fondo.lower()
        except Exception:
            pass

    def poner_imagen_fondo_pac_y_admin(self):
        """
        Intenta cargar y mostrar la imagen 'fondo-paciente-admin.png' como textura 
        de fondo para las pantallas de los paneles de gestión. Si falta, pasa silenciosamente.
        """
        try:
            self.imagen_fondo = tk.PhotoImage(file="fondo-paciente-admin.png")
            self.label_fondo = tk.Label(self.root, image=self.imagen_fondo)
            self.label_fondo.place(x=0, y=0, relwidth=1, relheight=1)
            self.label_fondo.lower()
        except Exception:
            pass

# !!!!!!!!!!!! Ejecución del programa !!!!!!!!!!
if __name__ == "__main__":
    """
    Bloque principal de ejecución: Instancia la ventana raíz (root) de Tkinter,
    inicializa la lógica de ClinicaApp pasándole la ventana, y ejecuta 
    el mainloop (el bucle infinito que mantiene la app abierta respondiendo a clicks y teclado).
    """
    ventana_principal = tk.Tk()
    app = ClinicaApp(ventana_principal)
    ventana_principal.mainloop()