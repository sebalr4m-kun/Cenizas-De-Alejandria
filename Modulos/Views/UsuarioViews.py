from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QTextEdit
)
from PySide6.QtCore import Qt, QTimer

class VentanaEmergenciaRecuperacion(QDialog):
    def __init__(self, palabras, padre=None):
        super().__init__(padre)
        self.setWindowTitle("SISTEMA DE RECUPERACIÓN DE EMERGENCIA")
        self.setFixedSize(480, 500)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        layout = QVBoxLayout(self)

        aviso = QLabel("⚠️ ATENCIÓN: GUARDE ESTAS PALABRAS EN UN LUGAR SEGURO ⚠️")
        aviso.setStyleSheet("color: #FF4444; font-weight: bold; font-size: 14px;")
        aviso.setWordWrap(True)
        layout.addWidget(aviso)

        desc = QLabel("Estas 12 palabras son el único método para recuperar su acceso si olvida la contraseña:")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.caja_texto = QTextEdit()
        self.caja_texto.setReadOnly(True)
        self.caja_texto.setText("\n".join([f"{i+1}. {p}" for i, p in enumerate(palabras)]))
        self.caja_texto.setStyleSheet("font-family: 'Consolas'; font-size: 12px; background-color: #f0f0f0;")
        layout.addWidget(self.caja_texto)

        self.btn_confirmar = QPushButton("Espere 10 segundos...")
        self.btn_confirmar.setEnabled(False)
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

    def closeEvent(self, event):
        if self.segundos_restantes > 0:
            event.ignore()
        else:
            super().closeEvent(event)


class VistaUsuario(QWidget):
    def __init__(self):
        super().__init__()
        self.tabla = QTableWidget()
        self.entrada_busqueda = QLineEdit()
        self.btn_modo_crear = QPushButton("Crear Nuevo")
        self.btn_modo_editar = QPushButton("Editar Existente")
        self.widget_contenido_formulario = QWidget()

        self.entrada_email = QLineEdit()
        self.entrada_nombre = QLineEdit()
        self.combo_tipo_cuenta = QComboBox()
        self.etiqueta_pass_actual = QLabel("Contraseña Actual")
        self.entrada_pass_actual = QLineEdit()
        self.btn_recuperar_pass = QPushButton("¿Olvidó su contraseña?")
        self.etiqueta_pass_nueva = QLabel("Nueva Contraseña")
        self.entrada_pass_nueva = QLineEdit()
        self.etiqueta_estado = QLabel("Estado")
        self.combo_estado_cuenta = QComboBox()
        self.btn_guardar = QPushButton("Guardar Cambios")

        # Configuración inicial de widgets
        self.entrada_pass_actual.setEchoMode(QLineEdit.Password)
        self.entrada_pass_nueva.setEchoMode(QLineEdit.Password)
        self.combo_estado_cuenta.addItems(["ACTIVA", "SUSPENDIDA", "ELIMINADA"])

    def construir_vista_listado(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Gestión de Usuarios"))
        self.entrada_busqueda.setPlaceholderText("Filtrar por nombre o email...")
        layout.addWidget(self.entrada_busqueda)

        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Email", "Tipo Cuenta", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabla)
        return widget

    def construir_vista_formulario(self):
        widget_principal = QWidget()
        layout_principal = QVBoxLayout(widget_principal)

        # Selector de modo
        layout_modo = QHBoxLayout()
        self.btn_modo_crear.setCheckable(True)
        self.btn_modo_editar.setCheckable(True)
        layout_modo.addWidget(self.btn_modo_crear)
        layout_modo.addWidget(self.btn_modo_editar)
        layout_principal.addLayout(layout_modo)

        # Contenido del formulario
        layout_contenido = QVBoxLayout(self.widget_contenido_formulario)
        layout_contenido.setContentsMargins(5, 5, 5, 5)

        layout_contenido.addWidget(QLabel("Email"))
        layout_contenido.addWidget(self.entrada_email)
        layout_contenido.addWidget(QLabel("Nombre Completo"))
        layout_contenido.addWidget(self.entrada_nombre)
        layout_contenido.addWidget(QLabel("Tipo de Cuenta"))
        layout_contenido.addWidget(self.combo_tipo_cuenta)

        layout_contenido.addWidget(self.etiqueta_pass_actual)
        layout_contenido.addWidget(self.entrada_pass_actual)
        layout_contenido.addWidget(self.btn_recuperar_pass)
        layout_contenido.addWidget(self.etiqueta_pass_nueva)
        layout_contenido.addWidget(self.entrada_pass_nueva)

        layout_contenido.addWidget(self.etiqueta_estado)
        layout_contenido.addWidget(self.combo_estado_cuenta)

        layout_contenido.addStretch()

        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.setMinimumHeight(40)
        layout_contenido.addWidget(self.btn_guardar)

        layout_principal.addWidget(self.widget_contenido_formulario)
        layout_principal.addStretch()
        return widget_principal