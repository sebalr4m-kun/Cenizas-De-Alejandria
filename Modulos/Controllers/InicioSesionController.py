from PySide6.QtWidgets import QMessageBox
from Modulos.Models.InicioSesionModels import LoginModel
from Modulos.Views.InicioSesionViews import VistaLogin
from Modulos.PasswordRecover import ValidadorRecuperacion

class ControladorLogin:
    def __init__(self):
        self.model = LoginModel()
        self.vista = VistaLogin()

        # Datos de salida
        self.rol = "ninguno"
        self.nombre_usuario = ""
        self.autenticado = False

        # Conectar señales de la vista
        self.vista.botones.accepted.connect(self.intentar_login)
        self.vista.botones.rejected.connect(self.vista.reject)
        self.vista.boton_invitado.clicked.connect(self.aceptar_invitado)
        self.vista.btn_recuperar.clicked.connect(self.ejecutar_recuperacion)

    def ejecutar(self):
        """Muestra el diálogo y devuelve si se autenticó o no"""
        # === Chequeo automático del Modo Admin ANTES de mostrar el login ===
        if not self.model.hay_bibliotecario_activo():
            QMessageBox.information(
                None, 
                "Modo Config", 
                "No hay bibliotecario. Modo admin activado."
            )
            self.rol = "admin"
            self.nombre_usuario = "Administrador (Modo Desarrollo)"
            self.autenticado = True
            return True  # ← Simula que el login fue exitoso

        # Si hay bibliotecarios, mostramos el diálogo normal
        return self.vista.exec()

    def intentar_login(self):
        correo = self.vista.entrada_correo.text().strip()
        password = self.vista.entrada_contrasena.text().strip()

        if not correo or not password:
            QMessageBox.warning(self.vista, "Error", "Por favor, complete todos los campos.")
            return

        usuario = self.model.verificar_credenciales(correo, password)

        if usuario:
            self.rol = usuario['rol']
            self.nombre_usuario = usuario['nombre']
            self.autenticado = True
            self.vista.accept()
        else:
            QMessageBox.critical(self.vista, "Fallo de Inicio", "Correo o contraseña incorrectos.")

    def ejecutar_recuperacion(self):
        validador = ValidadorRecuperacion(self.vista)
        if validador.exec():
            self.rol = "admin"
            self.nombre_usuario = "Recuperado_Por_Llave"
            self.autenticado = True
            self.vista.accept()

    def aceptar_invitado(self):
        self.rol = "invitado"
        self.nombre_usuario = "Invitado"
        self.autenticado = True
        self.vista.accept()

    def obtener_resultado(self):
        return self.rol, self.nombre_usuario