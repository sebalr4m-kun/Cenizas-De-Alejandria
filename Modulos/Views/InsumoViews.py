from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
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
        
        self.entrada_busqueda = QLineEdit(placeholderText="Filtrar...")
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla) 
        layout.addWidget(self.entrada_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Título", "Clave RUNA", "Categoría", "Estado", "Adquisición"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        self.tabla.setRowCount(0)
        for i, d in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(d['Titulo']))
            self.tabla.setItem(i, 1, QTableWidgetItem(d['Clave RUNA']))
            self.tabla.setItem(i, 2, QTableWidgetItem(d['Categoria']))
            self.tabla.setItem(i, 3, QTableWidgetItem(d['Estado']))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(d['Adquisicion'])))

class FormularioInsumo(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        self.modo = 'crear'
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        
        layout_principal.addWidget(QLabel("Acciones"))
        layout_modo = QHBoxLayout()
        self.btn_crear = QPushButton("Crear Nuevo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setChecked(True)
        self.btn_crear.clicked.connect(lambda: self.establecer_modo('crear'))
        
        self.btn_editar = QPushButton("Editar Existente")
        self.btn_editar.setCheckable(True)
        self.btn_editar.clicked.connect(lambda: self.establecer_modo('editar'))
        
        layout_modo.addWidget(self.btn_crear)
        layout_modo.addWidget(self.btn_editar)
        layout_principal.addLayout(layout_modo)
        
        self.widget_contenido = QWidget()
        layout_contenido = QVBoxLayout(self.widget_contenido)

        self.etiqueta_runa = QLabel("Clave RUNA (Auto-Generada)")
        layout_contenido.addWidget(self.etiqueta_runa)
        self.entrada_runa = QLineEdit()
        self.entrada_runa.setPlaceholderText("Ingrese Clave RUNA para buscar")
        self.entrada_runa.textChanged.connect(self.intentar_cargar_edicion)
        layout_contenido.addWidget(self.entrada_runa)

        layout_contenido.addWidget(QLabel("Nombre"))
        self.entrada_nombre = QLineEdit()
        layout_contenido.addWidget(self.entrada_nombre)
        
        layout_contenido.addWidget(QLabel("Categoría"))
        self.combo_cat = QComboBox()
        layout_contenido.addWidget(self.combo_cat)
        
        self.etiqueta_fecha = QLabel("Fecha Adquisición") 
        layout_contenido.addWidget(self.etiqueta_fecha)
        self.entrada_fecha = QDateEdit(calendarPopup=True)
        self.entrada_fecha.setDisplayFormat("yyyy-MM-dd")
        self.entrada_fecha.setDate(QDate.currentDate())
        layout_contenido.addWidget(self.entrada_fecha)
        
        self.etiqueta_estado = QLabel("Estado")
        layout_contenido.addWidget(self.etiqueta_estado)
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["DISPONIBLE", "PRESTADO", "MANTENIMIENTO", "SUSPENDIDA", "ELIMINADA"])
        layout_contenido.addWidget(self.combo_estado)
        
        layout_contenido.addStretch()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.clicked.connect(self.ejecutar_guardado)
        layout_contenido.addWidget(self.btn_guardar)
        
        layout_principal.addWidget(self.widget_contenido)
        layout_principal.addStretch() 
        
        self.widget_contenido.hide()
        self.establecer_modo('crear', inicial=True)

    def establecer_modo(self, modo, inicial=False):
        self.modo = modo
        es_crear = (modo == 'crear')
        
        self.btn_crear.setChecked(es_crear)
        self.btn_editar.setChecked(not es_crear)
        
        self.etiqueta_runa.setText("Clave RUNA (Auto-Generada)" if es_crear else "Clave RUNA (ID Único)")
        self.entrada_runa.setReadOnly(es_crear)
        if es_crear: self.entrada_runa.hide()
        else: self.entrada_runa.show()
            
        self.entrada_nombre.setReadOnly(False)
        self.combo_cat.setEnabled(True)
        
        self.etiqueta_estado.setVisible(not es_crear)
        self.combo_estado.setVisible(not es_crear)
        self.etiqueta_fecha.setVisible(not es_crear)
        self.entrada_fecha.setVisible(not es_crear)

        self.limpiar()
        if not inicial:
            self.widget_contenido.show()

    def limpiar(self):
        self.entrada_runa.clear()
        self.entrada_nombre.clear()
        self.entrada_fecha.setDate(QDate.currentDate())
        if self.combo_cat.count() > 0:
            self.combo_cat.setCurrentIndex(0)
        self.combo_estado.setCurrentText("DISPONIBLE")

    def intentar_cargar_edicion(self):
        if self.modo != 'editar': return
        clave_runa = self.entrada_runa.text().strip()
        if not clave_runa: return
        
        item = self.ctrl.obtener_uno(clave_runa) 
        if item:
            self.entrada_nombre.setText(item.get('titulo', ''))
            id_tipo = item.get('id_tipo_insumo')
            indice = self.combo_cat.findData(id_tipo)
            if indice != -1: self.combo_cat.setCurrentIndex(indice)
            
            fecha_adquisicion = item.get('fecha_adquisicion')
            if isinstance(fecha_adquisicion, datetime):
                fecha_bd_str = fecha_adquisicion.strftime("%Y-%m-%d")
                fecha_bd = QDate.fromString(fecha_bd_str, "yyyy-MM-dd")
                self.entrada_fecha.setDate(fecha_bd)
            
            estado_ui = 'SUSPENDIDA' if item['estado'] == 'INACTIVA' else item['estado']
            self.combo_estado.setCurrentText(estado_ui)
            
            if self.ctrl.es_libro(id_tipo):
                self.entrada_nombre.setReadOnly(True)
                self.combo_cat.setEnabled(False)
                self.entrada_fecha.setReadOnly(True)
                QMessageBox.information(self, "Libro Detectado", "Este insumo es un Libro. Solo puede editar su Estado.")
            else:
                self.entrada_nombre.setReadOnly(False)
                self.combo_cat.setEnabled(True)
                self.entrada_fecha.setReadOnly(False)

    def ejecutar_guardado(self):
        # Recolectar datos de la vista
        datos = {
            'modo': self.modo,
            'titulo': self.entrada_nombre.text().strip(),
            'id_tipo': self.combo_cat.currentData(),
            'clave_runa': self.entrada_runa.text().strip(),
            'estado_ui': self.combo_estado.currentText(),
            'fecha_ui': self.entrada_fecha.date().toString("yyyy-MM-dd")
        }
        self.ctrl.manejar_guardado(datos)