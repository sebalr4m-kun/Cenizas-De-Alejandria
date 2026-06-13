import random
import socket
import smtplib
from email.mime.text import MIMEText
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication
)
from PySide6.QtCore import Qt

class ValidadorCuenta(QDialog):
    """
    Controlador visual para la validación de correos electrónicos.
    Refactorizado para coincidir con el estilo y lógica de PasswordRecover,
    solicitando únicamente 3 palabras al azar y asistiendo en el debugging.
    """
    def __init__(self, palabras_completas, email_usuario, padre=None):
        if not isinstance(email_usuario, str):
            padre_real = email_usuario
            if hasattr(padre_real, 'entrada_email'):
                email_rescatado = padre_real.entrada_email.text().strip()
            else:
                email_rescatado = ""
            super().__init__(padre_real)
            self.email_usuario = email_rescatado
        else:
            super().__init__(padre)
            self.email_usuario = email_usuario
            
        self.intentos_fallidos = 0
        self.inputs_desafio = {}
        
        pos_elegidas = random.sample(range(12), 3)
        pos_elegidas.sort()
        self.palabras_correctas = {pos + 1: palabras_completas[pos].strip().lower() for pos in pos_elegidas}
        
        self.setWindowTitle("SEGURIDAD - CENIZAS DE ALEJANDRÍA")
        self.setFixedSize(460, 560)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        self.aplicar_estilos_vanta()
        self.init_ui()
        
        if self.verificar_conexion():
            self.enviar_correo()

    def aplicar_estilos_vanta(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                color: #000000;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #000000;
                font-size: 15px;
                font-weight: 700;
                margin-top: 5px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #000000;
                border: 2px solid #000000;
                border-radius: 4px;
                padding: 12px; 
                font-size: 16px;
                font-weight: 600;
                min-height: 25px; 
            }
            QLineEdit:focus {
                border: 3px solid #2980B9;
                background-color: #F0F7FF;
            }
            QPushButton {
                background-color: #2980B9;
                color: #000000;
                border-radius: 5px;
                padding: 14px;
                font-size: 15px;
                font-weight: 900;
                border: 2px solid #000000;
            }
            #btnConfirmar {
                background-color: #27AE60;
                color: #000000;
            }
            #btnConfirmar:hover {
                background-color: #2ECC71;
            }
            #btnConfirmar:disabled {
                background-color: #BDC3C7;
                color: #444444;
                border: 2px solid #7F8C8D;
            }
        """)

    @staticmethod
    def verificar_conexion():
        try:
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except socket.error:
            return False

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(45, 40, 45, 40)
        self.layout_principal.setSpacing(8)

        self.lbl_titulo = QLabel("VERIFICACIÓN DE IDENTIDAD")
        self.lbl_titulo.setStyleSheet("font-size: 22px; font-weight: 900; color: #000000; margin-bottom: 25px;")
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        self.layout_principal.addWidget(self.lbl_titulo)

        self.lbl_instrucciones = QLabel("CÓDIGO ENVIADO\nIngrese las 3 palabras asignadas:")
        self.lbl_instrucciones.setStyleSheet("color: #000000; font-weight: 900; font-size: 16px; margin-bottom: 10px;")
        self.lbl_instrucciones.setAlignment(Qt.AlignCenter)
        self.layout_principal.addWidget(self.lbl_instrucciones)

        for pos in self.palabras_correctas.keys():
            lbl = QLabel(f"Palabra {pos}:")
            edit = QLineEdit()
            edit.textChanged.connect(self.validar_campos_completos)
            self.layout_principal.addWidget(lbl)
            self.layout_principal.addWidget(edit)
            self.inputs_desafio[pos] = edit

        self.btn_validar = QPushButton("Confirmar Credenciales")
        self.btn_validar.setObjectName("btnConfirmar")
        self.btn_validar.setCursor(Qt.PointingHandCursor)
        self.btn_validar.setEnabled(False)
        self.btn_validar.clicked.connect(self.verificar_respuestas)
        self.layout_principal.addWidget(self.btn_validar)

    def validar_campos_completos(self):
        completos = all(len(edit.text().strip()) > 0 for edit in self.inputs_desafio.values())
        self.btn_validar.setEnabled(completos)

    def enviar_correo(self):
        try:
            remitente = "414nX4rd@gmail.com"
            password = "lvjzabsitxrxwqmr" 
            
            print("\n" + "="*50)
            print(f"[DEBUG - CÓDIGOS DE VALIDACIÓN PARA: {self.email_usuario}]")
            texto_cuerpo = []
            for pos, palabra in self.palabras_correctas.items():
                linea = f"Palabra {pos}: {palabra.upper()}"
                texto_cuerpo.append(linea)
                print(linea)
            print("="*50 + "\n")

            cuerpo = "Claves de validación de seguridad de Cenizas de Alejandría:\n\n" + "\n".join(texto_cuerpo)
            
            msg = MIMEText(cuerpo, 'plain', 'utf-8')
            msg['Subject'] = "Seguridad - Bibliotecario"
            msg['From'] = remitente
            msg['To'] = self.email_usuario
            
            # BLINDAJE: local_hostname='localhost' anula la lectura del nombre de la computadora y evita el error ASCII
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, local_hostname='localhost') as server:
                server.login(remitente, password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERROR DE RED] No se pudo enviar el correo a {self.email_usuario}: {e}")
            return False

    def verificar_respuestas(self):
        aciertos = 0
        for pos, palabra_real in self.palabras_correctas.items():
            if self.inputs_desafio[pos].text().strip().lower() == palabra_real.lower():
                aciertos += 1
        
        if aciertos == 3:
            QMessageBox.information(self, "Éxito", "Identidad confirmada. La cuenta ha sido activada.")
            self.accept()
        else:
            self.intentos_fallidos += 1
            restantes = 3 - self.intentos_fallidos
            
            if restantes > 0:
                QMessageBox.warning(self, "Error", f"Palabras incorrectas. Quedan {restantes} intentos.")
                for edit in self.inputs_desafio.values():
                    edit.clear()
                self.btn_validar.setEnabled(False)
            else:
                QMessageBox.critical(self, "Bloqueo de Seguridad", "Validación fallida. Bloqueo de seguridad activado.")
                self.reject()