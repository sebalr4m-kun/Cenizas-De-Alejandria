from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

class VistaTablaParametro(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Parámetros")) 
        
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Todos", "Tipo Usuario", "Tipo Insumo", "Autor", "Editorial", "Categoría", "Género"])
        layout.addWidget(self.combo_filtro)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Rubro", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)

class FormularioParametro(QWidget):
    def __init__(self, controlador):
        super().__init__()
        self.ctrl = controlador
        
        layout_principal = QVBoxLayout(self)
        
        # Botones de modo (siempre visibles)
        layout_modo = QHBoxLayout()
        self.btn_crear = QPushButton("Crear")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setChecked(True)
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setCheckable(True)
        
        layout_modo.addWidget(self.btn_crear)
        layout_modo.addWidget(self.btn_editar)
        layout_principal.addLayout(layout_modo)

        # ==================== CONTENEDOR OCULTABLE ====================
        self.widget_contenido = QWidget()
        self.layout_contenido = QVBoxLayout(self.widget_contenido)
        
        self.layout_contenido.addWidget(QLabel("Rubro"))
        self.combo_rubro = QComboBox()
        self.combo_rubro.addItems(["Tipo Usuario", "Tipo Insumo", "Autor", "Editorial", "Categoría", "Género"]) 
        self.layout_contenido.addWidget(self.combo_rubro)
        
        self.layout_contenido.addWidget(QLabel("Nombre"))
        self.entrada_nombre = QLineEdit()
        self.layout_contenido.addWidget(self.entrada_nombre)
        
        self.etiqueta_estado = QLabel("Estado")
        self.layout_contenido.addWidget(self.etiqueta_estado)
        
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["ACTIVO", "INACTIVO"]) 
        self.layout_contenido.addWidget(self.combo_estado)
        
        layout_principal.addWidget(self.widget_contenido)
        layout_principal.addStretch()
        
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("ActionButton")
        layout_principal.addWidget(self.btn_guardar)

        # Estado inicial: todo oculto
        self.widget_contenido.hide()

    def establecer_modo_ui(self, modo):
        """Este método es llamado desde el controlador"""
        if modo == 'crear':
            self.btn_crear.setChecked(True)
            self.btn_editar.setChecked(False)
            self.etiqueta_estado.hide()
            self.combo_estado.hide()
            self.widget_contenido.show()
        else:  # editar
            self.btn_crear.setChecked(False)
            self.btn_editar.setChecked(True)
            self.etiqueta_estado.show()
            self.combo_estado.show()
            self.widget_contenido.show()