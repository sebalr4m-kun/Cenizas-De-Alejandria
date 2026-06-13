import sys
import os
import json
import pandas as pd
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget,
    QMessageBox, QFileDialog, QApplication
)
from PySide6.QtCore import Qt

from Modulos.Controllers.UsuarioController import ControladorUsuario
from Modulos.Controllers.InsumoController import ControladorInsumo
from Modulos.Controllers.LibroController import ControladorLibro
from Modulos.Controllers.PrestamoController import ControladorPrestamo
from Modulos.Controllers.ParametroController import ControladorParametro
from Modulos.Config import Conexion

class VentanaPrincipal(QMainWindow):
    def __init__(self, pasaporte=None):
        super().__init__()
        
        # Extracción y decodificación del Pasaporte de Sesión
        self.pasaporte = pasaporte if pasaporte else {
            'id_usuario': None, 'nombre': 'Invitado', 'rol': 'invitado', 
            'admitido': False, 'permisos': {}
        }
        self.id_usuario = self.pasaporte.get('id_usuario')
        self.nombre_usuario = self.pasaporte.get('nombre')
        self.rol = self.pasaporte.get('rol')
        self.admitido = self.pasaporte.get('admitido')
        self.permisos = self.pasaporte.get('permisos', {})
        self.conexion = Conexion()

        self.setWindowTitle(f"Sistema de Gestión de Biblioteca (Cenizas De Alejandría) | Usuario: {self.nombre_usuario}")
        self.setGeometry(100, 100, 1024, 600)

        # Controladores
        self.ctrl_param = ControladorParametro()
        self.ctrl_usuario = ControladorUsuario()
        
        # INYECCIÓN DE SESIÓN: Transferimos el pasaporte de seguridad al controlador
        self.ctrl_usuario.establecer_sesion_actual(self.pasaporte)

        self.ctrl_insumo = ControladorInsumo()
        self.ctrl_libro = ControladorLibro()
        self.ctrl_prestamo = ControladorPrestamo()

        self.controladores = [
            self.ctrl_usuario, self.ctrl_insumo, 
            self.ctrl_libro, self.ctrl_prestamo, self.ctrl_param
        ]

        self.mapa_modulos = ["Usuarios", "Insumos", "Libros", "Préstamos", "Parámetros"]

        # ==================== UI ====================
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

        # Conexiones
        self.btn_usuarios.clicked.connect(lambda: self.cambiar_pagina(0))
        self.btn_items.clicked.connect(lambda: self.cambiar_pagina(1))
        self.btn_libros.clicked.connect(lambda: self.cambiar_pagina(2))
        self.btn_prestamos.clicked.connect(lambda: self.cambiar_pagina(3))
        self.btn_params.clicked.connect(lambda: self.cambiar_pagina(4))
        self.btn_exportar.clicked.connect(self.exportar_datos)

        # Conexiones Maestras
        self._conectar_guardado_usuarios()
        self._conectar_senales_recarga()

        # Despliegue de Jerarquía de Acceso RBAC blindado
        try:
            self._aplicar_restricciones_menu()
        except Exception as e:
            print(f"[CRÍTICO] Fallo al aplicar restricciones: {e}")

    def _obtener_permisos_seguro(self, nombre_modulo):
        """
        Solución definitiva al problema de mayúsculas/minúsculas y acentos del JSON.
        Mapea exactamente lo que llega de la BD sin importar cómo esté escrito.
        """
        mapeo_db = {
            "Usuarios": "usuarios",
            "Insumos": "insumos",
            "Libros": "libros",
            "Préstamos": "prestamos", 
            "Parámetros": "parámetros" # json.loads interpreta \u00e1 como á
        }
        clave_ideal = mapeo_db.get(nombre_modulo, nombre_modulo.lower())
        
        # Intento 1: Coincidencia exacta con el diccionario
        if clave_ideal in self.permisos:
            return self.permisos[clave_ideal]
            
        # Intento 2: Búsqueda dinámica tolerante a errores ortográficos
        for k, v in self.permisos.items():
            k_norm = k.lower().replace("á", "a").replace("é", "e")
            clave_norm = clave_ideal.lower().replace("á", "a").replace("é", "e")
            if k_norm == clave_norm:
                return v
                
        return {}

    def _aplicar_restricciones_menu(self):
        if self.rol == 'admin':
            self.cambiar_pagina(0)
            return

        al_menos_uno_visible = False
        primer_indice_visible = 0

        # Iterar mapeando de forma segura
        for i, modulo in enumerate(self.mapa_modulos):
            perms = self._obtener_permisos_seguro(modulo)
            puede_ver = perms.get('ver', False)
            self.botones_menu[i].setVisible(puede_ver)
            
            if puede_ver and not al_menos_uno_visible:
                al_menos_uno_visible = True
                primer_indice_visible = i

        puede_exportar = all([
            self._obtener_permisos_seguro('Usuarios').get('ver', False),
            self._obtener_permisos_seguro('Insumos').get('ver', False),
            self._obtener_permisos_seguro('Libros').get('ver', False)
        ])
        self.btn_exportar.setVisible(puede_exportar)

        if al_menos_uno_visible:
            self.cambiar_pagina(primer_indice_visible)
        else:
            self.pila_central.hide()
            self.pila_derecha.hide()

    def _verificar_integridad_sesion(self):
        if self.rol in ['admin', 'invitado'] or not self.id_usuario:
            return 
        
        bd = self.conexion.obtener_conexion()
        if not bd: return
        
        bd.commit() 
        cursor = bd.cursor(dictionary=True)
        expulsar = False
        razon = ""
        
        try:
            consulta = '''
                SELECT u.estado_cuenta, p.permisos, p.admitido 
                FROM usuarios u
                JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                WHERE u.id_usuario = %s
            '''
            cursor.execute(consulta, (self.id_usuario,))
            usuario_db = cursor.fetchone()
            
            if not usuario_db:
                expulsar = True
                razon = "Su cuenta ha sido eliminada del sistema físico."
            elif usuario_db['estado_cuenta'] != 'ACTIVA':
                expulsar = True
                razon = "Su cuenta ha sido suspendida administrativamente."
            elif not usuario_db['admitido'] and self.admitido:
                expulsar = True
                razon = "Su tipo de cuenta ha perdido la designación de admisión."
            else:
                try:
                    permisos_db_dict = json.loads(usuario_db['permisos']) if usuario_db['permisos'] else {}
                except Exception:
                    permisos_db_dict = {}
                    
                # Evalúa diferencias ignorando el orden interno de Python
                if self.permisos != permisos_db_dict:
                    expulsar = True
                    razon = "Sus privilegios de acceso al sistema han sido modificados remotamente."
                    
        except Exception:
            pass
        finally:
            cursor.close()
            
        if expulsar:
            QMessageBox.critical(self, "Sesión Terminada por Seguridad", f"{razon}\n\nPor favor, vuelva a iniciar sesión.")
            try:
                QApplication.quit()
                os.execl(sys.executable, sys.executable, *sys.argv)
            except Exception:
                sys.exit(1) # Cierre forzado seguro si el OS bloquea el execl

    def _conectar_guardado_usuarios(self):
        try:
            self.ctrl_usuario.vista.btn_guardar.clicked.disconnect()
        except Exception:
            pass
            
        try:
            self.ctrl_usuario.vista.btn_guardar.clicked.connect(self._handle_guardado_usuario)
        except Exception:
            pass

    def _handle_guardado_usuario(self):
        resultado = self.ctrl_usuario.manejar_guardado()
        if resultado is True:
            self.ctrl_usuario.limpiar_formulario()
            self.ctrl_usuario.reiniciar_visibilidad_formulario()
            self.recargar_todo()

    def _conectar_senales_recarga(self):
        if hasattr(self.ctrl_usuario, 'datos_actualizados'):
            self.ctrl_usuario.datos_actualizados.connect(self.recargar_todo)
        if hasattr(self.ctrl_libro, 'libro_guardado'):
            self.ctrl_libro.libro_guardado.connect(self.recargar_todo)
        if hasattr(self.ctrl_insumo, 'datos_actualizados'):
            self.ctrl_insumo.datos_actualizados.connect(self.recargar_todo)
        if hasattr(self.ctrl_param, 'parametro_guardado'):
            self.ctrl_param.parametro_guardado.connect(self.recargar_todo)

    def recargar_todo(self):
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
            
            if ctrl == self.ctrl_libro and hasattr(ctrl, 'vista') and hasattr(ctrl.vista, 'actualizar_combos'):
                try: ctrl.vista.actualizar_combos(self.ctrl_param)
                except: pass

        if self.pila_central.currentWidget():
            self.pila_central.currentWidget().update()
        if self.pila_derecha.isVisible() and self.pila_derecha.currentWidget():
            self.pila_derecha.currentWidget().update()

        self._verificar_integridad_sesion()

    def cambiar_pagina(self, indice):
        for ctrl in self.controladores:
            if hasattr(ctrl, 'reiniciar_visibilidad_formulario'):
                ctrl.reiniciar_visibilidad_formulario()
            elif hasattr(ctrl, 'vista') and hasattr(ctrl.vista, 'limpiar_interfaz'):
                try: ctrl.vista.limpiar_interfaz()
                except: pass

        self.actualizar_resaltado_menu(indice)
        self.pila_central.setCurrentIndex(indice)
        self.pila_derecha.setCurrentIndex(indice)

        if self.rol == 'admin':
            self.pila_derecha.show()
        else:
            modulo_actual = self.mapa_modulos[indice]
            perms = self._obtener_permisos_seguro(modulo_actual)
            puede_editar_o_crear = perms.get('editar', False) or perms.get('crear', False) or perms.get('borrar', False)
            
            if puede_editar_o_crear:
                self.pila_derecha.show()
            else:
                self.pila_derecha.hide()

        self.recargar_todo()

    def actualizar_resaltado_menu(self, indice):
        if not (0 <= indice < len(self.botones_menu)): return
        for i, btn in enumerate(self.botones_menu):
            btn.setProperty("class", "ActiveMenuButton" if i == indice else "MenuButton")
            btn.style().polish(btn)

    def exportar_datos(self):
        if self.rol != 'admin':
            puede_exportar = all([
                self._obtener_permisos_seguro('Usuarios').get('ver', False),
                self._obtener_permisos_seguro('Insumos').get('ver', False),
                self._obtener_permisos_seguro('Libros').get('ver', False)
            ])
            if not puede_exportar:
                QMessageBox.warning(self, "Acceso Denegado", "Se requiere permiso de lectura en Usuarios, Insumos y Libros para generar el reporte general.")
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