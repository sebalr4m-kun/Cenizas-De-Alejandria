from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt

class VistaLibro:
    def __init__(self, controlador):
        self.ctrl = controlador
        
        # Referencias de UI
        self.widget_vista = None
        self.widget_formulario = None
        self.widget_contenido_formulario = None
        self.tabla = None
        
        # Campos de entrada
        self.entrada_isbn = None
        self.entrada_titulo = None
        self.entrada_stock = None
        self.combo_autor = None
        self.combo_editorial = None
        self.combo_categoria = None
        self.combo_genero = None
        self.combo_estado = None
        self.etiqueta_estado = None
        self.entrada_busqueda = None
        
        # Botones de modo
        self.btn_crear = None
        self.btn_editar = None

    def construir_vista_catalogo(self):
        self.widget_vista = QWidget()
        layout = QVBoxLayout(self.widget_vista)
        
        titulo = QLabel("Catálogo de Libros")
        titulo.setProperty("isTitle", True) 
        layout.addWidget(titulo) 
        
        self.entrada_busqueda = QLineEdit(placeholderText="Filtrar por Título o ISBN...")
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.entrada_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Título", "ISBN", "Autor", "Stock", "Disponible"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)
        
        # Guardamos la referencia de la tabla en el controlador para que pueda refrescarla
        self.ctrl.tabla = self.tabla
        self.cargar_datos_tabla()
        return self.widget_vista

    def construir_formulario(self, ctrl_param):
        self.widget_formulario = QWidget()
        layout_principal = QVBoxLayout(self.widget_formulario)
        
        layout_principal.addWidget(QLabel("Acciones"))
        layout_modo = QHBoxLayout()
        self.btn_crear = QPushButton("Crear Nuevo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setChecked(True)
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
        self.entrada_isbn.editingFinished.connect(self.intentar_cargar_edicion)
        layout_contenido.addWidget(self.entrada_isbn)
        
        layout_contenido.addWidget(QLabel("Título"))
        self.entrada_titulo = QLineEdit()
        layout_contenido.addWidget(self.entrada_titulo)
        
        layout_contenido.addWidget(QLabel("Autor Principal"))
        self.combo_autor = QComboBox()
        layout_contenido.addWidget(self.combo_autor)
        
        layout_contenido.addWidget(QLabel("Editorial"))
        self.combo_editorial = QComboBox()
        layout_contenido.addWidget(self.combo_editorial)
        
        layout_contenido.addWidget(QLabel("Categoría"))
        self.combo_categoria = QComboBox()
        layout_contenido.addWidget(self.combo_categoria)
        
        layout_contenido.addWidget(QLabel("Género"))
        self.combo_genero = QComboBox()
        layout_contenido.addWidget(self.combo_genero)
        
        # Carga inicial de datos desde el controlador de parámetros
        self.actualizar_combos(ctrl_param)
        
        layout_contenido.addWidget(QLabel("Stock Total"))
        self.entrada_stock = QLineEdit()
        self.entrada_stock.setValidator(QIntValidator(0, 9999))
        layout_contenido.addWidget(self.entrada_stock)
        
        self.etiqueta_estado = QLabel("Estado del Libro")
        layout_contenido.addWidget(self.etiqueta_estado)
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["ACTIVA", "INACTIVA", "ELIMINADA"])
        layout_contenido.addWidget(self.combo_estado)
        
        layout_contenido.addStretch()
        btn_guardar = QPushButton("Guardar Libro")
        btn_guardar.setObjectName("ActionButton")
        btn_guardar.clicked.connect(self.procesar_guardado)
        layout_contenido.addWidget(btn_guardar)
        
        layout_principal.addWidget(self.widget_contenido_formulario)
        layout_principal.addStretch() 
        
        self.widget_contenido_formulario.hide() 
        self.establecer_modo('crear', inicial=True)
        return self.widget_formulario

    def actualizar_combos(self, ctrl_param):
        """Usa el modelo unificado para cargar todos los combos de libros"""
        if not ctrl_param: return
        
        combos_config = [
            (self.combo_autor, "Autor", "Seleccione Autor"),
            (self.combo_editorial, "Editorial", "Seleccione Editorial"),
            (self.combo_categoria, "Categoría", "Seleccione Categoría"),
            (self.combo_genero, "Género", "Seleccione Género")
        ]

        for combo, rubro, placeholder in combos_config:
            combo.clear()
            combo.addItem(placeholder, None)
            try:
                # Acceso directo al modelo del controlador unificado
                datos = ctrl_param.model.obtener_lista_activos(rubro)
                for d in datos:
                    combo.addItem(d['nombre'], d['id'])
            except Exception as e:
                print(f"Error cargando rubro {rubro}: {e}")

    def establecer_modo(self, modo, inicial=False):
        self.ctrl.modo = modo
        if modo == 'crear':
            self.btn_crear.setChecked(True)
            self.btn_editar.setChecked(False)
            self.entrada_isbn.setReadOnly(False)
            self.etiqueta_estado.hide()
            self.combo_estado.hide()
            self.limpiar_formulario()
        else:
            self.btn_crear.setChecked(False)
            self.btn_editar.setChecked(True)
            self.entrada_isbn.setReadOnly(False)
            self.etiqueta_estado.show()
            self.combo_estado.show()
            self.limpiar_formulario()
            
        if not inicial and self.widget_contenido_formulario:
            self.widget_contenido_formulario.show()

    def limpiar_formulario(self):
        self.entrada_titulo.clear()
        self.entrada_isbn.clear()
        self.entrada_stock.clear()
        if self.combo_autor: self.combo_autor.setCurrentIndex(0)
        if self.combo_editorial: self.combo_editorial.setCurrentIndex(0)
        if self.combo_categoria: self.combo_categoria.setCurrentIndex(0)
        if self.combo_genero: self.combo_genero.setCurrentIndex(0)
        if self.combo_estado: self.combo_estado.setCurrentText('ACTIVA')

    def cargar_datos_tabla(self):
        """Solicita los datos al controlador y los dibuja"""
        if not self.tabla: return
        datos = self.ctrl.obtener_todos()
        self.tabla.setRowCount(0)
        for i, d in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(str(d.get('titulo', '')))) 
            self.tabla.setItem(i, 1, QTableWidgetItem(str(d.get('isbn', ''))))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(d.get('Autor', 'Sin Autor'))))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(d.get('Stock', 0))))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(d.get('Cantidad_Disponible', 0))))

    def filtrar_tabla(self, texto):
        if not self.tabla: return
        texto = texto.lower()
        for i in range(self.tabla.rowCount()):
            coincidencia = False
            for j in range(self.tabla.columnCount()):
                item = self.tabla.item(i, j)
                if j in [0, 1] and item and texto in item.text().lower():
                    coincidencia = True
                    break
            self.tabla.setRowHidden(i, not coincidencia)

    def intentar_cargar_edicion(self):
        if self.ctrl.modo != 'editar': return
        isbn = self.entrada_isbn.text().strip()
        if not isbn: 
            self.limpiar_formulario()
            return
            
        libro = self.ctrl.obtener_por_isbn(isbn)
        if libro:
            QMessageBox.information(None, "Éxito", "Libro localizado en el archivo.")
            self.entrada_titulo.setText(libro['titulo'])
            estado_bd = libro.get('estado')
            self.combo_estado.setCurrentText(estado_bd if estado_bd != 'INACTIVO' else 'INACTIVA')
            self.entrada_stock.setText(str(libro.get('stock_total') or 0))
            
            # Mapeo de IDs para posicionar los ComboBox
            mapeo = [
                (self.combo_autor, 'primer_id_autor'), 
                (self.combo_editorial, 'primer_id_editorial'),
                (self.combo_categoria, 'primer_id_categoria'),
                (self.combo_genero, 'primer_id_genero')
            ]
            for combo, key in mapeo:
                if libro.get(key):
                    idx = combo.findData(libro[key])
                    if idx != -1: combo.setCurrentIndex(idx)
            
            self.entrada_isbn.setReadOnly(True) 
        else:
            QMessageBox.warning(None, "Aviso", "No se encontró ningún registro con ese ISBN.")

    def procesar_guardado(self):
        isbn = self.entrada_isbn.text().strip()
        titulo = self.entrada_titulo.text().strip()
        
        try:
            stock_str = self.entrada_stock.text().strip()
            stock = int(stock_str) if stock_str else 0
            if stock < 0: raise ValueError
        except ValueError:
            QMessageBox.warning(None, "Error", "El Stock debe ser un valor numérico válido.")
            return

        id_autor = self.combo_autor.currentData()
        id_editorial = self.combo_editorial.currentData()
        id_categoria = self.combo_categoria.currentData()
        id_genero = self.combo_genero.currentData()

        if not isbn or not titulo or not id_autor:
            QMessageBox.warning(None, "Datos Faltantes", "ISBN, Título y Autor son obligatorios.")
            return

        try:
            if self.ctrl.modo == 'crear':
                if self.ctrl.obtener_por_isbn(isbn):
                    QMessageBox.warning(None, "Error", "Este ISBN ya existe en el sistema.")
                    return
                self.ctrl.guardar_bd(titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, 'ACTIVO', False)
                QMessageBox.information(None, "Éxito", "Nuevo libro registrado con éxito.")
            else:
                estado_ui = self.combo_estado.currentText()
                if estado_ui == 'ELIMINADA':
                    confirmar = QMessageBox.question(None, "Confirmar", "¿Eliminar este libro por completo?", QMessageBox.Yes | QMessageBox.No)
                    if confirmar == QMessageBox.Yes:
                        self.ctrl.eliminar_todo(isbn)
                        QMessageBox.information(None, "Info", "Libro eliminado permanentemente.")
                    else: return
                else:
                    estado_bd = 'INACTIVO' if estado_ui == 'INACTIVA' else 'ACTIVO'
                    self.ctrl.guardar_bd(titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, estado_bd, True)
                    QMessageBox.information(None, "Info", "Registro actualizado correctamente.")
            
            # Post-guardado: Refrescar UI
            self.cargar_datos_tabla()
            self.limpiar_formulario()
            self.ctrl.libro_guardado.emit()
            
        except Exception as e:
            QMessageBox.critical(None, "Error Crítico", f"Fallo en la operación: {str(e)}")