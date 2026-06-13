from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QCheckBox, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

# --- CLASE DE ESTILO PARA INTERRUPTORES (TOGGLE SWITCHES) ---
ESTILO_SWITCH = """
    QCheckBox::indicator {
        width: 40px;
        height: 20px;
        border-radius: 10px;
        border: 2px solid #bdc3c7;
        background-color: #ecf0f1;
    }
    QCheckBox::indicator:checked {
        background-color: #3498db;
        border: 2px solid #2980b9;
    }
    QCheckBox::indicator:checked:disabled {
        background-color: #7f8c8d; /**/
        border: 2px solid #576574;
    }
    QCheckBox::indicator:disabled {
        background-color: #ecf0f1;
        border: 2px solid #dcdde1;
    }
"""

class VistaTablaParametro(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        titulo = QLabel("Panel de Parámetros")
        titulo.setProperty("isTitle", True)
        layout.addWidget(titulo) 
        
        self.entrada_busqueda = QLineEdit()
        self.entrada_busqueda.setPlaceholderText("🔍 Filtrar por Nombre, Rubro o Estado...")
        self.entrada_busqueda.setMinimumHeight(30)
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla_global)
        layout.addWidget(self.entrada_busqueda)
        
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Todos", "Tipo Usuario", "Tipo Insumo", "Autor", "Editorial", "Categoría", "Género"])
        self.combo_filtro.hide() 
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Rubro", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: #dcdde1; }")
        
        self.tabla.itemDoubleClicked.connect(self.solicitar_edicion)
        layout.addWidget(self.tabla)

    def filtrar_tabla_global(self, texto):
        texto = texto.lower()
        for i in range(self.tabla.rowCount()):
            coincidencia = False
            for j in range(self.tabla.columnCount()):
                item = self.tabla.item(i, j)
                if item and texto in item.text().lower():
                    coincidencia = True
                    break
            self.tabla.setRowHidden(i, not coincidencia)

    def solicitar_edicion(self, item):
        fila = item.row()
        nombre = self.tabla.item(fila, 0).text()
        rubro = self.tabla.item(fila, 1).text()
        estado = self.tabla.item(fila, 2).text()
        
        if self.ctrl.widget_formulario:
            f = self.ctrl.widget_formulario
            f.limpiar_campos_valores() # Reset previo por seguridad
            
            f.combo_rubro.blockSignals(True)
            f.combo_rubro.setCurrentText(rubro)
            f.combo_rubro.blockSignals(False)
            
            f.entrada_nombre.setText(nombre)
            f.combo_estado.setCurrentText(estado)
            
            self.ctrl.establecer_editar()
            f.evaluar_visibilidad_permisos()


