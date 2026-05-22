import sys
import os
import pandas as pd
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt

from Modulos.Controllers.UsuarioController import ControladorUsuario
from Modulos.Controllers.InsumoController import ControladorInsumo
from Modulos.Controllers.LibroController import ControladorLibro
from Modulos.Controllers.PrestamoController import ControladorPrestamo
from Modulos.Controllers.ParametroController import ControladorParametro

class VentanaPrincipal(QMainWindow):
    def __init__(self, rol='invitado'):
        super().__init__()
        self.rol = rol
        # Actualización de nombre del proyecto según el registro formal
        self.setWindowTitle("Sistema de Gestión de Biblioteca (Cenizas De Alejandría)")
        self.setGeometry(100, 100, 1024, 600)

        # Controladores
        self.ctrl_param = ControladorParametro()
        self.ctrl_usuario = ControladorUsuario()
        self.ctrl_insumo = ControladorInsumo()
        self.ctrl_libro = ControladorLibro()
        self.ctrl_prestamo = ControladorPrestamo()

        # Lista universal para gestión de estados
        self.controladores = [
            self.ctrl_usuario, self.ctrl_insumo, 
            self.ctrl_libro, self.ctrl_prestamo, self.ctrl_param
        ]

        # ==================== UI ====================
        widget_principal = QWidget()
        layout_principal = QHBoxLayout(widget_principal)
        self.setCentralWidget(widget_principal)

        # Menú lateral
        layout_menu = QVBoxLayout()
        layout_menu.setSpacing(10)

        self.btn_usuarios = QPushButton("Usuarios")
        self.btn_items = QPushButton("Insumos")
        self.btn_libros = QPushButton("Libros (Clase)")
        self.btn_prestamos = QPushButton("Préstamos")
        self.btn_params = QPushButton("Parámetros")
        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setObjectName("SecondaryButton")

        self.botones_menu = [self.btn_usuarios, self.btn_items, self.btn_libros,
                             self.btn_prestamos, self.btn_params]

        for btn in self.botones_menu:
            btn.setMinimumHeight(45)
            layout_menu.addWidget(btn)

        layout_menu.addStretch()
        layout_menu.addWidget(self.btn_exportar)

        contenedor_menu = QWidget()
        contenedor_menu.setLayout(layout_menu)
        contenedor_menu.setFixedWidth(180)
        layout_principal.addWidget(contenedor_menu)

        # Pilas
        self.pila_central = QStackedWidget()
        self.pila_central.addWidget(self.ctrl_usuario.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_insumo.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_libro.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_prestamo.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_param.obtener_widget_vista())

        self.pila_derecha = QStackedWidget()
        self.pila_derecha.addWidget(self.ctrl_usuario.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_insumo.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_libro.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_prestamo.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_param.obtener_widget_formulario())

        self.pila_derecha.setFixedWidth(280)

        layout_principal.addWidget(self.pila_central, 1)
        layout_principal.addWidget(self.pila_derecha)

        # Conexiones de Navegación
        self.btn_usuarios.clicked.connect(lambda: self.cambiar_pagina(0))
        self.btn_items.clicked.connect(lambda: self.cambiar_pagina(1))
        self.btn_libros.clicked.connect(lambda: self.cambiar_pagina(2))
        self.btn_prestamos.clicked.connect(lambda: self.cambiar_pagina(3))
        self.btn_params.clicked.connect(lambda: self.cambiar_pagina(4))

        self.btn_exportar.clicked.connect(self.exportar_datos)

        # Conexiones Maestras
        self._conectar_guardado_usuarios()
        self._conectar_senales_recarga()

        # Restricciones por Rol
        if self.rol not in ['Bibliotecario', 'admin', 'Director']:
            self.pila_derecha.hide()
            self.btn_params.hide()

        self.cambiar_pagina(0)

    def _conectar_guardado_usuarios(self):
        """Desconecta señales previas y asegura que el controlador gestione el flujo"""
        try:
            self.ctrl_usuario.vista.btn_guardar.clicked.disconnect()
        except:
            pass
        self.ctrl_usuario.vista.btn_guardar.clicked.connect(self._handle_guardado_usuario)

    def _handle_guardado_usuario(self):
        """Intermediario: reinicia visibilidad tras éxito en el guardado"""
        resultado = self.ctrl_usuario.manejar_guardado()
        if resultado is True:
            self.ctrl_usuario.limpiar_formulario()
            self.ctrl_usuario.reiniciar_visibilidad_formulario()
            self.recargar_todo()

    def _conectar_senales_recarga(self):
        """Sincronización cruzada entre controladores"""
        if hasattr(self.ctrl_usuario, 'datos_actualizados'):
            self.ctrl_usuario.datos_actualizados.connect(self.recargar_todo)
        if hasattr(self.ctrl_libro, 'libro_guardado'):
            self.ctrl_libro.libro_guardado.connect(self.recargar_todo)
        if hasattr(self.ctrl_insumo, 'datos_actualizados'):
            self.ctrl_insumo.datos_actualizados.connect(self.recargar_todo)
        if hasattr(self.ctrl_param, 'parametro_guardado'):
            self.ctrl_param.parametro_guardado.connect(self.recargar_todo)

    def recargar_todo(self):
        """Refresca tablas y combos en todos los módulos"""
        for ctrl in self.controladores:
            if hasattr(ctrl, 'cargar_datos'):
                try: ctrl.cargar_datos()
                except: pass
            elif hasattr(ctrl, 'cargar_datos_tabla'):
                try: ctrl.cargar_datos_tabla()
                except: pass

            if hasattr(ctrl, 'cargar_combos'):
                try: ctrl.cargar_combos()
                except: pass
            
            if ctrl == self.ctrl_libro and hasattr(ctrl.vista, 'actualizar_combos'):
                try: ctrl.vista.actualizar_combos(self.ctrl_param)
                except: pass

        if self.pila_central.currentWidget():
            self.pila_central.currentWidget().update()
        if self.pila_derecha.isVisible() and self.pila_derecha.currentWidget():
            self.pila_derecha.currentWidget().update()

    def cambiar_pagina(self, indice):
        """Limpia la UI y asegura que los formularios de usuario se escondan al navegar"""
        for ctrl in self.controladores:
            # Esta función es la que esconde los campos de edición/creación
            if hasattr(ctrl, 'reiniciar_visibilidad_formulario'):
                ctrl.reiniciar_visibilidad_formulario()
            elif hasattr(ctrl, 'vista') and hasattr(ctrl.vista, 'limpiar_interfaz'):
                try: ctrl.vista.limpiar_interfaz()
                except: pass

        self.actualizar_resaltado_menu(indice)
        self.pila_central.setCurrentIndex(indice)
        self.pila_derecha.setCurrentIndex(indice)
        self.recargar_todo()

    def actualizar_resaltado_menu(self, indice):
        if not (0 <= indice < len(self.botones_menu)): return
        for i, btn in enumerate(self.botones_menu):
            btn.setProperty("class", "ActiveMenuButton" if i == indice else "MenuButton")
            btn.style().polish(btn)

    def exportar_datos(self):
        if self.rol != 'Bibliotecario':
            QMessageBox.warning(self, "Acceso Denegado", "Solo los bibliotecarios pueden exportar.")
            return
        self.recargar_todo()
        datos_para_exportar = {
            "Usuarios": self.ctrl_usuario.model.obtener_todos() if hasattr(self.ctrl_usuario, 'model') else [],
            "Insumos": self.ctrl_insumo.obtener_todos() if hasattr(self.ctrl_insumo, 'obtener_todos') else [],
            "Libros": self.ctrl_libro.obtener_todos() if hasattr(self.ctrl_libro, 'obtener_todos') else [],
        }
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Exportación", 
            f'Export_Lib_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx', "Excel (*.xlsx)"
        )
        if ruta_archivo:
            try:
                with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as escritor:
                    for hoja, datos in datos_para_exportar.items():
                        if datos: pd.DataFrame(datos).to_excel(escritor, sheet_name=hoja, index=False)
                QMessageBox.information(self, "Éxito", "Datos exportados correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error exportando: {e}")