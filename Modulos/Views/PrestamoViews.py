# ==========================================
# Archivo: PrestamoViews.py (Actualizado)
# ==========================================
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt

# --- CLASE CUSTOM PARA LISTAS CON MÚLTIPLES CHECKBOXES (INSUMOS/DEVOLUCIONES) ---
class ListaCheckable(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background-color: #f5f6fa;
            }
            QListWidget::item:selected {
                background-color: #dff9fb;
                color: #2c3e50;
            }
            QListWidget::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #bdc3c7;
                background-color: #ecf0f1;
                margin-right: 5px;
            }
            QListWidget::indicator:checked {
                background-color: #3498db;
                border: 2px solid #2980b9;
            }
        """)

    def addItem(self, item):
        if isinstance(item, str):
            item = QListWidgetItem(item)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        if item.checkState() == Qt.CheckState.Unchecked or not item.data(Qt.CheckStateRole):
            item.setCheckState(Qt.Unchecked)
        super().addItem(item)
        
    def insertItem(self, row, item):
        if isinstance(item, str):
            item = QListWidgetItem(item)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        if item.checkState() == Qt.CheckState.Unchecked or not item.data(Qt.CheckStateRole):
            item.setCheckState(Qt.Unchecked)
        super().insertItem(row, item)

    def mousePressEvent(self, event):
        """Intercepta el clic para evitar el doble toggle nativo y permitir clics en toda la fila."""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            # Si el elemento existe y está habilitado
            if item and (item.flags() & Qt.ItemIsEnabled):
                nuevo_estado = Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked
                item.setCheckState(nuevo_estado)
                self.setCurrentItem(item) # Mantiene el resaltado visual
                event.accept()
                return
        super().mousePressEvent(event)


# --- CLASE CUSTOM PARA LISTA DE USUARIOS (SELECCIÓN ÚNICA EXCLUYENTE) ---
class ListaUsuariosUnicos(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background-color: #f5f6fa;
            }
            QListWidget::item:selected {
                background-color: #dff9fb;
                color: #2c3e50;
            }
            QListWidget::indicator {
                width: 20px;
                height: 20px;
                border-radius: 10px; /* Diseño circular estilo Radio Button */
                border: 2px solid #bdc3c7;
                background-color: #ecf0f1;
                margin-right: 5px;
            }
            QListWidget::indicator:checked {
                background-color: #3498db;
                border: 2px solid #2980b9;
            }
        """)

    def addItem(self, item):
        if isinstance(item, str):
            item = QListWidgetItem(item)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        if item.checkState() == Qt.CheckState.Unchecked or not item.data(Qt.CheckStateRole):
            item.setCheckState(Qt.Unchecked)
        super().addItem(item)
        
    def insertItem(self, row, item):
        if isinstance(item, str):
            item = QListWidgetItem(item)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        if item.checkState() == Qt.CheckState.Unchecked or not item.data(Qt.CheckStateRole):
            item.setCheckState(Qt.Unchecked)
        super().insertItem(row, item)

    def mousePressEvent(self, event):
        """Aplica la lógica estricta de Radio Button y control de focos lógicos."""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item and (item.flags() & Qt.ItemIsEnabled):
                estado_previo = item.checkState()
                
                # Desmarcar todos los demás por seguridad
                for i in range(self.count()):
                    self.item(i).setCheckState(Qt.Unchecked)

                if estado_previo == Qt.Checked:
                    # El usuario se arrepiente y desmarca; vaciamos el foco lógico.
                    self.setCurrentItem(None)
                    self.clearSelection()
                else:
                    # Se marca correctamente como único objetivo.
                    item.setCheckState(Qt.Checked)
                    self.setCurrentItem(item)
                    
                event.accept()
                return
        super().mousePressEvent(event)


