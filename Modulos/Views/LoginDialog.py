from PySide6.QtWidgets import QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QPushButton
from PySide6.QtCore import Qt
# Importamos tu nuevo validador
from Modulos.PasswordRecover import ValidadorRecuperacion

class DialogoLogin(QDialog):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Inicio de Sesión")
        self.setModal(True)
        
        # Guardamos el rol y el nombre de usuario resultante
        self.rol = "ninguno"
        self.nombre_usuario = ""
        
        self.entrada_nombre = QLineEdit()
        self.entrada_contrasena = QLineEdit()
        self.entrada_contrasena.setEchoMode(QLineEdit.Password)
        
        layout = QFormLayout(self)
        layout.addRow("Nombre del Bibliotecario:", self.entrada_nombre)
        layout.addRow("Contraseña:", self.entrada_contrasena)
        
        # --- BOTÓN DE RECUPERACIÓN ---
        self.btn_recuperar = QPushButton("Olvidé mi contraseña")
        self.btn_recuperar.setStyleSheet("color: blue; text-decoration: underline; border: none; background: none;")
        self.btn_recuperar.setCursor(Qt.PointingHandCursor)
        self.btn_recuperar.clicked.connect(self.ejecutar_recuperacion)
        layout.addRow(self.btn_recuperar)
        
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.boton_invitado = self.botones.addButton("Ingresar como Invitado", QDialogButtonBox.ActionRole)
        
        layout.addWidget(self.botones)
        
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)
        self.boton_invitado.clicked.connect(self.aceptar_invitado)

    def ejecutar_recuperacion(self):
        """Llama al desafío de las 12 palabras"""
        validador = ValidadorRecuperacion(self)
        if validador.exec():
            # Si pasa el desafío, marcamos el bypass
            self.rol = "admin"
            self.nombre_usuario = "Recuperado_Por_Llave"
            self.accept()

    def aceptar_invitado(self):
        self.rol = "invitado"
        self.accept()

    def obtener_credenciales(self):
        if self.rol == "invitado":
            return ("invitado", None, None)
        
        # Si ya se definió el rol por recuperación, enviamos el TOKEN DE BYPASS
        if self.rol == "admin" and self.nombre_usuario == "Recuperado_Por_Llave":
            return ("admin", "Bibliotecario", "BYPASS_RECOVERY")
            
        return ("admin", self.entrada_nombre.text(), self.entrada_contrasena.text())