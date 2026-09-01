import tkinter as tk
from tkinter import messagebox

# ==========================================
# GESTIÓN DE TURNOS MÉDICOS - PASO 1: LOGIN
# ==========================================

class ClinicaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Turnos Médicos")
        self.root.geometry("400x300")
        self.root.config(padx=20, pady=20)
        
        # Base de datos simulada temporalmente (Usuario: [Contraseña, Rol])
        self.usuarios_db = {
            "admin": ["1234", "administrador"],
            "juan": ["paciente1", "paciente"]
        }

        self.crear_pantalla_login()

    def crear_pantalla_login(self):
        # Limpiar la ventana por si venimos de otra pantalla
        for widget in self.root.winfo_children():
            widget.destroy()

        # --- Elementos de la Interfaz (UI) ---
        
        # Título principal
        lbl_titulo = tk.Label(self.root, text="Bienvenido a la Clínica", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=10)

        # Campo para el Usuario
        tk.Label(self.root, text="Usuario:").pack()
        self.entry_usuario = tk.Entry(self.root)
        self.entry_usuario.pack(pady=5)

        # Campo para la Contraseña (con caracteres ocultos)
        tk.Label(self.root, text="Contraseña:").pack()
        self.entry_password = tk.Entry(self.root, show="*")
        self.entry_password.pack(pady=5)

        # Botón de Ingreso que ejecuta la validación
        btn_ingresar = tk.Button(self.root, text="Ingresar", command=self.validar_login, width=15)
        btn_ingresar.pack(pady=20)

    def validar_login(self):
        # Obtener los datos ingresados en los campos
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        # --- Control de Errores Básico ---
        if not usuario or not password:
            messagebox.showwarning("Error", "Por favor, complete todos los campos.")
            return

        # Validación contra la "base de datos"
        if usuario in self.usuarios_db and self.usuarios_db[usuario][0] == password:
            rol = self.usuarios_db[usuario][1]
            messagebox.showinfo("Éxito", f"Bienvenido {usuario}. Rol: {rol}")
            
            # Aquí llamaremos a la siguiente pantalla dependiendo del rol
            if rol == "administrador":
                 self.crear_pantalla_admin()
            else:
                 self.crear_pantalla_paciente()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

# --- Bloque Principal de Ejecución ---
if __name__ == "__main__":
    ventana_principal = tk.Tk()
    app = ClinicaApp(ventana_principal)
    ventana_principal.mainloop()