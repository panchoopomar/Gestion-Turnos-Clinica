import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import hashlib

# ==========================================
# GESTIÓN DE TURNOS MÉDICOS - LOGIN Y REGISTRO
# ==========================================

class ClinicaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Turnos Médicos")
        self.root.geometry("400x350")
        self.root.config(padx=20, pady=20)
        
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

        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='administrador'")
        if cursor.fetchone()[0] == 0:
            # Lista de administradores a precargar (email/usuario, contraseña)
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

    # --- PANTALLA DE LOGIN ---
    def crear_pantalla_login(self):
        self.limpiar_ventana()
        
        tk.Label(self.root, text="Bienvenido a la Clínica", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(self.root, text="Email / Usuario:").pack()
        self.entry_usuario = tk.Entry(self.root)
        self.entry_usuario.pack(pady=5)

        tk.Label(self.root, text="Contraseña:").pack()
        self.entry_password = tk.Entry(self.root, show="*")
        self.entry_password.pack(pady=5)

        tk.Button(self.root, text="Ingresar", command=self.validar_login, width=20).pack(pady=10)
        
        # Botón para ir a la pantalla de registro
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
                
        else:
            messagebox.showerror("Error", "Email/Usuario o contraseña incorrectos.")

    # --- PANTALLA DE REGISTRO DE PACIENTE ---
    def crear_pantalla_registro(self):
        self.limpiar_ventana()

        tk.Label(self.root, text="Registro de Nuevo Paciente", font=("Arial", 14, "bold")).pack(pady=10)

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

        # Control de errores en el registro
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
            # Si el email ya existe, SQLite lanzará un error porque definimos 'username' como UNIQUE
            cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                           (email, pass_hash, 'paciente'))
            conexion.commit()
            messagebox.showinfo("Éxito", "Paciente registrado correctamente. Ya puede iniciar sesión.")
            self.crear_pantalla_login() # Volvemos al login automáticamente
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ese email ya se encuentra registrado.")
        finally:
            conexion.close()

    def limpiar_ventana(self):
        """Utilidad para borrar los widgets de la pantalla actual antes de dibujar otra."""
        for widget in self.root.winfo_children():
            widget.destroy()
            
    # --- PANTALLA DE ADMINISTRADOR ---
    def crear_pantalla_admin(self):
        self.limpiar_ventana()
        self.root.geometry("700x500") # Agrandamos la ventana para que entre todo

        tk.Label(self.root, text="Panel de Administrador - Gestión de Médicos", font=("Arial", 16, "bold")).pack(pady=10)

        # Marco para el formulario (minimalista y ordenado)
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

        tk.Label(frame_form, text="Horarios:").grid(row=1, column=2, padx=5, pady=5)
        self.entry_med_horarios = tk.Entry(frame_form)
        self.entry_med_horarios.grid(row=1, column=3, padx=5, pady=5)

        # Botones de Acción de la pantalla admin
        frame_botones = tk.Frame(self.root)
        frame_botones.pack(pady=10)
        
        tk.Button(frame_botones, text="Agregar", command=self.agregar_medico, width=15).grid(row=0, column=0, padx=10)
        tk.Button(frame_botones, text="Modificar", command=self.modificar_medico, width=15).grid(row=0, column=1, padx=10)
        tk.Button(frame_botones, text="Eliminar", command=self.eliminar_medico, width=15).grid(row=0, column=2, padx=10)
        tk.Button(frame_botones, text="Cerrar Sesión", command=self.crear_pantalla_login, width=15).grid(row=0, column=3, padx=10)

        # Tabla (Treeview) para mostrar a los médicos
        self.tabla_medicos = ttk.Treeview(self.root, columns=("ID", "Nombre", "Especialidad", "Días", "Horarios"), show="headings")
        self.tabla_medicos.heading("ID", text="ID")
        self.tabla_medicos.heading("Nombre", text="Nombre")
        self.tabla_medicos.heading("Especialidad", text="Especialidad")
        self.tabla_medicos.heading("Días", text="Días")
        self.tabla_medicos.heading("Horarios", text="Horarios")
        
        # Ajustar anchos de las columnas
        self.tabla_medicos.column("ID", width=30)
        self.tabla_medicos.column("Nombre", width=150)
        self.tabla_medicos.column("Especialidad", width=150)
        self.tabla_medicos.column("Días", width=120)
        self.tabla_medicos.column("Horarios", width=120)
        
        self.tabla_medicos.pack(pady=10, fill="x", padx=20)
        
        # usuario hace clic en una fila de la tabla
        self.tabla_medicos.bind("<ButtonRelease-1>", self.seleccionar_medico)
        
        # Cargar los médicos ni bien se abre la pantalla del admin
        self.cargar_medicos()
        
    def cargar_medicos(self):
        """Lee los médicos de la base de datos y los muestra en la tabla."""
        # limpiamos la tabla por las dudas
        for fila in self.tabla_medicos.get_children():
            self.tabla_medicos.delete(fila)
        
        # Consultamos a SQLite
        conexion = sqlite3.connect("clinica.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM medicos")
        filas = cursor.fetchall()
        conexion.close()

        # Insertamos cada fila en el Treeview
        for fila in filas:
            self.tabla_medicos.insert("", tk.END, values=fila)
            
    def limpiar_campos_medico(self):
        """Vacía las cajas de texto del formulario."""
        self.entry_med_nombre.delete(0, tk.END)
        self.entry_med_especialidad.delete(0, tk.END)
        self.entry_med_dias.delete(0, tk.END)
        self.entry_med_horarios.delete(0, tk.END)

    def agregar_medico(self):
        """Agrega un nuevo médico a la base de datos."""
        nombre = self.entry_med_nombre.get().strip()
        especialidad = self.entry_med_especialidad.get().strip()
        dias = self.entry_med_dias.get().strip()
        horarios = self.entry_med_horarios.get().strip()

        # Sacar campos vacíos
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
        self.cargar_medicos() # Actualizamos la tabla

    def seleccionar_medico(self, event):
        """Rellena el formulario cuando haces clic en un médico de la tabla."""
        item_seleccionado = self.tabla_medicos.focus()
        if not item_seleccionado:
            return
        
        valores = self.tabla_medicos.item(item_seleccionado, "values")
        
        self.limpiar_campos_medico()
        # values[0] es el ID, values[1] es el nombre, etc.
        self.entry_med_nombre.insert(0, valores[1])
        self.entry_med_especialidad.insert(0, valores[2])
        self.entry_med_dias.insert(0, valores[3])
        self.entry_med_horarios.insert(0, valores[4])

    def modificar_medico(self):
        """Actualiza los datos del médico seleccionado en la tabla."""
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
        """Borra un médico de la base de datos."""
        item_seleccionado = self.tabla_medicos.focus()
        if not item_seleccionado:
            messagebox.showwarning("Error", "Seleccione un médico de la tabla para eliminar.")
            return

        valores = self.tabla_medicos.item(item_seleccionado, "values")
        id_medico = valores[0]
        nombre_medico = valores[1]

        # confirmación
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

# --- Ejecución del programa ---
if __name__ == "__main__":
    ventana_principal = tk.Tk()
    app = ClinicaApp(ventana_principal)
    ventana_principal.mainloop()