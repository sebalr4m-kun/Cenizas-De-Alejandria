from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt


class VistaLibro:
    def __init__(self, controlador):
        self.ctrl = controlador
        self.widget_vista = None
        self.tabla = None

    def construir_vista_catalogo(self):
        self.widget_vista = QWidget()
        layout = QVBoxLayout(self.widget_vista)
        
        titulo = QLabel("Catálogo de Libros")
        titulo.setProperty("isTitle", True) 
        layout.addWidget(titulo) 
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Título", "ISBN", "Autor", "Disponible", "Stock Total"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)
        
        self.ctrl.tabla = self.tabla
        
        # VERSIÓN ULTRA SIMPLE - SOLO GUIONES
        self.tabla.setRowCount(0)
        for i in range(5):   # 5 filas de prueba
            self.tabla.insertRow(i)
            for col in range(5):
                self.tabla.setItem(i, col, QTableWidgetItem("---"))

        print("=== VISTA LIBRO: Se cargaron 5 filas con guiones ===")
        
        return self.widget_vista

    # Métodos vacíos para no romper nada
    def construir_formulario(self, ctrl_param):
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        w = QWidget()
        QVBoxLayout(w).addWidget(QLabel("Formulario de Libro (deshabilitado temporalmente)"))
        return w

    def actualizar_combos(self, ctrl_param):
        pass

    def establecer_modo(self, modo, inicial=False):
        pass

    def limpiar_formulario(self):
        pass

    def filtrar_tabla(self, texto):
        pass

    def intentar_cargar_edicion(self):
        pass

    def procesar_guardado(self):
        if hasattr(self.ctrl, 'libro_guardado'):
            self.ctrl.libro_guardado.emit()