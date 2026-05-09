import re
import socket
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

class ValidadorCuenta(QDialog):
    """
    Controlador visual para la validación de correos electrónicos.
    Compara las palabras maestras ingresadas con las generadas por el sistema
    en el momento de la creación.
    """
    def __init__(self, palabras_correctas, padre=None):
        super().__init__(padre)
        # Normalizamos las palabras para evitar fallos por espacios o mayúsculas
        self.palabras_correctas = [p.strip().lower() for p in palabras_correctas]
        self.intentos_restantes = 3
        
        self.setWindowTitle("VALIDACIÓN DE IDENTIDAD - CENIZAS DE ALEJANDRÍA")
        self.setFixedSize(400, 280)
        self.setModal(True)
        # Bloqueamos el cierre accidental (debe validar o fallar)
        self.setWindowFlags(Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        titulo = QLabel("Verificación de Bibliotecario")
        titulo.setStyleSheet("font-weight: bold; font-size: 16px; color: #00FF00;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        instrucciones = QLabel(
            "Se ha enviado un código de seguridad a su correo.\n"
            "Por favor, ingrese las palabras maestras para activar su cuenta."
        )
        instrucciones.setWordWrap(True)
        instrucciones.setAlignment(Qt.AlignCenter)
        layout.addWidget(instrucciones)

        self.entrada_codigo = QLineEdit()
        self.entrada_codigo.setPlaceholderText("Pegue o escriba sus palabras aquí...")
        self.entrada_codigo.setMinimumHeight(40)
        self.entrada_codigo.setStyleSheet("""
            background-color: #1e1e1e; 
            color: #00FF00; 
            font-family: 'Consolas';
            border: 1px solid #333;
        """)
        layout.addWidget(self.entrada_codigo)

        self.lbl_intentos = QLabel(f"Intentos restantes: {self.intentos_restantes}")
        self.lbl_intentos.setStyleSheet("color: #FF8800; font-weight: bold;")
        self.lbl_intentos.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_intentos)

        self.btn_validar = QPushButton("Validar y Activar")
        self.btn_validar.setMinimumHeight(45)
        self.btn_validar.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_validar.clicked.connect(self.verificar_codigo)
        layout.addWidget(self.btn_validar)

    def verificar_codigo(self):
        # Regex para extraer solo palabras (ignora números de lista como '1. hola')
        texto_usuario = self.entrada_codigo.text().strip().lower()
        palabras_usuario = re.findall(r'[a-z]+', texto_usuario)

        # Validación de secuencia exacta
        if len(palabras_usuario) == len(self.palabras_correctas) and \
           all(p == c for p, c in zip(palabras_usuario, self.palabras_correctas)):
            QMessageBox.information(self, "Éxito", "Identidad confirmada. La cuenta ha sido activada.")
            self.accept()
        else:
            self.intentos_restantes -= 1
            self.lbl_intentos.setText(f"Intentos restantes: {self.intentos_restantes}")
            
            if self.intentos_restantes <= 0:
                QMessageBox.critical(self, "Error Crítico", 
                    "Validación fallida. La cuenta no será creada por seguridad.")
                self.reject()
            else:
                QMessageBox.warning(self, "Código Incorrecto", 
                    "Las palabras no coinciden. Verifique el orden y vuelva a intentarlo.")
                self.entrada_codigo.clear()

    @staticmethod
    def verificar_conexion():
        """Verifica si hay señal para el envío del correo de validación."""
        try:
            # Intento de conexión al DNS de Google
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False