class VistaTablaPrestamo(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        titulo = QLabel("Gestión de Préstamos y Devoluciones")
        titulo.setProperty("isTitle", True)
        layout.addWidget(titulo)
        
        self.entrada_busqueda = QLineEdit()
        self.entrada_busqueda.setPlaceholderText("🔍 Filtrar por Usuario o ID de Préstamo...")
        self.entrada_busqueda.setMinimumHeight(30)
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.entrada_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "ID Préstamo", "Usuario Solicitante", "Progreso (Devueltos / Total)", "Fecha Préstamo", "Estado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("QTableWidget { gridline-color: #dcdde1; }")
        
        self.tabla.cellDoubleClicked.connect(self._on_fila_doble_click)
        layout.addWidget(self.tabla)

    def _on_fila_doble_click(self, fila, columna):
        if self.ctrl and hasattr(self.ctrl, 'widget_formulario'):
            self.ctrl.widget_formulario.establecer_modo('editar')
            self.tabla.blockSignals(True)
            self.tabla.clearSelection()
            self.tabla.blockSignals(False)
            self.tabla.selectRow(fila)

    def actualizar_tabla(self, datos):
        self.tabla.setRowCount(0)
        for fila, prestamo in enumerate(datos):
            self.tabla.insertRow(fila)

            usuario_texto = f"{prestamo['usuario_nombre']} ({prestamo['usuario_email']})"
            progreso = f"{prestamo['items_devueltos']} / {prestamo['total_items']} ítems devueltos"
            fecha = prestamo['fecha_prestamo'] if prestamo['fecha_prestamo'] else 'N/A'
            estado = prestamo['estado_prestamo']

            item_id = QTableWidgetItem(str(prestamo['id_prestamo']))
            item_id.setData(Qt.UserRole, prestamo)

            self.tabla.setItem(fila, 0, item_id)
            self.tabla.setItem(fila, 1, QTableWidgetItem(usuario_texto))
            self.tabla.setItem(fila, 2, QTableWidgetItem(progreso))
            self.tabla.setItem(fila, 3, QTableWidgetItem(fecha))
            self.tabla.setItem(fila, 4, QTableWidgetItem(estado))

    def filtrar_tabla(self, texto):
        texto = texto.lower()
        for i in range(self.tabla.rowCount()):
            coincidencia = False
            for j in range(self.tabla.columnCount()):
                item = self.tabla.item(i, j)
                if item and texto in item.text().lower():
                    coincidencia = True
                    break
            self.tabla.setRowHidden(i, not coincidencia)

    def limpiar_interfaz(self):
        self.entrada_busqueda.clear()
        self.tabla.setRowCount(0)


class FormularioPrestamo(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        self.modo = 'crear'
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(5, 5, 5, 5)
        layout_principal.setAlignment(Qt.AlignTop)
        
        contenedor_modos = QFrame()
        layout_modo = QHBoxLayout(contenedor_modos)
        
        self.btn_crear = QPushButton("Nuevo Préstamo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setMinimumHeight(35)
        self.btn_editar = QPushButton("Gestionar / Devolver")
        self.btn_editar.setCheckable(True)
        self.btn_editar.setMinimumHeight(35)
        
        layout_modo.addWidget(self.btn_crear)
        layout_modo.addWidget(self.btn_editar)
        layout_principal.addWidget(contenedor_modos)
        
        self.widget_contenido = QWidget()
        layout_campos = QVBoxLayout(self.widget_contenido)
        layout_campos.setContentsMargins(10, 10, 10, 10)
        layout_campos.setSpacing(8)
        
        # --- SECCIÓN USUARIO ---
        self.label_usuario = QLabel("1. Usuario Solicitante")
        self.label_usuario.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout_campos.addWidget(self.label_usuario)
        
        self.buscar_usuario = QLineEdit()
        self.buscar_usuario.setPlaceholderText("🔍 Buscar usuario por nombre o correo...")
        self.buscar_usuario.setMinimumHeight(30)
        self.buscar_usuario.textChanged.connect(self.filtrar_lista_usuarios)
        layout_campos.addWidget(self.buscar_usuario)
        
        # FIX: Integrada la nueva clase estricta para usuarios
        self.lista_usuarios = ListaUsuariosUnicos()
        layout_campos.addWidget(self.lista_usuarios)
        
        # --- SECCIÓN CATEGORÍA E ÍTEMS (NUEVO PRÉSTAMO) ---
        self.container_creacion = QWidget()
        layout_creacion = QVBoxLayout(self.container_creacion)
        layout_creacion.setContentsMargins(0, 0, 0, 0)

        lbl_cat = QLabel("2. Seleccionar Categoría de Insumo")
        lbl_cat.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout_creacion.addWidget(lbl_cat)
        
        self.combo_tipo_insumo = QComboBox()
        self.combo_tipo_insumo.setMinimumHeight(30)
        self.combo_tipo_insumo.currentIndexChanged.connect(self.ctrl.al_cambiar_categoria)
        layout_creacion.addWidget(self.combo_tipo_insumo)
        
        lbl_ins = QLabel("3. Seleccionar Libros / Insumos a prestar")
        lbl_ins.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout_creacion.addWidget(lbl_ins)
        
        self.buscar_insumo = QLineEdit()
        self.buscar_insumo.setPlaceholderText("🔍 Buscar insumos disponibles...")
        self.buscar_insumo.setMinimumHeight(30)
        self.buscar_insumo.textChanged.connect(self.filtrar_lista_insumos)
        layout_creacion.addWidget(self.buscar_insumo)
        
        self.lista_insumos = ListaCheckable()
        layout_creacion.addWidget(self.lista_insumos)

        layout_campos.addWidget(self.container_creacion)

        # --- SECCIÓN DEVOLUCIÓN DE ÍTEMS ---
        self.container_devolucion = QWidget()
        layout_devolucion = QVBoxLayout(self.container_devolucion)
        layout_devolucion.setContentsMargins(0, 0, 0, 0)

        self.label_prestamo_info = QLabel("Seleccione un préstamo de la tabla")
        self.label_prestamo_info.setStyleSheet("font-weight: bold; color: #1e88e5;")
        layout_devolucion.addWidget(self.label_prestamo_info)

        lbl_dev = QLabel("🔍 Buscar ítem a devolver:")
        lbl_dev.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout_devolucion.addWidget(lbl_dev)
        
        self.buscar_item_devolucion = QLineEdit()
        self.buscar_item_devolucion.setPlaceholderText("Buscar por título o RUNA en este préstamo...")
        self.buscar_item_devolucion.setMinimumHeight(30)
        self.buscar_item_devolucion.textChanged.connect(self.filtrar_devolucion_items)
        layout_devolucion.addWidget(self.buscar_item_devolucion)

        self.lista_devolucion = ListaCheckable()
        layout_devolucion.addWidget(self.lista_devolucion)

        layout_campos.addWidget(self.container_devolucion)

        # --- BOTONES DE ACCIÓN ---
        estilos_botones = """
            QPushButton#ActionButton { font-weight: bold; font-size: 14px; background-color: #34495e; color: white; border-radius: 5px; }
            QPushButton#ActionButton:hover { background-color: #2c3e50; }
            QPushButton#ActionButton:disabled { background-color: #95a5a6; color: #ecf0f1; border: 1px solid #7f8c8d; }
        """

        self.btn_guardar = QPushButton("Registrar Préstamo Conjunto")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.setMinimumHeight(45)
        self.btn_guardar.setStyleSheet(estilos_botones)
        layout_campos.addWidget(self.btn_guardar)

        self.btn_devolver = QPushButton("Registrar Devolución")
        self.btn_devolver.setObjectName("ActionButton")
        self.btn_devolver.setMinimumHeight(45)
        self.btn_devolver.setStyleSheet(estilos_botones)
        layout_campos.addWidget(self.btn_devolver)
        
        layout_principal.addWidget(self.widget_contenido)
        
        self.widget_contenido.hide()
        self.btn_crear.clicked.connect(lambda: self.establecer_modo('crear'))
        self.btn_editar.clicked.connect(lambda: self.establecer_modo('editar'))


    def establecer_modo(self, modo, inicial=False):
        self.modo = modo
        es_crear = (modo == 'crear')
        self.btn_crear.setChecked(es_crear)
        self.btn_editar.setChecked(not es_crear)

        if es_crear:
            self.container_creacion.show()
            self.container_devolucion.hide()
            self.btn_guardar.show()
            self.btn_devolver.hide()
            self.lista_usuarios.show()
            self.buscar_usuario.show()
            self.label_usuario.show()
        else:
            self.container_creacion.hide()
            self.container_devolucion.show()
            self.btn_guardar.hide()
            self.btn_devolver.show()
            self.lista_usuarios.hide()
            self.buscar_usuario.hide()
            self.label_usuario.hide()
        
        if not inicial:
            self.widget_contenido.show()
        else:
            self.widget_contenido.hide()

    def filtrar_lista_usuarios(self, texto):
        texto = texto.lower()
        for i in range(self.lista_usuarios.count()):
            item = self.lista_usuarios.item(i)
            item.setHidden(texto not in item.text().lower())

    def filtrar_lista_insumos(self, *args):
        texto = self.buscar_insumo.text().lower()
        id_categoria = self.combo_tipo_insumo.currentData()
        
        for i in range(self.lista_insumos.count()):
            item = self.lista_insumos.item(i)
            match_texto = texto in item.text().lower()
            
            id_tipo_item = item.data(Qt.UserRole + 1)
            
            match_categoria = True
            if id_categoria is not None:
                match_categoria = (id_categoria == id_tipo_item)
                
            item.setHidden(not (match_texto and match_categoria))

    def filtrar_devolucion_items(self, texto):
        texto = texto.lower()
        for i in range(self.lista_devolucion.count()):
            item = self.lista_devolucion.item(i)
            item.setHidden(texto not in item.text().lower())

    def limpiar_interfaz(self):
        self.buscar_usuario.clear()
        self.buscar_insumo.clear()
        self.buscar_item_devolucion.clear()
        self.lista_usuarios.clear()
        
        for i in range(self.lista_insumos.count()):
            item = self.lista_insumos.item(i)
            item.setCheckState(Qt.Unchecked)
            
        self.lista_devolucion.clear()
        
        if self.combo_tipo_insumo.count() > 0:
            self.combo_tipo_insumo.setCurrentIndex(0)
            
        self.btn_crear.setChecked(False)
        self.btn_editar.setChecked(False)
        self.widget_contenido.hide()