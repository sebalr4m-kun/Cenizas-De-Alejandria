from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer

class VentanaEmergenciaRecuperacion(QDialog):
    """
    Mantiene la seguridad de las palabras maestras con un timer obligatorio de 10s.
    Esta ventana es crítica para la creación de nuevos bibliotecarios.
    """
    def __init__(self, palabras, padre=None):
        super().__init__(padre)
        self.setWindowTitle("SISTEMA DE RECUPERACIÓN DE EMERGENCIA")
        self.setFixedSize(480, 500)
        self.setModal(True)
        # Bloquea el cierre accidental mediante la X
        self.setWindowFlags(Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        layout = QVBoxLayout(self)
        aviso = QLabel("⚠️ ATENCIÓN: GUARDE ESTAS PALABRAS EN UN LUGAR SEGURO ⚠️")
        aviso.setStyleSheet("color: #FF4444; font-weight: bold; font-size: 14px;")
        aviso.setWordWrap(True)
        layout.addWidget(aviso)

        self.caja_texto = QTextEdit()
        self.caja_texto.setReadOnly(True)
        # Formateo de las palabras para facilitar la lectura
        self.caja_texto.setText("\n".join([f"{i+1}. {p}" for i, p in enumerate(palabras)]))
        self.caja_texto.setStyleSheet("""
            font-family: 'Consolas'; 
            font-size: 13px; 
            background-color: #1e1e1e; 
            color: #00FF00; 
            padding: 10px;
        """)
        layout.addWidget(self.caja_texto)

        self.btn_confirmar = QPushButton("Espere 10 segundos...")
        self.btn_confirmar.setEnabled(False)
        self.btn_confirmar.setMinimumHeight(40)
        self.btn_confirmar.clicked.connect(self.accept)
        layout.addWidget(self.btn_confirmar)

        self.segundos_restantes = 10
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_timer)
        self.timer.start(1000)

    def actualizar_timer(self):
        self.segundos_restantes -= 1
        if self.segundos_restantes > 0:
            self.btn_confirmar.setText(f"Espere {self.segundos_restantes} segundos...")
        else:
            self.timer.stop()
            self.btn_confirmar.setText("¡Ya guardé mi código!")
            self.btn_confirmar.setEnabled(True)
            self.btn_confirmar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

class VistaUsuario(QWidget):
    def __init__(self):
        super().__init__()
        # Componentes de Listado
        self.tabla = QTableWidget()
        self.entrada_busqueda = QLineEdit()
        
        # Selectores de Modo
        self.btn_modo_crear = QPushButton("Crear Nuevo")
        self.btn_modo_editar = QPushButton("Editar Existente")
        
        # Contenedor del Formulario (se oculta/muestra dinámicamente)
        self.widget_contenido_formulario = QWidget()
        
        # Campos de entrada
        self.entrada_email = QLineEdit()
        self.entrada_nombre = QLineEdit()
        self.combo_tipo_cuenta = QComboBox()
        
        # Seguridad y Contraseñas
        self.etiqueta_pass_actual = QLabel("Contraseña Actual")
        self.entrada_pass_actual = QLineEdit()
        self.btn_recuperar_pass = QPushButton("¿Olvidó su contraseña?")
        
        self.etiqueta_pass_nueva = QLabel("Contraseña (Requerida para Bibliotecarios)")
        self.entrada_pass_nueva = QLineEdit()
        
        # Estado de cuenta
        self.etiqueta_estado = QLabel("Estado de Cuenta")
        self.combo_estado_cuenta = QComboBox()
        
        # Botón de acción principal
        self.btn_guardar = QPushButton("Guardar Cambios")

        # Configuración inicial de campos
        self.entrada_pass_actual.setEchoMode(QLineEdit.Password)
        self.entrada_pass_nueva.setEchoMode(QLineEdit.Password)
        self.combo_estado_cuenta.addItems(["ACTIVA", "SUSPENDIDA", "ELIMINADA"])

    def construir_vista_listado(self):
        """Genera el widget de la tabla y búsqueda (Pila Central)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        titulo = QLabel("Gestión de Usuarios")
        titulo.setProperty("isTitle", True) # Para estilos QSS
        layout.addWidget(titulo)

        self.entrada_busqueda.setPlaceholderText("🔍 Filtrar por nombre o email...")
        layout.addWidget(self.entrada_busqueda)

        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Email", "Tipo Cuenta", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        layout.addWidget(self.tabla)
        
        return widget

    def construir_vista_formulario(self):
        """Genera el widget del panel lateral (Pila Derecha)"""
        widget_principal = QWidget()
        layout_principal = QVBoxLayout(widget_principal)

        # Botones de alternancia de modo superior
        layout_modo = QHBoxLayout()
        self.btn_modo_crear.setCheckable(True)
        self.btn_modo_editar.setCheckable(True)
        layout_modo.addWidget(self.btn_modo_crear)
        layout_modo.addWidget(self.btn_modo_editar)
        layout_principal.addLayout(layout_modo)

        # Contenedor dinámico de campos
        layout_contenido = QVBoxLayout(self.widget_contenido_formulario)
        layout_contenido.setContentsMargins(5, 5, 5, 5)

        layout_contenido.addWidget(QLabel("Email (Formato @gmail.com)"))
        layout_contenido.addWidget(self.entrada_email)
        
        layout_contenido.addWidget(QLabel("Nombre Completo"))
        layout_contenido.addWidget(self.entrada_nombre)
        
        layout_contenido.addWidget(QLabel("Tipo de Cuenta (Rol)"))
        layout_contenido.addWidget(self.combo_tipo_cuenta)

        # Sección de Contraseña Actual (Solo aparece en edición de Bibliotecarios)
        layout_contenido.addWidget(self.etiqueta_pass_actual)
        layout_contenido.addWidget(self.entrada_pass_actual)
        layout_contenido.addWidget(self.btn_recuperar_pass)
        
        # Sección de Contraseña Nueva
        layout_contenido.addWidget(self.etiqueta_pass_nueva)
        layout_contenido.addWidget(self.entrada_pass_nueva)

        # Sección de Estado
        layout_contenido.addWidget(self.etiqueta_estado)
        layout_contenido.addWidget(self.combo_estado_cuenta)

        layout_contenido.addStretch()

        # Botón Final
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.setMinimumHeight(40)
        layout_contenido.addWidget(self.btn_guardar)

        layout_principal.addWidget(self.widget_contenido_formulario)
        layout_principal.addStretch()

        # Inicialmente el formulario está oculto hasta que se elija un modo
        self.widget_contenido_formulario.hide()
        
        return widget_principal

    def limpiar_interfaz(self):
        """Restablece todos los campos y esconde el formulario (Protocolo Anti-Fantasmas)[cite: 1, 3]"""
        self.entrada_email.clear()
        self.entrada_nombre.clear()
        self.entrada_pass_actual.clear()
        self.entrada_pass_nueva.clear()
        
        if self.combo_tipo_cuenta.count() > 0:
            self.combo_tipo_cuenta.setCurrentIndex(0)
        self.combo_estado_cuenta.setCurrentIndex(0)
        
        # Limpiar estilos de validación que pudieron quedar
        self.entrada_pass_actual.setStyleSheet("")
        self.entrada_email.setStyleSheet("")
        
        # Desmarcar botones de modo
        self.btn_modo_crear.setChecked(False)
        self.btn_modo_editar.setChecked(False)
        
        # Esconder el formulario
        self.widget_contenido_formulario.hide()