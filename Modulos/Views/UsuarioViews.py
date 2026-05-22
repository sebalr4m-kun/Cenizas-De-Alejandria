from PySide6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,

    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,

    QDialog, QTextEdit, QMessageBox

)

from PySide6.QtCore import Qt, QTimer, Slot



class VentanaEmergenciaRecuperacion(QDialog):

    """

    Mantiene la seguridad de las palabras maestras con un timer obligatorio de 10s.

    Esta ventana es de solo lectura y se limita a mostrar de forma segura las 12 palabras.

    """

    def __init__(self, palabras, padre=None):

        super().__init__(padre)

        self.setWindowTitle("SISTEMA DE RECUPERACIÓN DE EMERGENCIA")

        self.setFixedSize(480, 500)

        self.setModal(True)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint)



        layout = QVBoxLayout(self)

       

        aviso = QLabel("⚠️ ATENCIÓN: GUARDE ESTAS PALABRAS EN UN LUGAR SEGURO ⚠️")

        aviso.setStyleSheet("color: #FF4444; font-weight: bold; font-size: 14px;")

        aviso.setWordWrap(True)

        layout.addWidget(aviso)



        self.caja_texto = QTextEdit()

        self.caja_texto.setReadOnly(True)

        self.caja_texto.setText("\n".join([f"{i+1}. {p}" for i, p in enumerate(palabras)]))

        self.caja_texto.setStyleSheet("""

            font-family: 'Consolas'; font-size: 13px;

            background-color: #1e1e1e; color: #00FF00; padding: 10px;

        """)

        layout.addWidget(self.caja_texto)



        self.btn_confirmar = QPushButton("Espere 10 segundos...")

        self.btn_confirmar.setEnabled(False)

        self.btn_confirmar.setMinimumHeight(40)

        self.btn_confirmar.clicked.connect(self.accept)

        layout.addWidget(self.btn_confirmar)



        self.timer = QTimer(self)

        self.timer.timeout.connect(self.actualizar_timer)

        self.timer.start(1000)

        self.segundos = 10



    def actualizar_timer(self):

        self.segundos -= 1

        if self.segundos > 0:

            self.btn_confirmar.setText(f"Espere {self.segundos} segundos...")

        else:

            self.timer.stop()

            self.btn_confirmar.setText("CONFIRMAR Y FINALIZAR")

            self.btn_confirmar.setEnabled(True)

            self.btn_confirmar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")



