# Views/FormularioSesionesViews.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStackedWidget, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont

class FormularioSesiones(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        
        # --- PÁGINA 0: SIN SESIÓN (Login Centralizado) ---
        self.page_login = QWidget()
        page_login_layout = QVBoxLayout(self.page_login)
        page_login_layout.setAlignment(Qt.AlignCenter)
        
        card_login = QFrame()
        card_login.setObjectName("LoginCard") 
        card_login.setFixedWidth(380)
        card_login.setStyleSheet("""
            QFrame#LoginCard {
                background-color: rgba(25, 25, 25, 220); 
                border: 1px solid #333; 
                border-radius: 8px;
            }
        """)
        
        card_layout = QVBoxLayout(card_login)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        lbl_titulo_login = QLabel("INICIAR SESIÓN")
        lbl_titulo_login.setFont(QFont("Arial", 14, QFont.Bold))
        lbl_titulo_login.setAlignment(Qt.AlignCenter)
        lbl_titulo_login.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        card_layout.addWidget(lbl_titulo_login)
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Correo electrónico")
        self.input_email.setStyleSheet("background-color: #111111; color: #FFFFFF; border: 1px solid #444; padding: 8px; border-radius: 4px;")
        card_layout.addWidget(self.input_email)
        
        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText("Contraseña")
        self.input_pass.setEchoMode(QLineEdit.Password)
        self.input_pass.setStyleSheet("background-color: #111111; color: #FFFFFF; border: 1px solid #444; padding: 8px; border-radius: 4px;")
        card_layout.addWidget(self.input_pass)
        
        self.btn_login = QPushButton("Ingresar")
        self.btn_login.setFixedHeight(38)
        self.btn_login.setFont(QFont("Arial", 11, QFont.Bold))
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #2A52BE; 
                color: #FFFFFF; 
                border: none; 
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1F3D8C; }
        """)
        self.btn_login.setCursor(QCursor(Qt.PointingHandCursor))
        card_layout.addWidget(self.btn_login)
        
        links_layout = QHBoxLayout()
        lbl_recuperar = QLabel("<a href='#' style='color:#AAAAAA; text-decoration:none; font-size:11px;'>Olvidé mi contraseña</a>")
        lbl_recuperar.setStyleSheet("background: transparent;")
        lbl_registro = QLabel("<a href='#' style='color:#AAAAAA; text-decoration:none; font-size:11px;'>Registrarse</a>")
        lbl_registro.setStyleSheet("background: transparent;")
        
        links_layout.addWidget(lbl_recuperar)
        links_layout.addStretch()
        links_layout.addWidget(lbl_registro)
        card_layout.addLayout(links_layout)
        
        page_login_layout.addWidget(card_login)
        
        # --- PÁGINA 1: CON SESIÓN ACTIVA ---
        self.page_activa = QWidget()
        page_activa_layout = QVBoxLayout(self.page_activa)
        page_activa_layout.setAlignment(Qt.AlignCenter)
        
        card_activa = QFrame()
        card_activa.setObjectName("ActivaCard")
        card_activa.setFixedWidth(380)
        card_activa.setStyleSheet("""
            QFrame#ActivaCard {
                background-color: rgba(25, 25, 25, 220); 
                border: 1px solid #333; 
                border-radius: 8px;
            }
        """)
        
        card_activa_layout = QVBoxLayout(card_activa)
        card_activa_layout.setContentsMargins(20, 20, 20, 20)
        card_activa_layout.setSpacing(15)
        
        user_header_layout = QVBoxLayout()
        user_header_layout.setAlignment(Qt.AlignCenter)
        user_header_layout.setSpacing(5)
        
        self.lbl_nombre_usuario = QLabel("Nombre de Usuario")
        self.lbl_nombre_usuario.setAlignment(Qt.AlignCenter)
        self.lbl_nombre_usuario.setFont(QFont("Arial", 14, QFont.Bold))
        self.lbl_nombre_usuario.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        user_header_layout.addWidget(self.lbl_nombre_usuario)
        
        self.lbl_email_usuario = QLabel("usuario@email.com")
        self.lbl_email_usuario.setAlignment(Qt.AlignCenter)
        self.lbl_email_usuario.setFont(QFont("Arial", 10))
        self.lbl_email_usuario.setStyleSheet("color: #00E5FF; background: transparent; border: none;")
        user_header_layout.addWidget(self.lbl_email_usuario)

        self.lbl_fecha_registro = QLabel("Miembro desde: DD/MM/AAAA")
        self.lbl_fecha_registro.setAlignment(Qt.AlignCenter)
        self.lbl_fecha_registro.setFont(QFont("Arial", 9))
        self.lbl_fecha_registro.setStyleSheet("color: #AAAAAA; background: transparent; border: none;")
        user_header_layout.addWidget(self.lbl_fecha_registro)
        
        card_activa_layout.addLayout(user_header_layout)
        
        card_activa_layout.addSpacing(15)
        
        self.btn_logout = QPushButton("Cerrar Sesión")
        self.btn_logout.setFixedHeight(35)
        self.btn_logout.setStyleSheet("background-color: #444444; color: #FFFFFF; border: none; border-radius: 4px; font-weight: bold;")
        self.btn_logout.setCursor(QCursor(Qt.PointingHandCursor))
        card_activa_layout.addWidget(self.btn_logout)
        
        self.btn_borrar = QPushButton("Borrar Cuenta")
        self.btn_borrar.setFixedHeight(35)
        self.btn_borrar.setStyleSheet("background-color: #8B0000; color: #FFFFFF; border: none; border-radius: 4px; font-weight: bold;")
        self.btn_borrar.setCursor(QCursor(Qt.PointingHandCursor))
        card_activa_layout.addWidget(self.btn_borrar)
        
        page_activa_layout.addWidget(card_activa)
        
        self.stacked_widget.addWidget(self.page_login)
        self.stacked_widget.addWidget(self.page_activa)
        
        layout.addWidget(self.stacked_widget)

    def cambiar_a_sesion_activa(self, nombre, email, fecha_registro):
        self.lbl_nombre_usuario.setText(nombre)
        self.lbl_email_usuario.setText(email)
        self.lbl_fecha_registro.setText(f"Miembro desde: {fecha_registro}")
        self.stacked_widget.setCurrentIndex(1)

    def cambiar_a_login(self):
        self.input_email.clear()
        self.input_pass.clear()
        self.stacked_widget.setCurrentIndex(0)