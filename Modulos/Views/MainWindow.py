import sys
import os
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QMessageBox,
    QFileDialog 
)
from PySide6.QtCore import Qt, Signal

from Modulos.Controllers.UsuarioController import ControladorUsuario
from Modulos.Controllers.InsumoController import ControladorInsumo
from Modulos.Controllers.LibroController import ControladorLibro
from Modulos.Controllers.PrestamoController import ControladorPrestamo
from Modulos.Controllers.ParametroController import ControladorParametro

from Modulos.Views.UsuarioViews import VentanaEmergenciaRecuperacion

class VentanaPrincipal(QMainWindow):
    def __init__(self, rol='invitado'):
        super().__init__()
        self.rol = rol
        self.setWindowTitle("Sistema de Gestión de Biblioteca (MATEO11-15)")
        self.setGeometry(100, 100, 1024, 600)
        
        self.ctrl_param = ControladorParametro()
        self.ctrl_usuario = ControladorUsuario()
        self.ctrl_insumo = ControladorInsumo()
        self.ctrl_libro = ControladorLibro() 
        self.ctrl_prestamo = ControladorPrestamo()
        
        if hasattr(self.ctrl_usuario, 'datos_actualizados'):
            self.ctrl_usuario.datos_actualizados.connect(lambda: self.cambiar_pagina(0))
        
        self.ctrl_libro.libro_guardado.connect(self.ctrl_insumo.cargar_datos)
        self.ctrl_insumo.datos_actualizados.connect(self.ctrl_libro.cargar_datos)

        widget_principal = QWidget()
        layout_principal = QHBoxLayout(widget_principal)
        self.setCentralWidget(widget_principal)
        
        layout_menu = QVBoxLayout()
        layout_menu.setSpacing(10)
        self.btn_usuarios = QPushButton("Usuarios")
        self.btn_items = QPushButton("Insumos")
        self.btn_libros = QPushButton("Libros (Clase)")
        self.btn_prestamos = QPushButton("Préstamos")
        self.btn_params = QPushButton("Parámetros")
        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setObjectName("SecondaryButton")
        
        self.botones_menu = [self.btn_usuarios, self.btn_items, self.btn_libros, self.btn_prestamos, self.btn_params]

        for btn in self.botones_menu:
            btn.setMinimumHeight(45)
            layout_menu.addWidget(btn)
        layout_menu.addStretch()
        layout_menu.addWidget(self.btn_exportar)
        
        contenedor_menu = QWidget()
        contenedor_menu.setLayout(layout_menu)
        contenedor_menu.setFixedWidth(180)
        layout_principal.addWidget(contenedor_menu)
        
        self.pila_central = QStackedWidget()
        self.pila_central.addWidget(self.ctrl_usuario.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_insumo.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_libro.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_prestamo.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_param.obtener_widget_vista())
        layout_principal.addWidget(self.pila_central, 1)
        
        self.pila_derecha = QStackedWidget()
        self.pila_derecha.addWidget(self.ctrl_usuario.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_insumo.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_libro.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_prestamo.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_param.obtener_widget_formulario())
        
        self.pila_derecha.setFixedWidth(280)
        layout_principal.addWidget(self.pila_derecha)
        
        self.btn_usuarios.clicked.connect(lambda: self.cambiar_pagina(0))
        self.btn_items.clicked.connect(lambda: self.cambiar_pagina(1))
        self.btn_libros.clicked.connect(lambda: self.cambiar_pagina(2))
        self.btn_prestamos.clicked.connect(lambda: self.cambiar_pagina(3))
        self.btn_params.clicked.connect(lambda: self.cambiar_pagina(4))
        self.btn_exportar.clicked.connect(self.exportar_datos)

        # === CONEXIÓN ESPECIAL PARA USUARIOS ===
        self._conectar_guardado_usuarios()

        roles_autorizados = ['Bibliotecario', 'admin', 'Director']
        if self.rol not in roles_autorizados:
            self.pila_derecha.hide()
            self.btn_params.hide()
            
        self.cambiar_pagina(0) 

    def _conectar_guardado_usuarios(self):
        try:
            self.ctrl_usuario.vista.btn_guardar.clicked.disconnect()
        except:
            pass
        self.ctrl_usuario.vista.btn_guardar.clicked.connect(self._handle_guardado_usuario)

    def _handle_guardado_usuario(self):
        """Solo llama al controlador. La ventana de 12 palabras se muestra SOLO desde el Controller."""
        self.ctrl_usuario.manejar_guardado()
        # ←←← YA NO CREAMOS NINGUNA VENTANA AQUÍ
        # La ventana limpia (con parent=None) se muestra desde el Controller

    # === EL RESTO ES IGUAL AL QUE YA TENÍAS ===
    def actualizar_resaltado_menu(self, indice):
        if not (0 <= indice < len(self.botones_menu)): return
        for i, btn in enumerate(self.botones_menu):
            if i == indice: btn.setProperty("class", "ActiveMenuButton")
            else: btn.setProperty("class", "MenuButton")
            btn.style().polish(btn)

    def cambiar_pagina(self, indice):
        self.actualizar_resaltado_menu(indice)
        self.pila_central.setCurrentIndex(indice)
        self.pila_derecha.setCurrentIndex(indice)
        
        controlador = self.obtener_controlador_por_indice(indice)
        if controlador:
            if hasattr(controlador, 'cargar_datos'):
                controlador.cargar_datos()
            if hasattr(controlador, 'reiniciar_visibilidad_formulario'):
                controlador.reiniciar_visibilidad_formulario()
            widget_actual = self.pila_central.currentWidget()
            if widget_actual:
                widget_actual.update()
                widget_actual.repaint()
                widget_actual.adjustSize()

    def obtener_controlador_por_indice(self, indice):
        controladores = [self.ctrl_usuario, self.ctrl_insumo, self.ctrl_libro, self.ctrl_prestamo, self.ctrl_param]
        return controladores[indice] if 0 <= indice < len(controladores) else None

    def exportar_datos(self):
        if self.rol != 'Bibliotecario':
            QMessageBox.warning(self, "Acceso Denegado", "Solo los bibliotecarios pueden exportar.")
            return
        
        datos_para_exportar = {
            "Usuarios": self.ctrl_usuario.model.obtener_todos(),
            "Insumos": self.ctrl_insumo.obtener_todos(),
            "Libros": self.ctrl_libro.obtener_todos(),
            "Préstamos": self.ctrl_prestamo.obtener_todos(),
        }

        marca_tiempo = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        nombre_archivo_defecto = f'Exportacion_Biblioteca_{marca_tiempo}.xlsx'
        ruta_archivo, _ = QFileDialog.getSaveFileName(self, "Guardar", nombre_archivo_defecto, "Excel (*.xlsx)")

        if not ruta_archivo: return
        try:
            with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as escritor:
                for nombre_hoja, datos in datos_para_exportar.items():
                    if datos: pd.DataFrame(datos).to_excel(escritor, sheet_name=nombre_hoja, index=False)
            QMessageBox.information(self, "Éxito", f"Exportado a:\n{ruta_archivo}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando: {e}")