class VistaUsuario(QWidget):

    def __init__(self):

        super().__init__()

        # Componentes base de la UI

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

       

        self.etiqueta_pass_nueva = QLabel("Contraseña (Requerida para Bibliotecarios)")

        self.entrada_pass_nueva = QLineEdit()

       

        # Nuevo campo de confirmación solicitado

        self.etiqueta_pass_confirmar = QLabel("Confirmar Contraseña")

        self.entrada_pass_confirmar = QLineEdit()

       

        self.etiqueta_estado = QLabel("Estado de Cuenta")

        self.combo_estado_cuenta = QComboBox()

        self.btn_guardar = QPushButton("Guardar Cambios")



        # Ajustes de seguridad visual

        self.entrada_pass_actual.setEchoMode(QLineEdit.Password)

        self.entrada_pass_nueva.setEchoMode(QLineEdit.Password)

        self.entrada_pass_confirmar.setEchoMode(QLineEdit.Password)

        self.combo_estado_cuenta.addItems(["ACTIVA", "SUSPENDIDA", "ELIMINADA"])

       

        self.parent_controller = None

        self.init_layout()

       

        # Conexión dinámica para alternar la visibilidad según el tipo de cuenta

        self.combo_tipo_cuenta.currentTextChanged.connect(self.ajustar_visibilidad_campos_seguridad)



    def init_layout(self):

        layout_principal = QHBoxLayout(self)

       

        self.widget_listado = self.construir_vista_listado()

        layout_principal.addWidget(self.widget_listado, 2)

       

        self.widget_formulario = self.construir_vista_formulario()

        layout_principal.addWidget(self.widget_formulario, 1)



    def construir_vista_listado(self):

        widget = QWidget()

        layout = QVBoxLayout(widget)

       

        titulo = QLabel("Panel de Control de Usuarios")

        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db; margin-bottom: 10px;")

        layout.addWidget(titulo)



        self.entrada_busqueda.setPlaceholderText("🔍 Filtrar registros por nombre o email...")

        self.entrada_busqueda.setMinimumHeight(30)

        layout.addWidget(self.entrada_busqueda)



        self.tabla.setColumnCount(4)

        self.tabla.setHorizontalHeaderLabels(["Nombre", "Email", "Tipo Cuenta", "Estado"])

        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)

        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)

        self.tabla.setAlternatingRowColors(True)

        self.tabla.setStyleSheet("QTableWidget { gridline-color: #dcdde1; }")

        layout.addWidget(self.tabla)

       

        return widget



    def construir_vista_formulario(self):

        widget_principal = QWidget()

        layout_principal = QVBoxLayout(widget_principal)



        layout_modo = QHBoxLayout()

        self.btn_modo_crear.setCheckable(True)

        self.btn_modo_editar.setCheckable(True)

        self.btn_modo_crear.setMinimumHeight(35)

        self.btn_modo_editar.setMinimumHeight(35)

        layout_modo.addWidget(self.btn_modo_crear)

        layout_modo.addWidget(self.btn_modo_editar)

        layout_principal.addLayout(layout_modo)



        layout_contenido = QVBoxLayout(self.widget_contenido_formulario)

        layout_contenido.setContentsMargins(10, 10, 10, 10)

        layout_contenido.setSpacing(8)



        layout_contenido.addWidget(QLabel("Email Institucional"))

        layout_contenido.addWidget(self.entrada_email)

       

        layout_contenido.addWidget(QLabel("Nombre Completo"))

        layout_contenido.addWidget(self.entrada_nombre)

       

        layout_contenido.addWidget(QLabel("Tipo de Cuenta (Rol)"))

        layout_contenido.addWidget(self.combo_tipo_cuenta)



        layout_contenido.addWidget(self.etiqueta_pass_actual)

        layout_contenido.addWidget(self.entrada_pass_actual)

        layout_contenido.addWidget(self.btn_recuperar_pass)

       

        layout_contenido.addWidget(self.etiqueta_pass_nueva)

        layout_contenido.addWidget(self.entrada_pass_nueva)

       

        # Inserción de los componentes de confirmación en el layout

        layout_contenido.addWidget(self.etiqueta_pass_confirmar)

        layout_contenido.addWidget(self.entrada_pass_confirmar)



        layout_contenido.addWidget(self.etiqueta_estado)

        layout_contenido.addWidget(self.combo_estado_cuenta)



        layout_contenido.addStretch()



        self.btn_guardar.setMinimumHeight(45)

        self.btn_guardar.setStyleSheet("""

            QPushButton { font-weight: bold; font-size: 14px; background-color: #34495e; color: white; border-radius: 5px; }

            QPushButton:hover { background-color: #2c3e50; }

        """)

        layout_contenido.addWidget(self.btn_guardar)



        layout_principal.addWidget(self.widget_contenido_formulario)

        layout_principal.addStretch()



        self.widget_contenido_formulario.hide()

        return widget_principal



    def ajustar_visibilidad_campos_seguridad(self, rol):

        """Muestra u oculta las opciones de contraseña según el tipo de cuenta seleccionado."""

        es_bibliotecario = (rol == "Bibliotecario")

        self.etiqueta_pass_nueva.setVisible(es_bibliotecario)

        self.entrada_pass_nueva.setVisible(es_bibliotecario)

        self.etiqueta_pass_confirmar.setVisible(es_bibliotecario)

        self.entrada_pass_confirmar.setVisible(es_bibliotecario)



    def verificar_coincidencia_contrasenas(self) -> bool:

        """Valida que las contraseñas coincidan si el usuario es de tipo Bibliotecario."""

        if self.combo_tipo_cuenta.currentText() == "Bibliotecario":

            pass_nueva = self.entrada_pass_nueva.text().strip()

            pass_conf = self.entrada_pass_confirmar.text().strip()

            if pass_nueva != pass_conf:

                QMessageBox.warning(self, "Error de Validación", "Las contraseñas ingresadas no coinciden. Por favor verifíquelas.")

                return False

        return True



    @Slot(str, str, str, object)

    def mostrar_notificacion(self, tipo, titulo, mensaje, datos_extra=None):

        """Gestor centralizado de notificaciones y diálogos externos de seguridad."""

        if tipo == 'info':

            QMessageBox.information(self, titulo, mensaje)

        elif tipo == 'warn':

            QMessageBox.warning(self, titulo, mensaje)

        elif tipo == 'crit':

            QMessageBox.critical(self, titulo, mensaje)

        elif tipo == 'success':

            QMessageBox.information(self, titulo, mensaje)

       

        elif tipo == 'recovery_trigger':

            from Modulos.PasswordRecover import ValidadorRecuperacion

            dialogo = ValidadorRecuperacion(self)

            dialogo.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)

            dialogo.activateWindow()

            dialogo.raise_()

           

            exito = (dialogo.exec() == QDialog.Accepted)

            email_recuperado = None

            if hasattr(dialogo, 'entrada_email'):

                email_recuperado = dialogo.entrada_email.text().strip()

           

            if self.parent_controller:

                self.parent_controller.validar_identidad_finalizada(exito, email_recuperado)



        elif tipo == 'validador_cuenta':

            from Modulos.AccountValidator import ValidadorCuenta

            email = mensaje

            pals = datos_extra

           

            validador = ValidadorCuenta(pals, self)

            validador.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)

            validador.activateWindow()

            validador.raise_()

           

            if validador.exec() == QDialog.Accepted:

                if self.parent_controller:

                    self.parent_controller.finalizar_operacion(f"Bibliotecario '{email}' validado.", pals)

            else:

                if self.parent_controller:

                    self.parent_controller.abortar_creacion(email)



        elif tipo == 'emergencia':

            if datos_extra:

                dialogo_pals = VentanaEmergenciaRecuperacion(datos_extra, self)

                dialogo_pals.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)

                dialogo_pals.activateWindow()

                dialogo_pals.raise_()

                dialogo_pals.exec()



    def limpiar_interfaz(self):

        """Restablece el estado visual de todos los campos de interacción."""

        self.entrada_email.clear()

        self.entrada_nombre.clear()

        self.entrada_pass_actual.clear()

        self.entrada_pass_nueva.clear()

        self.entrada_pass_confirmar.clear()

       

        self.entrada_pass_actual.setStyleSheet("")

        self.entrada_email.setStyleSheet("")

        self.btn_guardar.setEnabled(True)

       

        if self.combo_tipo_cuenta.count() > 0:

            self.combo_tipo_cuenta.setCurrentIndex(0)

        self.combo_estado_cuenta.setCurrentIndex(0)

       

        self.btn_modo_crear.setChecked(False)

        self.btn_modo_editar.setChecked(False)

        self.widget_contenido_formulario.hide()