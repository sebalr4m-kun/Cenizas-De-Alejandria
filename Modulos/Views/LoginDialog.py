from PySide6.QtWidgets import QDialog, QLineEdit, QFormLayout, QDialogButtonBox
from PySide6.QtCore import Qt

class DialogoLogin(QDialog):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Inicio de Sesión")
        self.setModal(True)
        self.entrada_nombre = QLineEdit()
        self.entrada_contrasena = QLineEdit()
        self.entrada_contrasena.setEchoMode(QLineEdit.Password)
        
        layout = QFormLayout(self)
        layout.addRow("Nombre del Bibliotecario:", self.entrada_nombre)
        layout.addRow("Contraseña:", self.entrada_contrasena)
        
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.boton_invitado = self.botones.addButton("Ingresar como Invitado", QDialogButtonBox.ActionRole)
        
        layout.addWidget(self.botones)
        
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)
        self.boton_invitado.clicked.connect(self.aceptar_invitado)
        
        self.rol = "ninguno"

    def aceptar_invitado(self):
        self.rol = "invitado"
        self.accept()

    def obtener_credenciales(self):
        if self.rol == "invitado":
            return ("invitado", None, None)
            
        return ("admin", self.entrada_nombre.text(), self.entrada_contrasena.text())