class FormularioParametro(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        self._estado_original = None  # Almacena el estado inalterado para comparar
        
        layout_principal = QVBoxLayout(self)
        
        # Contenedor de Botones de Modo
        contenedor_modos = QFrame()
        layout_modo = QHBoxLayout(contenedor_modos)
        
        self.btn_crear = QPushButton("Crear Nuevo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setMinimumHeight(35)
        
        self.btn_editar = QPushButton("Editar Existente")
        self.btn_editar.setCheckable(True)
        self.btn_editar.setMinimumHeight(35)
        
        layout_modo.addWidget(self.btn_crear)
        layout_modo.addWidget(self.btn_editar)
        layout_principal.addWidget(contenedor_modos)

        # ==================== CONTENEDOR PRINCIPAL ====================
        self.widget_contenido = QWidget(self)
        self.layout_contenido = QVBoxLayout(self.widget_contenido)
        self.layout_contenido.setContentsMargins(10, 10, 10, 10)
        self.layout_contenido.setSpacing(8)
        
        self.layout_contenido.addWidget(QLabel("Rubro del Parámetro"))
        self.combo_rubro = QComboBox()
        self.combo_rubro.addItems(["Tipo Usuario", "Tipo Insumo", "Autor", "Editorial", "Categoría", "Género"]) 
        self.combo_rubro.currentTextChanged.connect(self.evaluar_visibilidad_permisos)
        self.combo_rubro.currentTextChanged.connect(self.verificar_cambios)
        self.layout_contenido.addWidget(self.combo_rubro)
        
        self.layout_contenido.addWidget(QLabel("Nombre Identificativo"))
        self.entrada_nombre = QLineEdit()
        self.entrada_nombre.textChanged.connect(self.verificar_cambios)
        self.layout_contenido.addWidget(self.entrada_nombre)
        
        self.etiqueta_estado = QLabel("Estado")
        self.layout_contenido.addWidget(self.etiqueta_estado)
        
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["ACTIVO", "INACTIVO", "ELIMINAR"]) 
        self.combo_estado.currentTextChanged.connect(self.verificar_cambios)
        self.layout_contenido.addWidget(self.combo_estado)
        
        # ==================== CONTENEDOR RBAC (TIPO USUARIO) ====================
        self.widget_rbac = QWidget()
        self.layout_rbac = QVBoxLayout(self.widget_rbac)
        self.layout_rbac.setContentsMargins(0, 10, 0, 0)
        
        layout_admision = QHBoxLayout()
        self.lbl_admision = QLabel("ADMItido (Acceso al Sistema)")
        self.lbl_admision.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.switch_admitido = QCheckBox()
        self.switch_admitido.setStyleSheet(ESTILO_SWITCH)
        self.switch_admitido.setToolTip("Permite a este tipo de usuario tener una contraseña para ingresar")
        self.switch_admitido.stateChanged.connect(self.evaluar_switches_modulos)
        self.switch_admitido.stateChanged.connect(self.verificar_cambios)
        layout_admision.addWidget(self.lbl_admision)
        layout_admision.addWidget(self.switch_admitido)
        layout_admision.addStretch()
        self.layout_rbac.addLayout(layout_admision)
        
        self.scroll_modulos = QScrollArea()
        self.scroll_modulos.setWidgetResizable(True) 
        self.scroll_modulos.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.scroll_modulos.setFrameShape(QFrame.NoFrame)
        self.scroll_modulos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.widget_modulos = QWidget()
        self.layout_modulos = QVBoxLayout(self.widget_modulos)
        self.layout_modulos.setContentsMargins(0, 0, 10, 0) 
        
        self.permisos = {} 
        modulos = ["Libros", "Insumos", "Usuarios", "Préstamos", "Parámetros"]
        
        for modulo in modulos:
            marco = QFrame()
            marco.setStyleSheet("QFrame { border: 1px solid #bdc3c7; border-radius: 5px; padding: 5px; background-color: #f9f9f9; }")
            l_marco = QVBoxLayout(marco)
            
            lbl_tit = QLabel(f"Acceso a {modulo}")
            lbl_tit.setStyleSheet("font-weight: bold; border: none; background: transparent;")
            l_marco.addWidget(lbl_tit)
            
            lay_ver = QHBoxLayout()
            sw_ver = QCheckBox()
            sw_ver.setStyleSheet(ESTILO_SWITCH)
            lay_ver.addWidget(sw_ver)
            lay_ver.addWidget(QLabel("Ver"))
            lay_ver.addStretch()
            
            lay_editar = QHBoxLayout()
            sw_editar = QCheckBox()
            sw_editar.setStyleSheet(ESTILO_SWITCH)
            sw_editar.setEnabled(False) 
            lay_editar.addWidget(sw_editar)
            lay_editar.addWidget(QLabel("Permitir Crear y Editar"))
            lay_editar.addStretch()
            
            lay_borrar = QHBoxLayout()
            sw_borrar = QCheckBox()
            sw_borrar.setStyleSheet(ESTILO_SWITCH)
            sw_borrar.setEnabled(False) 
            lbl_borrar = QLabel("Permitir Borrado Físico")
            lbl_borrar.setStyleSheet("color: #c0392b; font-weight: bold;")
            lay_borrar.addWidget(sw_borrar)
            lay_borrar.addWidget(lbl_borrar)
            lay_borrar.addStretch()
            
            # --- Cierre (Closure) para blindar la evaluación de la cascada ---
            def crear_validador(v, e, b):
                def validador(*args):
                    estado_ver = v.isChecked()
                    e.setEnabled(estado_ver)
                    if not estado_ver:
                        e.blockSignals(True)
                        e.setChecked(False)
                        e.blockSignals(False)
                        
                    puede_borrar = estado_ver and e.isChecked()
                    b.setEnabled(puede_borrar)
                    if not puede_borrar:
                        b.blockSignals(True)
                        b.setChecked(False)
                        b.blockSignals(False)
                        
                    self.verificar_cambios()
                return validador
                
            validador_modulo = crear_validador(sw_ver, sw_editar, sw_borrar)
            
            sw_ver.stateChanged.connect(validador_modulo)
            sw_editar.stateChanged.connect(validador_modulo)
            sw_borrar.stateChanged.connect(self.verificar_cambios) # Borrar no dispara sub-cascadas, solo ensucia el estado
            
            l_marco.addLayout(lay_ver)
            l_marco.addLayout(lay_editar)
            l_marco.addLayout(lay_borrar)
            self.layout_modulos.addWidget(marco)
            
            nombre_clave = modulo.lower().replace("é", "e")
            self.permisos[nombre_clave] = {'ver': sw_ver, 'editar': sw_editar, 'borrar': sw_borrar, 'validador': validador_modulo}
            
        self.layout_modulos.addStretch() 
        self.scroll_modulos.setWidget(self.widget_modulos)
        self.layout_rbac.addWidget(self.scroll_modulos)
        
        self.layout_contenido.addWidget(self.widget_rbac)
        # ========================================================================
        
        # SOLUCIÓN: Empotrar el widget dentro del contenedor principal de la vista
        layout_principal.addWidget(self.widget_contenido)
        
        layout_principal.addStretch()
        
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.setMinimumHeight(45)
        self.btn_guardar.setStyleSheet("""
            QPushButton#ActionButton { font-weight: bold; font-size: 14px; background-color: #34495e; color: white; border-radius: 5px; }
            QPushButton#ActionButton:hover { background-color: #2c3e50; }
            QPushButton#ActionButton:disabled { background-color: #95a5a6; color: #ecf0f1; border: 1px solid #7f8c8d; }
        """)
        self.btn_guardar.setEnabled(False) # Inicia bloqueado
        layout_principal.addWidget(self.btn_guardar)

        self.widget_contenido.hide()
        self.btn_guardar.hide()
        self.widget_rbac.hide()
        self.scroll_modulos.hide()

    # --- LÓGICA DE ESTADO SUCIO (DIRTY STATE) ---
    def fijar_estado_original(self):
        """Toma una foto de los datos actuales tras cargar y la guarda para comparar. Bloquea el botón Guardar."""
        self._estado_original = self.obtener_datos_formulario()
        self.btn_guardar.setEnabled(False)

    def verificar_cambios(self, *args):
        """Compara el estado actual de la UI con la foto original. Si difiere, desbloquea el botón Guardar."""
        if self._estado_original is None:
            return
        
        estado_actual = self.obtener_datos_formulario()
        hay_cambios = estado_actual != self._estado_original
        self.btn_guardar.setEnabled(hay_cambios)
    # ---------------------------------------------

    def evaluar_visibilidad_permisos(self):
        if self.combo_rubro.currentText() == "Tipo Usuario":
            self.widget_rbac.show()
        else:
            self.widget_rbac.hide()

    def forzar_evaluacion_cascada(self):
        """Fuerza a la UI a reconectar la lógica de dependencias tras una inyección de datos masiva."""
        if self.switch_admitido.isChecked():
            for mod in self.permisos.values():
                mod['validador']() 

    def evaluar_switches_modulos(self):
        if self.switch_admitido.isChecked():
            self.scroll_modulos.show()
            self.scroll_modulos.verticalScrollBar().setValue(0) 
            self.forzar_evaluacion_cascada()
        else:
            self.scroll_modulos.hide()
            for mod in self.permisos.values():
                mod['ver'].setChecked(False)
                mod['validador']()

    def limpiar_campos_valores(self):
        self._estado_original = None # Suspendemos el tracking
        
        self.combo_rubro.blockSignals(True)
        self.combo_estado.blockSignals(True)
        self.switch_admitido.blockSignals(True)
        
        self.entrada_nombre.clear()
        self.combo_rubro.setCurrentIndex(0)
        self.combo_estado.setCurrentIndex(0)
        self.switch_admitido.setChecked(False)
        
        for mod in self.permisos.values():
            mod['ver'].blockSignals(True)
            mod['editar'].blockSignals(True)
            mod['borrar'].blockSignals(True)
            
            mod['ver'].setChecked(False)
            mod['editar'].setChecked(False)
            mod['borrar'].setChecked(False)
            
            mod['editar'].setEnabled(False)
            mod['borrar'].setEnabled(False)
            
            mod['ver'].blockSignals(False)
            mod['editar'].blockSignals(False)
            mod['borrar'].blockSignals(False)
            
        self.combo_rubro.blockSignals(False)
        self.combo_estado.blockSignals(False)
        self.switch_admitido.blockSignals(False)
        
        self.scroll_modulos.hide()
        self.btn_guardar.setEnabled(False)

    def limpiar_formulario(self):
        self.limpiar_campos_valores()
        self.btn_crear.setChecked(False)
        self.btn_editar.setChecked(False)
        self.widget_contenido.hide()
        self.btn_guardar.hide()
        self.widget_rbac.hide()

    def establecer_modo_ui(self, modo):
        self.widget_contenido.show()
        self.btn_guardar.show()
        
        if modo == 'crear':
            self.btn_crear.setChecked(True)
            self.btn_editar.setChecked(False)
            self.etiqueta_estado.hide()
            self.combo_estado.hide()
            self.limpiar_campos_valores()
            self.fijar_estado_original()
        else:  
            self.btn_crear.setChecked(False)
            self.btn_editar.setChecked(True)
            self.etiqueta_estado.show()
            self.combo_estado.show()
            
        self.evaluar_visibilidad_permisos()
        self.evaluar_switches_modulos()

    def obtener_datos_formulario(self):
        datos = {
            "nombre": self.entrada_nombre.text().strip(),
            "rubro": self.combo_rubro.currentText(),
            "estado": self.combo_estado.currentText(),
            "admitido": self.switch_admitido.isChecked(),
            "permisos": {}
        }
        
        for modulo, controles in self.permisos.items():
            datos["permisos"][modulo] = {
                "ver": controles["ver"].isChecked(),
                "editar": controles["editar"].isChecked(),
                "borrar": controles["borrar"].isChecked()
            }
            
        return datos