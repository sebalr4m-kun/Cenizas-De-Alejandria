import random
import socket
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from Modulos.Config import Conexion

class ValidadorRecuperacion(QDialog):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.setWindowTitle("SEGURIDAD - CENIZAS DE ALEJANDRÍA")
        self.setFixedSize(460, 560)
        self.setModal(True)
        self.bd = Conexion().obtener_conexion()
        
        # Variables de control
        self.id_usuario_local = None
        self.email_usuario = None
        self.palabras_correctas = {} 
        self.expiracion_token = None
        self.metodo_online = False
        self.intentos_fallidos = 0 # Contador de seguridad
        
        self.aplicar_estilos_vanta()
        self.init_ui()

    def aplicar_estilos_vanta(self):
        """Estética de alto contraste extremo con texto negro puro."""
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

    def verificar_conexion(self):
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

        # Modificación de texto generalizado para RBAC
        self.etiqueta_instruccion = QLabel("Correo de la Cuenta Admitida:")
        self.layout_principal.addWidget(self.etiqueta_instruccion)

        self.entrada_email = QLineEdit()
        self.entrada_email.setPlaceholderText("usuario@ejemplo.com")
        self.layout_principal.addWidget(self.entrada_email)

        self.btn_verificar_mail = QPushButton("Validar Cuenta")
        self.btn_verificar_mail.setCursor(Qt.PointingHandCursor)
        self.btn_verificar_mail.clicked.connect(self.preparar_desafio)
        self.layout_principal.addWidget(self.btn_verificar_mail)

        self.contenedor_desafio = QVBoxLayout()
        self.layout_principal.addLayout(self.contenedor_desafio)

        self.btn_validar_desafio = QPushButton("Confirmar Credenciales")
        self.btn_validar_desafio.setObjectName("btnConfirmar")
        self.btn_validar_desafio.setCursor(Qt.PointingHandCursor)
        self.btn_validar_desafio.clicked.connect(self.verificar_respuestas)
        self.btn_validar_desafio.hide()
        self.btn_validar_desafio.setEnabled(False) 
        self.layout_principal.addWidget(self.btn_validar_desafio)

    def preparar_desafio(self):
        self.email_usuario = self.entrada_email.text().strip()
        if not self.email_usuario: 
            QMessageBox.warning(self, "Error", "Ingrese un correo.")
            return

        self.btn_verificar_mail.setEnabled(False)
        self.btn_verificar_mail.setText("Comprobando...")
        QApplication.processEvents() 

        cursor = self.bd.cursor(dictionary=True)
        try:
            # === OPTIMIZACIÓN RBAC: Cambio de 'Bibliotecario' por 'admitido = 1' ===
            query = """
                SELECT u.id_usuario FROM usuarios u
                JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                WHERE u.email = %s AND p.admitido = 1
            """
            cursor.execute(query, (self.email_usuario,))
            usuario = cursor.fetchone()

            if not usuario:
                QMessageBox.critical(self, "Acceso Denegado", "El correo ingresado no pertenece a una cuenta admitida para este proceso.")
                self.btn_verificar_mail.setEnabled(True)
                self.btn_verificar_mail.setText("Validar Cuenta")
                return

            self.id_usuario_local = usuario['id_usuario']
            
            if self.verificar_conexion():
                self.metodo_online = True
                self.generar_desafio_email(cursor)
            else:
                self.metodo_online = False
                self.generar_desafio_local(cursor)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.btn_verificar_mail.setEnabled(True)
        finally:
            cursor.close()

    def generar_desafio_email(self, cursor):
        cursor.execute("SELECT palabra FROM param_diccionario_seguridad ORDER BY RAND() LIMIT 3")
        palabras = [row['palabra'] for row in cursor.fetchall()]
        self.palabras_correctas = {i+1: p for i, p in enumerate(palabras)}
        self.expiracion_token = datetime.now() + timedelta(minutes=10)
        
        if self.enviar_correo(palabras):
            self.mostrar_interfaz_desafio("CÓDIGO ENVIADO\nIngrese las 3 palabras:")
        else:
            self.generar_desafio_local(cursor)

    def generar_desafio_local(self, cursor):
        cursor.execute("SELECT indices_palabras FROM seguridad_recuperacion WHERE id_usuario = %s", (self.id_usuario_local,))
        res = cursor.fetchone()
        if not res:
            QMessageBox.critical(self, "Error", "Sin llaves offline. Contacte a un administrador.")
            self.btn_verificar_mail.setEnabled(True)
            return

        indices = [int(i) for i in res['indices_palabras'].split(",")]
        pos_elegidas = random.sample(range(12), 3)
        pos_elegidas.sort()

        for pos in pos_elegidas:
            cursor.execute("SELECT palabra FROM param_diccionario_seguridad WHERE id_palabra = %s", (indices[pos],))
            self.palabras_correctas[pos + 1] = cursor.fetchone()['palabra']

        self.mostrar_interfaz_desafio("MODO OFFLINE\nConsulte sus llaves físicas:")

    def enviar_correo(self, palabras):
        try:
            remitente = "414nX4rd@gmail.com"
            password = "lvjzabsitxrxwqmr" 
            cuerpo = f"Palabras de Recuperación RBAC:\n1. {palabras[0]}\n2. {palabras[1]}\n3. {palabras[2]}"
            msg = MIMEText(cuerpo)
            # Modificación de texto del asunto para desplazar 'Bibliotecario'
            msg['Subject'] = "Seguridad de Acceso - Cenizas de Alejandría"
            msg['From'] = remitente
            msg['To'] = self.email_usuario
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(remitente, password)
                server.send_message(msg)
            return True
        except: return False

    def mostrar_interfaz_desafio(self, mensaje):
        self.entrada_email.hide()
        self.btn_verificar_mail.hide()
        self.etiqueta_instruccion.setText(mensaje)
        self.etiqueta_instruccion.setStyleSheet("color: #000000; font-weight: 900; font-size: 16px; margin-bottom: 10px;")

        self.inputs_desafio = {}
        for pos in self.palabras_correctas.keys():
            lbl = QLabel(f"Palabra {pos}:")
            edit = QLineEdit()
            if not self.metodo_online: edit.setEchoMode(QLineEdit.Password)
            edit.textChanged.connect(self.validar_campos_completos)
            self.contenedor_desafio.addWidget(lbl)
            self.contenedor_desafio.addWidget(edit)
            self.inputs_desafio[pos] = edit

        self.btn_validar_desafio.show()

    def validar_campos_completos(self):
        completos = all(len(edit.text().strip()) > 0 for edit in self.inputs_desafio.values())
        self.btn_validar_desafio.setEnabled(completos)

    def verificar_respuestas(self):
        """Verifica respuestas con sistema de 3 intentos."""
        if self.metodo_online and datetime.now() > self.expiracion_token:
            QMessageBox.warning(self, "Expirado", "El tiempo ha terminado.")
            self.reject()
            return

        aciertos = 0
        for pos, palabra_real in self.palabras_correctas.items():
            if self.inputs_desafio[pos].text().strip().lower() == palabra_real.lower():
                aciertos += 1
        
        if aciertos == 3:
            QMessageBox.information(self, "Éxito", "Identidad confirmada. Redirigiendo al sistema...")
            self.accept()
        else:
            self.intentos_fallidos += 1
            restantes = 3 - self.intentos_fallidos
            
            if restantes > 0:
                QMessageBox.warning(self, "Error", f"Palabras incorrectas. Quedan {restantes} intentos.")
                for edit in self.inputs_desafio.values(): edit.clear()
            else:
                QMessageBox.critical(self, "Bloqueo de Seguridad", "Demasiados intentos fallidos. Volviendo al inicio.")
                self.reject()