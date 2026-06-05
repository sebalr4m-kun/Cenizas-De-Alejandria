from PySide6.QtWidgets import QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

class VistaLogin(QDialog):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Acceso al Sistema - Cenizas De Alejandría")
        self.setModal(True)
        self.setFixedWidth(380) # Un ancho ligeramente mayor para mejorar las proporciones áureas del cuadro
        
        # Aplicamos una hoja de estilos global, limpia y profesional para esta ventana
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f6fa;
            }
            QLabel {
                font-size: 13px;
                color: #2f3640;
                font-weight: 500;
            }
        """)
        
        # Layout principal vertical para estructurar el contenido con márgenes elegantes
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 35, 30, 25)
        layout_principal.setSpacing(15)
        
        # Encabezado estético interno para que parezca un software pulido
        self.lbl_titulo = QLabel("Cenizas de Alejandría")
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        self.lbl_titulo.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #2c3e50;
            margin-bottom: 2px;
        """)
        layout_principal.addWidget(self.lbl_titulo)
        
        self.lbl_subtitulo = QLabel("Por favor, introduce tus credenciales de acceso")
        self.lbl_subtitulo.setAlignment(Qt.AlignCenter)
        self.lbl_subtitulo.setStyleSheet("font-size: 12px; color: #7f8c8d; margin-bottom: 15px;")
        layout_principal.addWidget(self.lbl_subtitulo)
        
        # Formulario para los campos de texto
        layout_formulario = QFormLayout()
        layout_formulario.setSpacing(12)
        layout_formulario.setLabelAlignment(Qt.AlignLeft)
        
        # Estilo moderno para las casillas de entrada (Bordes suaves, padding y enfoque reactivo)
        estilo_inputs = """
            QLineEdit {
                padding: 8px 12px;
                font-size: 13px;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2f3640;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background-color: #ffffff;
            }
        """
        
        self.entrada_correo = QLineEdit()
        self.entrada_correo.setPlaceholderText("ejemplo@biblioteca.com")
        self.entrada_correo.setStyleSheet(estilo_inputs)
        
        self.entrada_contrasena = QLineEdit()
        self.entrada_contrasena.setEchoMode(QLineEdit.Password)
        self.entrada_contrasena.setPlaceholderText("••••••••")
        self.entrada_contrasena.setStyleSheet(estilo_inputs)
        
        layout_formulario.addRow("Correo Electrónico:", self.entrada_correo)
        layout_formulario.addRow("Contraseña:", self.entrada_contrasena)
        layout_principal.addLayout(layout_formulario)
        
        # Botón de recuperación (Mantiene tu enlace original pero refinando su comportamiento de selección)
        self.btn_recuperar = QPushButton("Olvidé mi contraseña")
        self.btn_recuperar.setStyleSheet("""
            QPushButton {
                color: #3498db; 
                text-decoration: underline; 
                border: none; 
                background: none;
                font-size: 12px;
                text-align: left;
                padding: 0px;
            }
            QPushButton:hover {
                color: #2980b9;
            }
        """)
        self.btn_recuperar.setCursor(Qt.PointingHandCursor)
        layout_principal.addWidget(self.btn_recuperar)
        
        # Espaciado de separación sutil antes de las acciones finales
        layout_principal.addSpacing(10)
        
        # Caja de botones del sistema
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.boton_invitado = self.botones.addButton("Ingresar como Invitado", QDialogButtonBox.ActionRole)
        
        # Extracción y estilización manual de cada botón para asegurar consistencia visual perfecta
        btn_ok = self.botones.button(QDialogButtonBox.Ok)
        btn_cancel = self.botones.button(QDialogButtonBox.Cancel)
        
        estilo_base_botones = """
            QPushButton {
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
        """
        
        if btn_ok:
            btn_ok.setText("Iniciar Sesión")
            btn_ok.setCursor(Qt.PointingHandCursor)
            btn_ok.setStyleSheet(estilo_base_botones + """
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2c3e50;
                }
            """)
            
        if btn_cancel:
            btn_cancel.setText("Cancelar")
            btn_cancel.setCursor(Qt.PointingHandCursor)
            btn_cancel.setStyleSheet(estilo_base_botones + """
                QPushButton {
                    background-color: #ffffff;
                    color: #7f8c8d;
                    border: 1px solid #dcdde1;
                }
                QPushButton:hover {
                    background-color: #f1f2f6;
                    color: #57606f;
                }
            """)
            
        if self.boton_invitado:
            self.boton_invitado.setCursor(Qt.PointingHandCursor)
            self.boton_invitado.setStyleSheet(estilo_base_botones + """
                QPushButton {
                    background-color: #e1b12c;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #c49b22;
                }
            """)
            
        layout_principal.addWidget(self.botones)