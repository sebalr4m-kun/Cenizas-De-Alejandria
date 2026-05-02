from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QDateEdit, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate, Signal
from datetime import datetime

class VistaTablaInsumo(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        titulo = QLabel("Catálogo de Insumos")
        titulo.setProperty("isTitle", True) 
        layout.addWidget(titulo)
        
        self.entrada_busqueda = QLineEdit()
        self.entrada_busqueda.setPlaceholderText("🔍 Filtrar por Título, RUNA o Categoría...")
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla) 
        layout.addWidget(self.entrada_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Título", "Clave RUNA", "Categoría", "Estado", "Adquisición"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        
        self.tabla.itemDoubleClicked.connect(self.solicitar_edicion)
        
        layout.addWidget(self.tabla)

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

    def actualizar_datos(self, datos):
        """Actualiza la tabla filtrando automáticamente libros de ISBNs inactivos"""
        self.tabla.setRowCount(0)
        fila_actual = 0
        for d in datos:
            # Lógica de filtrado: Si el ISBN asociado está marcado como inactivo, no se muestra
            if d.get('IsbnActivo') == 0: 
                continue
                
            self.tabla.insertRow(fila_actual)
            self.tabla.setItem(fila_actual, 0, QTableWidgetItem(str(d.get('Titulo', ''))))
            self.tabla.setItem(fila_actual, 1, QTableWidgetItem(str(d.get('Clave RUNA', ''))))
            self.tabla.setItem(fila_actual, 2, QTableWidgetItem(str(d.get('Categoria', ''))))
            self.tabla.setItem(fila_actual, 3, QTableWidgetItem(str(d.get('Estado', ''))))
            self.tabla.setItem(fila_actual, 4, QTableWidgetItem(str(d.get('Adquisicion', ''))))
            fila_actual += 1

    def solicitar_edicion(self, item):
        fila = item.row()
        runa = self.tabla.item(fila, 1).text()
        if self.ctrl.widget_formulario:
            self.ctrl.widget_formulario.establecer_modo('editar')
            self.ctrl.widget_formulario.entrada_runa.setText(runa)

class FormularioInsumo(QWidget):
    # Señal para avisar a otros módulos (como Libros) que deben refrescarse
    cambio_realizado = Signal()

    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        self.modo = 'crear'
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(5, 5, 5, 5)
        
        contenedor_modos = QFrame()
        layout_modo = QHBoxLayout(contenedor_modos)
        
        self.btn_crear = QPushButton("Crear Nuevo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.clicked.connect(lambda: self.establecer_modo('crear'))
        
        self.btn_editar = QPushButton("Editar Existente")
        self.btn_editar.setCheckable(True)
        self.btn_editar.clicked.connect(lambda: self.establecer_modo('editar'))
        
        layout_modo.addWidget(self.btn_crear)
        layout_modo.addWidget(self.btn_editar)
        layout_principal.addWidget(contenedor_modos)
        
        self.widget_contenido = QWidget()
        layout_campos = QVBoxLayout(self.widget_contenido)

        self.etiqueta_runa = QLabel("Clave RUNA")
        layout_campos.addWidget(self.etiqueta_runa)
        self.entrada_runa = QLineEdit()
        self.entrada_runa.setPlaceholderText("Escriba RUNA para buscar...")
        self.entrada_runa.textChanged.connect(self.intentar_cargar_edicion)
        layout_campos.addWidget(self.entrada_runa)

        layout_campos.addWidget(QLabel("Título del Insumo"))
        self.entrada_nombre = QLineEdit()
        layout_campos.addWidget(self.entrada_nombre)
        
        layout_campos.addWidget(QLabel("Categoría"))
        self.combo_cat = QComboBox() 
        layout_campos.addWidget(self.combo_cat)
        
        self.etiqueta_fecha = QLabel("Fecha Adquisición") 
        layout_campos.addWidget(self.etiqueta_fecha)
        self.entrada_fecha = QDateEdit(calendarPopup=True)
        self.entrada_fecha.setDisplayFormat("yyyy-MM-dd")
        self.entrada_fecha.setDate(QDate.currentDate())
        layout_campos.addWidget(self.entrada_fecha)
        
        self.etiqueta_estado = QLabel("Estado")
        layout_campos.addWidget(self.etiqueta_estado)
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["DISPONIBLE", "PRESTADO", "MANTENIMIENTO", "SUSPENDIDA", "ELIMINADA"])
        layout_campos.addWidget(self.combo_estado)
        
        layout_campos.addStretch()
        
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.setMinimumHeight(40)
        self.btn_guardar.clicked.connect(self.ejecutar_guardado)
        layout_campos.addWidget(self.btn_guardar)
        
        layout_principal.addWidget(self.widget_contenido)
        layout_principal.addStretch() 
        
        self.establecer_modo('crear', inicial=True)

    def establecer_modo(self, modo, inicial=False):
        self.modo = modo
        es_crear = (modo == 'crear')
        
        self.btn_crear.setChecked(es_crear)
        self.btn_editar.setChecked(not es_crear)
        
        self.entrada_runa.setVisible(not es_crear)
        self.etiqueta_runa.setVisible(not es_crear)
        self.etiqueta_fecha.setVisible(not es_crear)
        self.entrada_fecha.setVisible(not es_crear)
        self.etiqueta_estado.setVisible(not es_crear)
        self.combo_estado.setVisible(not es_crear)
        
        self.limpiar()
        
        if not inicial:
            self.widget_contenido.show()
        else:
            self.widget_contenido.hide()

    def limpiar(self):
        self.entrada_runa.clear()
        self.entrada_nombre.clear()
        self.entrada_nombre.setReadOnly(False)
        self.combo_cat.setEnabled(True)
        self.entrada_fecha.setDate(QDate.currentDate())
        self.entrada_fecha.setReadOnly(False)
        if self.combo_cat.count() > 0:
            self.combo_cat.setCurrentIndex(0)
        self.combo_estado.setCurrentText("DISPONIBLE")

    def intentar_cargar_edicion(self):
        if self.modo != 'editar': return
        
        clave_runa = self.entrada_runa.text().strip()
        if len(clave_runa) < 3: return 
        
        item = self.ctrl.obtener_uno(clave_runa) 
        if item:
            self.entrada_nombre.setText(item.get('titulo', ''))
            
            id_tipo = item.get('id_tipo_insumo')
            indice = self.combo_cat.findData(id_tipo)
            if indice != -1: self.combo_cat.setCurrentIndex(indice)
            
            fecha_bd = item.get('fecha_adquisicion')
            if fecha_bd:
                qdate = QDate.fromString(str(fecha_bd), "yyyy-MM-dd")
                self.entrada_fecha.setDate(qdate)
            
            estado_db = item.get('estado', 'DISPONIBLE')
            estado_ui = 'SUSPENDIDA' if estado_db == 'INACTIVA' else estado_db
            self.combo_estado.setCurrentText(estado_ui)
            
            if self.ctrl.es_libro(id_tipo):
                self.entrada_nombre.setReadOnly(True)
                self.combo_cat.setEnabled(False)
                self.entrada_fecha.setReadOnly(True)
            else:
                self.entrada_nombre.setReadOnly(False)
                self.combo_cat.setEnabled(True)
                self.entrada_fecha.setReadOnly(False)

    def ejecutar_guardado(self):
        datos = {
            'modo': self.modo,
            'titulo': self.entrada_nombre.text().strip(),
            'id_tipo': self.combo_cat.currentData(),
            'clave_runa': self.entrada_runa.text().strip(),
            'estado_ui': self.combo_estado.currentText(),
            'fecha_ui': self.entrada_fecha.date().toString("yyyy-MM-dd")
        }
        
        exito = self.ctrl.manejar_guardado(datos)
        
        if exito:
            # 1. Solución Formulario Fantasma: Resetear y ocultar tras guardar
            self.establecer_modo('crear', inicial=True)
            
            # 2. Sincronización: Emitir señal para que la matriz de Libros se actualice
            # El controlador debe estar conectado a esta señal para refrescar la otra vista.
            self.cambio_realizado.emit()
            
            # 3. Forzar actualización de la tabla local
            self.ctrl.actualizar_vistas()