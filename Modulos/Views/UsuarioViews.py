from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Slot, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
import re

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


class TablaUsuariosFiltro(QTableWidget):
    """
    Tabla personalizada que intercepta la visibilidad de las filas
    para garantizar que los usuarios con estado INACTIVA o SUSPENDIDA 
    permanezcan ocultos, incluso si el controlador intenta mostrarlos.
    """
    def setRowHidden(self, row, hide):
        item_estado = self.item(row, 3) # La columna 3 es "Estado"
        if item_estado and item_estado.text().strip().upper() in ("INACTIVA", "SUSPENDIDA"):
            super().setRowHidden(row, True)
        else:
            super().setRowHidden(row, hide)

    def setItem(self, row, column, item):
        super().setItem(row, column, item)
        # Al setear la columna de Estado, verificamos si debe ocultarse al instante
        if column == 3:
            if item.text().strip().upper() in ("INACTIVA", "SUSPENDIDA"):
                super().setRowHidden(row, True)


class VistaUsuario(QWidget):
    def __init__(self):
        super().__init__()
        # Componentes base de la UI (Usamos la tabla personalizada)
        self.tabla = TablaUsuariosFiltro()
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
        
        # Modificación de texto para el enfoque de cuentas ADMItidas
        self.etiqueta_pass_nueva = QLabel("Contraseña (Requerida para cuentas ADMItidas)")
        self.entrada_pass_nueva = QLineEdit()
        
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
        
        # --- ATRIBUTOS DE CONTROL DE ESTADO DE SEGURIDAD ---
        self.id_rol_original = None
        self._recovery_exitoso = False
        
        # Filtro estricto de entrada para evitar caracteres especiales inválidos en el nombre
        regex_nombre = QRegularExpression(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]*$")
        self.entrada_nombre.setValidator(QRegularExpressionValidator(regex_nombre, self))
        
        # Filtro estricto para correos: solo letras Unicode (\p{L}), números (\d o 0-9), arroba y punto.
        regex_email = QRegularExpression(r"^[\p{L}0-9@.]*$")
        self.entrada_email.setValidator(QRegularExpressionValidator(regex_email, self))

        # Filtro estricto para contraseñas: denegar espacios
        regex_pass = QRegularExpression(r"^[^\s]*$")
        self.entrada_pass_nueva.setValidator(QRegularExpressionValidator(regex_pass, self))
        self.entrada_pass_confirmar.setValidator(QRegularExpressionValidator(regex_pass, self))
        
        # Interceptar asignaciones programáticas del controlador en el ComboBox
        self._orig_setCurrentIndex = self.combo_tipo_cuenta.setCurrentIndex
        self.combo_tipo_cuenta.setCurrentIndex = self._custom_setCurrentIndex
        
        self.init_layout()
        
        # Conexiones dinámicas de eventos
        self.combo_tipo_cuenta.currentIndexChanged.connect(self._on_combo_index_changed)
        self.btn_modo_crear.clicked.connect(self._on_modo_cambiado)
        self.btn_modo_editar.clicked.connect(self._on_modo_cambiado)
        self.entrada_email.textChanged.connect(self._on_email_cambiado)
        self.btn_recuperar_pass.clicked.connect(self._on_recuperar_clicked)
        
        # Sincronización por doble click idéntica a Insumos
        self.tabla.cellDoubleClicked.connect(self._on_fila_doble_click)

    def init_layout(self):
        layout_principal = QHBoxLayout(self)
        
        self.widget_listado = self.construir_vista_listado()
        layout_principal.addWidget(self.widget_listado, 2)
        
        self.widget_formulario = self.construir_vista_formulario()
        layout_principal.addWidget(self.widget_formulario, 1)

    def construir_vista_listado(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Se homologa la estilización con el diseño global de Insumos usando la propiedad CSS del proyecto
        titulo = QLabel("Panel de Control de Usuarios")
        titulo.setProperty("isTitle", True)
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

    def _custom_setCurrentIndex(self, index):
        """Captura el rol de base de datos indexado (usando Data) antes de modificaciones manuales."""
        if self.btn_modo_editar.isChecked() and self.id_rol_original is None and index >= 0:
            self.id_rol_original = self.combo_tipo_cuenta.itemData(index)
        self._orig_setCurrentIndex(index)
        self.ajustar_visibilidad_campos_seguridad()

    def _on_combo_index_changed(self, index):
        self.ajustar_visibilidad_campos_seguridad()

    def _on_modo_cambiado(self):
        """Resetea el rastreo ante cambios de panel operativo y limpia el formulario."""
        if self.parent_controller:
            self.parent_controller.limpiar_formulario()
            
        if self.btn_modo_crear.isChecked():
            self.id_rol_original = None
            self._recovery_exitoso = False
            self.widget_contenido_formulario.show()
            self.btn_modo_editar.setChecked(False)
        elif self.btn_modo_editar.isChecked():
            self.btn_modo_crear.setChecked(False)
            self.widget_contenido_formulario.show()
        else:
            self.widget_contenido_formulario.hide()
            
        self.ajustar_visibilidad_campos_seguridad()

    def _on_email_cambiado(self):
        """Restaura los campos y la validación si se modifica el correo electrónico aunque sea por una letra."""
        self._recovery_exitoso = False
        self.entrada_pass_actual.clear()
        self.entrada_pass_nueva.clear()
        self.entrada_pass_confirmar.clear()
        self.ajustar_visibilidad_campos_seguridad()

    def _on_recuperar_clicked(self):
        """Triggerea la ventana de recuperación de contraseña."""
        self.mostrar_notificacion('recovery_trigger', 'Recuperación de Contraseña', '')

    def _on_fila_doble_click(self, fila, columna):
        """Mapea los datos de la fila de la tabla directamente al formulario de edición."""
        nombre_item = self.tabla.item(fila, 0)
        email_item = self.tabla.item(fila, 1)
        tipo_item = self.tabla.item(fila, 2)
        estado_item = self.tabla.item(fila, 3)

        if not email_item or not nombre_item:
            return

        # 1. Activamos el estado visual y lógico del formulario en modo Edición
        if self.parent_controller:
            self.parent_controller.establecer_modo_editar()
        else:
            self.btn_modo_crear.setChecked(False)
            self.btn_modo_editar.setChecked(True)
            self.widget_contenido_formulario.show()

        # 2. Limpieza preventiva de campos críticos (Seguridad de contraseñas)
        self.entrada_pass_actual.clear()
        self.entrada_pass_nueva.clear()
        self.entrada_pass_confirmar.clear()
        self._recovery_exitoso = False

        # 3. Inyección del dato principal (Email) e información descriptiva
        self.entrada_email.setText(email_item.text())
        self.entrada_email.setReadOnly(False) # ¡Libertad total de edición!
        self.entrada_nombre.setText(nombre_item.text())
        
        # 4. Ajuste de estado y combobox delegando la carga total al Controlador 
        # (Esto dispara al_terminar_edicion_email() el cual setea los flags originales correctos)
        if self.parent_controller:
            self.parent_controller.al_terminar_edicion_email()

    def ajustar_visibilidad_campos_seguridad(self):
        """Muestra u oculta las opciones de contraseña mitigando vulnerabilidades de escalado de privilegios de forma dinámica."""
        if not self.parent_controller:
            return
            
        es_admitido, fue_admitido, id_actual, id_orig = self.parent_controller._obtener_estados_admision()

        # ESCENARIO 1: Modo Creación de Usuario
        if self.btn_modo_crear.isChecked():
            self.id_rol_original = None
            
            self.etiqueta_pass_nueva.setVisible(es_admitido)
            self.entrada_pass_nueva.setVisible(es_admitido)
            self.etiqueta_pass_confirmar.setVisible(es_admitido)
            self.entrada_pass_confirmar.setVisible(es_admitido)
            
            self.etiqueta_pass_actual.hide()
            self.entrada_pass_actual.hide()
            self.btn_recuperar_pass.hide()
            
        # ESCENARIO 2: Modo Edición de Usuario Existente
        elif self.btn_modo_editar.isChecked():
            if self.id_rol_original is None and id_actual is not None:
                self.id_rol_original = id_actual
                es_admitido, fue_admitido, id_actual, id_orig = self.parent_controller._obtener_estados_admision()

            # Intervención al controlador: Forzar la generación de palabras si ascendemos a cuenta ADMItida
            if not fue_admitido and es_admitido:
                self.parent_controller.es_upgrade_a_admitido = True
            elif not fue_admitido and not es_admitido:
                self.parent_controller.es_upgrade_a_admitido = False

            # SUB-CASO A: El usuario ya era ADMItido originalmente
            if fue_admitido:
                if self._recovery_exitoso:
                    self.etiqueta_pass_actual.hide()
                    self.entrada_pass_actual.hide()
                    self.btn_recuperar_pass.hide()
                else:
                    self.etiqueta_pass_actual.show()
                    self.entrada_pass_actual.show()
                    self.btn_recuperar_pass.show()
                
                if es_admitido:
                    # Mantiene privilegios, los campos de nueva contraseña son opcionales
                    self.etiqueta_pass_nueva.show()
                    self.entrada_pass_nueva.show()
                    self.etiqueta_pass_confirmar.show()
                    self.entrada_pass_confirmar.show()
                else:
                    # Downgrade: Pierde privilegios. No muestra campos nuevos, solo exige la clave actual
                    self.etiqueta_pass_nueva.hide()
                    self.entrada_pass_nueva.hide()
                    self.etiqueta_pass_confirmar.hide()
                    self.entrada_pass_confirmar.hide()
                    
            # SUB-CASO B: El usuario original NO era ADMItido (Lector, etc.)
            else:
                self.etiqueta_pass_actual.hide()
                self.entrada_pass_actual.hide()
                self.btn_recuperar_pass.hide()
                
                # Si se le está ascendiendo a ADMItido, debe fijar su contraseña obligatoria
                if es_admitido:
                    self.etiqueta_pass_nueva.show()
                    self.entrada_pass_nueva.show()
                    self.etiqueta_pass_confirmar.show()
                    self.entrada_pass_confirmar.show()
                else:
                    self.etiqueta_pass_nueva.hide()
                    self.entrada_pass_nueva.hide()
                    self.etiqueta_pass_confirmar.hide()
                    self.entrada_pass_confirmar.hide()
        else:
            self.etiqueta_pass_actual.hide()
            self.entrada_pass_actual.hide()
            self.btn_recuperar_pass.hide()
            self.etiqueta_pass_nueva.hide()
            self.entrada_pass_nueva.hide()
            self.etiqueta_pass_confirmar.hide()
            self.entrada_pass_confirmar.hide()

    def verificar_coincidencia_contrasenas(self) -> bool:
        """Valida que las reglas de contraseñas y restricciones se cumplan estrictamente de forma dinámica."""
        nombre = self.entrada_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error de Validación", "El nombre completo no puede estar vacío.")
            return False
            
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$", nombre):
            QMessageBox.warning(self, "Error de Validación", "El nombre de usuario contiene caracteres no permitidos. Solo se admiten letras y espacios.")
            return False

        if not self.parent_controller:
            return True

        es_admitido, fue_admitido, _, _ = self.parent_controller._obtener_estados_admision()
        
        # Helper para forzar caracteres especiales excluyendo alfanuméricos y letras con tildes comunes
        def es_compleja(pwd):
            return bool(re.search(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]", pwd))
        
        if self.btn_modo_crear.isChecked():
            if es_admitido:
                pass_nueva = self.entrada_pass_nueva.text().strip()
                pass_conf = self.entrada_pass_confirmar.text().strip()
                if not pass_nueva:
                    QMessageBox.warning(self, "Error de Validación", "La nueva contraseña es requerida para cuentas ADMItidas.")
                    return False
                if not es_compleja(pass_nueva):
                    QMessageBox.warning(self, "Error de Seguridad", "La contraseña debe contener obligatoriamente al menos un carácter especial (símbolo).")
                    return False
                if pass_nueva != pass_conf:
                    QMessageBox.warning(self, "Error de Validación", "Las contraseñas ingresadas no coinciden. Por favor verifíquelas.")
                    return False
                    
        elif self.btn_modo_editar.isChecked():
            if fue_admitido:
                # Requiere rellenar la clave actual siempre, a menos que usó Recovery exitosamente
                if not self._recovery_exitoso:
                    pass_act = self.entrada_pass_actual.text().strip()
                    if not pass_act:
                        QMessageBox.warning(self, "Error de Validación", "Debe ingresar su contraseña actual para autorizar cambios en esta cuenta.")
                        return False
                
                # Si mantiene el rol ADMItido, permitimos cambio opcional
                if es_admitido:
                    pass_nueva = self.entrada_pass_nueva.text().strip()
                    pass_conf = self.entrada_pass_confirmar.text().strip()
                    if pass_nueva or pass_conf:
                        if not es_compleja(pass_nueva):
                            QMessageBox.warning(self, "Error de Seguridad", "La nueva contraseña debe contener obligatoriamente al menos un carácter especial (símbolo).")
                            return False
                        if pass_nueva != pass_conf:
                            QMessageBox.warning(self, "Error de Validación", "Las contraseñas nuevas no coinciden.")
                            return False
                
            # Si pasa de NO ADMItido a ADMItido (Ascenso)
            elif not fue_admitido and es_admitido:
                pass_nueva = self.entrada_pass_nueva.text().strip()
                pass_conf = self.entrada_pass_confirmar.text().strip()
                if not pass_nueva:
                    QMessageBox.warning(self, "Error de Validación", "La nueva contraseña es requerida para el alta como cuenta ADMItida.")
                    return False
                if not es_compleja(pass_nueva):
                    QMessageBox.warning(self, "Error de Seguridad", "La contraseña debe contener obligatoriamente al menos un carácter especial (símbolo).")
                    return False
                if pass_nueva != pass_conf:
                    QMessageBox.warning(self, "Error de Validación", "Las contraseñas ingresadas no coinciden. Por favor verifíquelas.")
                    return False
                    
        return True

    @Slot(str, str, str, object)
    def mostrar_notificacion(self, tipo, titulo, mensaje, datos_extra=None):
        """Gestor centralizado de notificaciones y diálogos externos de seguridad."""
        # Prevención estricta contra TypeError "argument 1 has unexpected type" de PySide6
        t_str = str(titulo) if titulo is not None else "Notificación"
        m_str = str(mensaje) if mensaje is not None else ""

        if tipo == 'info':
            QMessageBox.information(self, t_str, m_str)
        elif tipo == 'warn':
            QMessageBox.warning(self, t_str, m_str)
        elif tipo == 'crit':
            QMessageBox.critical(self, t_str, m_str)
        elif tipo == 'success':
            QMessageBox.information(self, t_str, m_str)
        
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
            
            if exito:
                self._recovery_exitoso = True
                self.ajustar_visibilidad_campos_seguridad()
                
            if self.parent_controller:
                self.parent_controller.validar_identidad_finalizada(exito, email_recuperado)

        elif tipo == 'validador_cuenta':
            from Modulos.AccountValidator import ValidadorCuenta
            email = m_str
            pals = datos_extra
            
            # Se inyecta la variable email directamente para coincidir con la firma nativa de la clase
            validador = ValidadorCuenta(pals, email, self)
            validador.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
            validador.activateWindow()
            validador.raise_()
            
            if validador.exec() == QDialog.Accepted:
                if self.parent_controller:
                    self.parent_controller.finalizar_operacion(f"Cuenta ADMItida '{email}' validada.", pals)
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
        """Restablece el estado visual de todos los campos de interacción limpiando referencias de persistencia."""
        self.id_rol_original = None
        self._recovery_exitoso = False
        
        self.entrada_email.clear()
        self.entrada_email.setReadOnly(False) # Mantenemos el reseteo por seguridad al limpiar
        self.entrada_nombre.clear()
        self.entrada_pass_actual.clear()
        self.entrada_pass_nueva.clear()
        self.entrada_pass_confirmar.clear()
        
        self.entrada_pass_actual.setStyleSheet("")
        self.entrada_email.setStyleSheet("")
        self.btn_guardar.setEnabled(True)
        
        if self.combo_tipo_cuenta.count() > 0:
            self._orig_setCurrentIndex(0)
        self.combo_estado_cuenta.setCurrentIndex(0)
        
        self.btn_modo_crear.setChecked(False)
        self.btn_modo_editar.setChecked(False)
        self.widget_contenido_formulario.hide()
        self.ajustar_visibilidad_campos_seguridad()