from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt

class VistaLibro:
    def __init__(self, controlador):
        self.ctrl = controlador
        self.widget_vista = None
        self.widget_formulario = None
        self.widget_contenido_formulario = None
        self.tabla = None

        # Referencias de UI
        self.entrada_isbn = None
        self.entrada_titulo = None
        self.entrada_stock = None
        self.combo_autor = None
        self.combo_editorial = None
        self.combo_categoria = None
        self.combo_genero = None
        self.combo_estado = None
        self.etiqueta_estado = None
        
        self.btn_crear = None
        self.btn_editar = None
        
        # Referencia al controlador de parámetros para refrescos rápidos
        self.ultima_ref_param = None

    def construir_vista_catalogo(self):
        self.widget_vista = QWidget()
        layout = QVBoxLayout(self.widget_vista)
        
        titulo = QLabel("Catálogo de Libros")
        titulo.setProperty("isTitle", True) 
        layout.addWidget(titulo) 
        
        self.entrada_busqueda = QLineEdit()
        self.entrada_busqueda.setPlaceholderText("🔍 Filtrar por Título o ISBN...")
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.entrada_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Título", "ISBN", "Autor", "Disponible", "Stock Total"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # --- CONFIGURACIÓN DE TABLA ---
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(False)
        
        self.tabla.clicked.connect(self.solicitar_edicion_desde_tabla)
        self.tabla.itemDoubleClicked.connect(self.solicitar_edicion_desde_tabla)
        
        layout.addWidget(self.tabla)
        self.ctrl.tabla = self.tabla
        return self.widget_vista

    def actualizar_tabla(self, datos=None):
        """
        ACTUALIZACIÓN AGRESIVA: Si no se pasan datos, la vista los solicita 
        directamente al controlador para asegurar sincronía con la matriz.
        """
        if not self.tabla: return
        
        # Si no nos pasan datos (llamada desde el Refresco Agresivo), los buscamos
        if datos is None:
            if hasattr(self.ctrl, 'model') and hasattr(self.ctrl.model, 'obtener_todos'):
                datos = self.ctrl.model.obtener_todos()
            else:
                # Intento de respaldo si la estructura varía
                datos = []

        self.tabla.setRowCount(0)
        for i, d in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(str(d.get('titulo', ''))))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(d.get('isbn', ''))))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(d.get('autor', 'Sin Autor'))))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(d.get('cantidad_disponible', 0))))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(d.get('stock', 0))))

    def filtrar_tabla(self, texto):
        texto = texto.lower()
        for i in range(self.tabla.rowCount()):
            t_match = texto in (self.tabla.item(i, 0).text().lower() if self.tabla.item(i,0) else "")
            i_match = texto in (self.tabla.item(i, 1).text().lower() if self.tabla.item(i,1) else "")
            self.tabla.setRowHidden(i, not (t_match or i_match))

    def construir_formulario(self, ctrl_param):
        self.ultima_ref_param = ctrl_param # Guardamos referencia para refrescos de combos
        self.widget_formulario = QWidget()
        layout_principal = QVBoxLayout(self.widget_formulario)
        
        layout_modo = QHBoxLayout()
        self.btn_crear = QPushButton("Crear Nuevo")
        self.btn_crear.setCheckable(True)
        self.btn_editar = QPushButton("Editar Existente")
        self.btn_editar.setCheckable(True)
        
        self.btn_crear.clicked.connect(lambda: self.establecer_modo('crear'))
        self.btn_editar.clicked.connect(lambda: self.establecer_modo('editar'))
        
        layout_modo.addWidget(self.btn_crear)
        layout_modo.addWidget(self.btn_editar)
        layout_principal.addLayout(layout_modo)

        self.widget_contenido_formulario = QWidget()
        layout_contenido = QVBoxLayout(self.widget_contenido_formulario)
        
        layout_contenido.addWidget(QLabel("ISBN (Identificador)"))
        self.entrada_isbn = QLineEdit()
        self.entrada_isbn.editingFinished.connect(self.intent_auto_carga)
        layout_contenido.addWidget(self.entrada_isbn)
        
        layout_contenido.addWidget(QLabel("Título"))
        self.entrada_titulo = QLineEdit()
        layout_contenido.addWidget(self.entrada_titulo)
        
        # Selects (QComboBox)
        self.combo_autor = self._crear_combo(layout_contenido, "Autor", ctrl_param)
        self.combo_editorial = self._crear_combo(layout_contenido, "Editorial", ctrl_param)
        self.combo_categoria = self._crear_combo(layout_contenido, "Categoría", ctrl_param)
        self.combo_genero = self._crear_combo(layout_contenido, "Género", ctrl_param)
        
        layout_contenido.addWidget(QLabel("Unidades en Stock"))
        self.entrada_stock = QLineEdit()
        self.entrada_stock.setValidator(QIntValidator(0, 999))
        layout_contenido.addWidget(self.entrada_stock)
        
        self.etiqueta_estado = QLabel("Estado del Registro")
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["ACTIVA", "INACTIVA"])
        layout_contenido.addWidget(self.etiqueta_estado)
        layout_contenido.addWidget(self.combo_estado)
        
        layout_contenido.addStretch()
        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setObjectName("ActionButton")
        btn_guardar.clicked.connect(self.procesar_guardado)
        layout_contenido.addWidget(btn_guardar)
        
        layout_principal.addWidget(self.widget_contenido_formulario)
        layout_principal.addStretch() 
        
        self.widget_contenido_formulario.hide() 
        return self.widget_formulario

    def establecer_modo(self, modo, inicial=False):
        if inicial:
            self.btn_crear.setChecked(False)
            self.btn_editar.setChecked(False)
            self.widget_contenido_formulario.hide()
            return

        self.ctrl.modo = modo
        self.btn_crear.setChecked(modo == 'crear')
        self.btn_editar.setChecked(modo == 'editar')
        
        self.limpiar_formulario()
        self.entrada_isbn.setReadOnly(False)
        
        if modo == 'crear':
            self.etiqueta_estado.hide()
            self.combo_estado.hide()
        else:
            self.etiqueta_estado.show()
            self.combo_estado.show()
            
        self.widget_contenido_formulario.show()
        # Al abrir el formulario, forzamos recarga de combos por si hubo cambios en Parámetros
        self.cargar_combos()

    def _crear_combo(self, layout, rubro, ctrl_param):
        layout.addWidget(QLabel(rubro))
        combo = QComboBox()
        self._cargar_datos_combo(combo, rubro, ctrl_param)
        layout.addWidget(combo)
        return combo

    def cargar_combos(self):
        """Método público para el Refresco Agresivo desde MainWindow."""
        if not self.ultima_ref_param: return
        
        self._cargar_datos_combo(self.combo_autor, "Autor", self.ultima_ref_param)
        self._cargar_datos_combo(self.combo_editorial, "Editorial", self.ultima_ref_param)
        self._cargar_datos_combo(self.combo_categoria, "Categoría", self.ultima_ref_param)
        self._cargar_datos_combo(self.combo_genero, "Género", self.ultima_ref_param)

    def _cargar_datos_combo(self, combo, rubro, ctrl_param):
        if not combo: return
        # Guardar selección actual para intentar restaurarla tras el refresco
        id_actual = combo.currentData()
        
        combo.clear()
        try:
            datos = ctrl_param.model.obtener_lista_activos(rubro)
            combo.addItem(f"Seleccione {rubro}", None)
            for d in datos:
                combo.addItem(d['nombre'], d['id'])
            
            # Intentar volver a seleccionar lo que estaba antes del refresco
            if id_actual:
                index = combo.findData(id_actual)
                if index != -1: combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Error cargando {rubro} en Libros: {e}")

    def solicitar_edicion_desde_tabla(self, index):
        fila = index.row()
        item_isbn = self.tabla.item(fila, 1)
        if not item_isbn: return
        
        isbn = item_isbn.text()
        self.establecer_modo('editar')
        self.entrada_isbn.setText(isbn)
        self.intentar_cargar_edicion()

    def intent_auto_carga(self):
        if hasattr(self.ctrl, 'modo') and self.ctrl.modo == 'editar':
            self.intentar_cargar_edicion()

    def intentar_cargar_edicion(self):
        isbn = self.entrada_isbn.text().strip()
        if not isbn: return
            
        libro = self.ctrl.obtener_por_isbn(isbn)
        if libro:
            self.entrada_titulo.setText(libro.get('titulo', ''))
            self.entrada_stock.setText(str(libro.get('stock_total') or 0))
            estado_db = libro.get('estado', 'ACTIVO')
            self.combo_estado.setCurrentText('ACTIVA' if estado_db == 'ACTIVO' else 'INACTIVA')
            
            mapeo = [
                (self.combo_autor, 'primer_id_autor'), 
                (self.combo_editorial, 'primer_id_editorial'),
                (self.combo_categoria, 'primer_id_categoria'), 
                (self.combo_genero, 'primer_id_genero')
            ]
            for combo, key in mapeo:
                id_val = libro.get(key)
                idx = combo.findData(id_val)
                combo.setCurrentIndex(idx if idx != -1 else 0)
            
            self.entrada_isbn.setReadOnly(True) 

    def procesar_guardado(self):
        try:
            datos = {
                'isbn': self.entrada_isbn.text().strip(),
                'titulo': self.entrada_titulo.text().strip(),
                'stock': int(self.entrada_stock.text() or 0),
                'id_autor': self.combo_autor.currentData(),
                'id_editorial': self.combo_editorial.currentData(),
                'id_categoria': self.combo_categoria.currentData(),
                'id_genero': self.combo_genero.currentData(),
                'estado': 'ACTIVO' if self.combo_estado.currentText() == 'ACTIVA' else 'INACTIVO'
            }

            if not datos['isbn'] or not datos['titulo'] or not datos['id_autor']:
                QMessageBox.warning(None, "Faltan datos", "ISBN, Título y Autor son obligatorios.")
                return

            es_act = (getattr(self.ctrl, 'modo', 'crear') == 'editar')
            self.ctrl.guardar_bd(
                datos['titulo'], datos['isbn'], datos['id_autor'], 
                datos['id_editorial'], datos['id_categoria'], datos['id_genero'], 
                datos['stock'], datos['estado'], es_act
            )

            # EMISIÓN DE SEÑAL DE ÉXITO (Para que MainWindow dispare el Refresco Agresivo)
            if hasattr(self.ctrl, 'libro_guardado'):
                self.ctrl.libro_guardado.emit() 
            
            QMessageBox.information(None, "Éxito", "Cambios aplicados correctamente.")
            self.establecer_modo('crear', inicial=True)
            self.limpiar_formulario()

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error en el guardado: {e}")

    def limpiar_formulario(self):
        self.entrada_isbn.clear()
        self.entrada_titulo.clear()
        self.entrada_stock.clear()
        for combo in [self.combo_autor, self.combo_editorial, self.combo_categoria, self.combo_genero]:
            if combo: combo.setCurrentIndex(0)