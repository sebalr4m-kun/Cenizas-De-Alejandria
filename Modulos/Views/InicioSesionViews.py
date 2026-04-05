from PySide6.QtWidgets import QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QPushButton, QLabel
from PySide6.QtCore import Qt

class VistaLogin(QDialog):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Acceso al Sistema - MATEO11-15")
        self.setModal(True)
        self.setFixedWidth(350)
        
        layout = QFormLayout(self)
        
        # Cambiamos la etiqueta y el placeholder para el Correo
        self.entrada_correo = QLineEdit()
        self.entrada_correo.setPlaceholderText("ejemplo@biblioteca.com")
        
        self.entrada_contrasena = QLineEdit()
        self.entrada_contrasena.setEchoMode(QLineEdit.Password)
        self.entrada_contrasena.setPlaceholderText("••••••••")
        
        layout.addRow("Correo Electrónico:", self.entrada_correo)
        layout.addRow("Contraseña:", self.entrada_contrasena)
        
        # Botón de recuperación (mantenemos tu estilo original)
        self.btn_recuperar = QPushButton("Olvidé mi contraseña")
        self.btn_recuperar.setStyleSheet("color: #3498db; text-decoration: underline; border: none; background: none;")
        self.btn_recuperar.setCursor(Qt.PointingHandCursor)
        layout.addRow(self.btn_recuperar)
        
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.boton_invitado = self.botones.addButton("Ingresar como Invitado", QDialogButtonBox.ActionRole)
        
        layout.addWidget(self.botones)