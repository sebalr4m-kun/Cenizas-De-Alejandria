import sys
import os
import json
import importlib

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget,
    QMessageBox, QApplication, QLabel, QHeaderView, QAbstractItemView, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt

from Modulos.Controllers.UsuarioController import ControladorUsuario
from Modulos.Controllers.InsumoController import ControladorInsumo
from Modulos.Controllers.LibroController import ControladorLibro
from Modulos.Controllers.PrestamoController import ControladorPrestamo 
from Modulos.Controllers.ParametroController import ControladorParametro
from Modulos.Config import Conexion

from Modulos.Auditorias import auditoria_global

class WidgetHistorialAuditorias(QWidget):
    """Vista de solo lectura para la trazabilidad y auditorías del sistema."""
    def __init__(self, conexion, parent=None):
        super().__init__(parent)
        self.conexion = conexion

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)

        lbl_titulo = QLabel("📜 Historial de Auditorías (Solo Lectura)")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout_principal.addWidget(lbl_titulo)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID Aud.", "Correo Electrónico", "Acción", "Módulo", "Elemento", "Fecha/Hora"])

        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch) 
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)

        layout_principal.addWidget(self.tabla)

    def cargar_datos(self):
        bd = self.conexion.obtener_conexion()
        if not bd: return
        try:
            cursor = bd.cursor(dictionary=True)
            consulta = '''
                SELECT a.id_auditoria, u.email AS correo, p.nombre_accion, a.modulo, a.elemento, a.fecha_hora 
                FROM auditorias a 
                LEFT JOIN param_acciones p ON a.id_accion = p.id_accion 
                LEFT JOIN usuarios u ON a.id_usuario = u.id_usuario
                ORDER BY a.fecha_hora DESC
            '''
            cursor.execute(consulta)
            registros = cursor.fetchall()

            self.tabla.setRowCount(0)
            for row_idx, reg in enumerate(registros):
                self.tabla.insertRow(row_idx)
                self.tabla.setItem(row_idx, 0, QTableWidgetItem(str(reg.get('id_auditoria', ''))))
                self.tabla.setItem(row_idx, 1, QTableWidgetItem(str(reg.get('correo', 'Desconocido'))))
                self.tabla.setItem(row_idx, 2, QTableWidgetItem(str(reg.get('nombre_accion', ''))))
                self.tabla.setItem(row_idx, 3, QTableWidgetItem(str(reg.get('modulo', ''))))
                self.tabla.setItem(row_idx, 4, QTableWidgetItem(str(reg.get('elemento', ''))))
                self.tabla.setItem(row_idx, 5, QTableWidgetItem(str(reg.get('fecha_hora', ''))))
        except Exception as e:
            print(f"[ERROR] Al cargar historial de auditorías: {e}")
        finally:
            cursor.close()

class VentanaPrincipal(QMainWindow):
    def __init__(self, pasaporte=None):
        super().__init__()

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

        auditoria_global.vincular_sesion(self.pasaporte)

        self.setWindowTitle(f"Sistema de Gestión de Biblioteca (Cenizas De Alejandría) | Usuario: {self.nombre_usuario}")
        self.setGeometry(100, 100, 1024, 600)

        self.colores_invertidos = False
        self.modo_estadisticas = False
        self.indice_modulo_actual = 0

        self.ctrl_param = ControladorParametro()
        self.ctrl_usuario = ControladorUsuario()
        self.ctrl_usuario.establecer_sesion_actual(self.pasaporte)
        self.ctrl_insumo = ControladorInsumo()
        self.ctrl_libro = ControladorLibro()
        self.ctrl_prestamo = ControladorPrestamo()

        self.controladores = [
            self.ctrl_usuario, self.ctrl_insumo, 
            self.ctrl_libro, self.ctrl_prestamo, self.ctrl_param
        ]

        self.mapa_modulos = ["Usuarios", "Insumos", "Libros", "Préstamos", "Parámetros"]
        self.vistas_estadisticas_cache = {}

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

        self.botones_menu = [self.btn_usuarios, self.btn_items, self.btn_libros,
                             self.btn_prestamos, self.btn_params]

        for btn in self.botones_menu:
            btn.setMinimumHeight(45)
            layout_menu.addWidget(btn)

        layout_menu.addStretch()

        self.btn_historial = QPushButton("Historial")
        self.btn_historial.setObjectName("SecondaryButton")
        self.btn_historial.setMinimumHeight(45)
        self.btn_historial.hide()
        layout_menu.addWidget(self.btn_historial)

        self.btn_estadisticas = QPushButton("Estadísticas")
        self.btn_estadisticas.setObjectName("SecondaryButton")
        self.btn_estadisticas.setMinimumHeight(45)
        layout_menu.addWidget(self.btn_estadisticas)

        contenedor_menu = QWidget()
        contenedor_menu.setLayout(layout_menu)
        contenedor_menu.setFixedWidth(180)
        layout_principal.addWidget(contenedor_menu)

        self.widget_historial = WidgetHistorialAuditorias(self.conexion)

        self.pila_central = QStackedWidget()
        self.pila_central.addWidget(self.ctrl_usuario.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_insumo.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_libro.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_prestamo.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_param.obtener_widget_vista())
        self.pila_central.addWidget(self.widget_historial) 

        self.pila_derecha = QStackedWidget()
        self.pila_derecha.addWidget(self.ctrl_usuario.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_insumo.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_libro.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_prestamo.obtener_widget_formulario(self.ctrl_param))
        self.pila_derecha.addWidget(self.ctrl_param.obtener_widget_formulario())

        self.pila_derecha.setFixedWidth(280)

        layout_principal.addWidget(self.pila_central, 1)
        layout_principal.addWidget(self.pila_derecha)

        self.btn_usuarios.clicked.connect(lambda: self.cambiar_pagina(0))
        self.btn_items.clicked.connect(lambda: self.cambiar_pagina(1))
        self.btn_libros.clicked.connect(lambda: self.cambiar_pagina(2))
        self.btn_prestamos.clicked.connect(lambda: self.cambiar_pagina(3))
        self.btn_params.clicked.connect(lambda: self.cambiar_pagina(4))

        self.btn_estadisticas.clicked.connect(self.alternar_modo_estadisticas)
        self.btn_historial.clicked.connect(self.mostrar_historial)

        self._conectar_guardado_usuarios()
        self._conectar_senales_recarga()

        try:
            self._aplicar_restricciones_menu()
        except Exception as e:
            print(f"[CRÍTICO] Fallo al aplicar restricciones: {e}")

    def _obtener_vista_estadisticas(self, modulo):
        """Carga dinámicamente la vista del controlador de estadísticas delegado con resolución polimórfica."""
        if modulo in self.vistas_estadisticas_cache:
            return self.vistas_estadisticas_cache[modulo]
        
        mapeo_modulos = {
            "Usuarios": ("Modulos.Controllers.UsuarioEstadisticas", "UsuarioEstadisticas"),
            "Parámetros": ("Modulos.Controllers.ParametroEstadisticas", "ParametroEstadisticas"),
            "Libros": ("Modulos.Controllers.LibroEstadisticas", "LibroEstadisticas"),
            "Insumos": ("Modulos.Controllers.InsumoEstadisticas", "InsumoEstadisticas"),
            "Préstamos": ("Modulos.Controllers.PrestamoEstadisticas", "PrestamoEstadisticas")
        }

        if modulo not in mapeo_modulos:
            return None

        ruta_import, nombre_clase = mapeo_modulos[modulo]
        try:
            mod = importlib.import_module(ruta_import)
            clase = getattr(mod, nombre_clase)

            # Intentar instanciar pasando la conexión o de forma predeterminada
            try:
                instancia = clase(self.conexion)
            except TypeError:
                try:
                    instancia = clase()
                except TypeError:
                    instancia = clase

            # Resolución polimórfica para extraer el QWidget correcto
            vista = None
            if hasattr(instancia, 'obtener_widget_vista') and callable(getattr(instancia, 'obtener_widget_vista')):
                vista = instancia.obtener_widget_vista()
            elif hasattr(instancia, 'obtener_vista') and callable(getattr(instancia, 'obtener_vista')):
                vista = instancia.obtener_vista()
            elif hasattr(instancia, 'vista'):
                vista = instancia.vista
            elif isinstance(instancia, QWidget):
                vista = instancia

            if vista is not None and isinstance(vista, QWidget):
                vista._controlador_estadisticas = instancia
                self.vistas_estadisticas_cache[modulo] = vista
                self.pila_central.addWidget(vista)
                return vista
            else:
                print(f"[ERROR] No se pudo resolver un QWidget válido para la clase de estadísticas {nombre_clase}")
                return None

        except (ImportError, ModuleNotFoundError, AttributeError) as e:
            print(f"[ERROR] Al cargar vista de estadísticas para {modulo}: {e}")
            return None

    def mostrar_historial(self):
        if not self.modo_estadisticas:
            return
        self.widget_historial.cargar_datos()
        self.pila_central.setCurrentWidget(self.widget_historial)

    def alternar_modo_estadisticas(self):
        self.modo_estadisticas = not self.modo_estadisticas
        self.alternar_colores()

        if self.modo_estadisticas:
            self.btn_estadisticas.setText("Modulos")
            self.btn_historial.show()
            self.pila_derecha.hide()
            self._mostrar_vista_estadisticas_actual()
        else:
            self.btn_estadisticas.setText("Estadísticas")
            self.btn_historial.hide()
            self.cambiar_pagina(self.indice_modulo_actual)

    def _mostrar_vista_estadisticas_actual(self):
        modulo_nombre = self.mapa_modulos[self.indice_modulo_actual]
        vista = self._obtener_vista_estadisticas(modulo_nombre)
        if vista:
            self.pila_central.setCurrentWidget(vista)
            ctrl = getattr(vista, '_controlador_estadisticas', vista)
            
            # Recorrer métodos estándar de actualización tanto en la vista como en su controlador
            for met in ['actualizar_vista_grafico', 'actualizar_grafico', 'cargar_datos', 'actualizar_datos', 'actualizar_combos']:
                if hasattr(vista, met) and callable(getattr(vista, met)):
                    try:
                        getattr(vista, met)()
                        break
                    except Exception as e:
                        print(f"[ERROR] Al ejecutar {met} en vista de {modulo_nombre}: {e}")
                elif hasattr(ctrl, met) and callable(getattr(ctrl, met)):
                    try:
                        getattr(ctrl, met)()
                        break
                    except Exception as e:
                        print(f"[ERROR] Al ejecutar {met} en controlador de {modulo_nombre}: {e}")

    def alternar_colores(self):
        self.colores_invertidos = self.modo_estadisticas
        if self.colores_invertidos:
            estilo_invertido = """
                QWidget { background-color: #121212; color: #ffffff; }
                QPushButton { background-color: #2c2c2c; color: #ffffff; border: 1px solid #7f8c8d; border-radius: 4px; }
                QPushButton:hover { background-color: #4a4a4a; }
                QPushButton#ActiveMenuButton { background-color: #555555; color: #ffffff; font-weight: bold; border-left: 4px solid #ffffff; }
                QLineEdit, QComboBox, QTableWidget, QListWidget { background-color: #1e1e1e; color: #ffffff; border: 1px solid #555555; }
                QHeaderView::section { background-color: #333333; color: #ffffff; border: 1px solid #555555; }
                QTableWidget::item:selected, QListWidget::item:selected { background-color: #34495e; color: #ffffff; }
            """
            self.setStyleSheet(estilo_invertido)
        else:
            self.setStyleSheet("")

    def _obtener_permisos_seguro(self, nombre_modulo):
        mapeo_db = {
            "Usuarios": "usuarios", "Insumos": "insumos",
            "Libros": "libros", "Préstamos": "prestamos", 
            "Parámetros": "parámetros" 
        }
        clave_ideal = mapeo_db.get(nombre_modulo, nombre_modulo.lower())
        if clave_ideal in self.permisos: return self.permisos[clave_ideal]
        for k, v in self.permisos.items():
            k_norm = k.lower().replace("á", "a").replace("é", "e")
            clave_norm = clave_ideal.lower().replace("á", "a").replace("é", "e")
            if k_norm == clave_norm: return v
        return {}

    def _aplicar_restricciones_menu(self):
        if self.rol == 'admin':
            self.cambiar_pagina(0)
            return
        al_menos_uno_visible = False
        primer_indice_visible = 0
        for i, modulo in enumerate(self.mapa_modulos):
            perms = self._obtener_permisos_seguro(modulo)
            puede_ver = perms.get('ver', False)
            self.botones_menu[i].setVisible(puede_ver)
            if puede_ver and not al_menos_uno_visible:
                al_menos_uno_visible = True
                primer_indice_visible = i
        if al_menos_uno_visible: self.cambiar_pagina(primer_indice_visible)
        else:
            self.pila_central.hide()
            self.pila_derecha.hide()

    def _verificar_integridad_sesion(self):
        if self.rol in ['admin', 'invitado'] or not self.id_usuario: return 
        bd = self.conexion.obtener_conexion()
        if not bd: return 
        bd.commit() 
        cursor = bd.cursor(dictionary=True)
        expulsar, razon = False, ""
        try:
            consulta = '''
                SELECT u.estado_cuenta, p.permisos, p.admitido 
                FROM usuarios u JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario WHERE u.id_usuario = %s
            '''
            cursor.execute(consulta, (self.id_usuario,))
            usuario_db = cursor.fetchone()
            if not usuario_db: expulsar, razon = True, "Su cuenta ha sido eliminada del sistema físico."
            elif usuario_db['estado_cuenta'] != 'ACTIVA': expulsar, razon = True, "Su cuenta ha sido suspendida administrativamente."
            elif not usuario_db['admitido'] and self.admitido: expulsar, razon = True, "Su tipo de cuenta ha perdido la designación de admisión."
            else:
                try: permisos_db_dict = json.loads(usuario_db['permisos']) if usuario_db['permisos'] else {}
                except Exception: permisos_db_dict = {}
                if self.permisos != permisos_db_dict: expulsar, razon = True, "Sus privilegios de acceso al sistema han sido modificados remotamente."
        except Exception: pass
        finally: cursor.close()

        if expulsar:
            auditoria_global.auditar_sesion(f"Cierre forzado: {razon}")
            QMessageBox.critical(self, "Sesión Terminada por Seguridad", f"{razon}\n\nPor favor, vuelva a iniciar sesión.")
            try: QApplication.quit(); os.execl(sys.executable, sys.executable, *sys.argv)
            except Exception: sys.exit(1)

    def _conectar_guardado_usuarios(self):
        try: self.ctrl_usuario.vista.btn_guardar.clicked.disconnect()
        except Exception: pass
        try: self.ctrl_usuario.vista.btn_guardar.clicked.connect(self._handle_guardado_usuario)
        except Exception: pass

    def _handle_guardado_usuario(self):
        resultado = self.ctrl_usuario.manejar_guardado()
        if resultado is True:
            self.ctrl_usuario.limpiar_formulario()
            self.ctrl_usuario.reiniciar_visibilidad_formulario()
            self.recargar_todo()

    def _conectar_senales_recarga(self):
        for ctrl in [self.ctrl_usuario, self.ctrl_libro, self.ctrl_insumo, self.ctrl_param, self.ctrl_prestamo]:
            if hasattr(ctrl, 'datos_actualizados'): ctrl.datos_actualizados.connect(self.recargar_todo)
        if hasattr(self.ctrl_libro, 'libro_guardado'): self.ctrl_libro.libro_guardado.connect(self.recargar_todo)
        if hasattr(self.ctrl_param, 'parametro_guardado'): self.ctrl_param.parametro_guardado.connect(self.recargar_todo)

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

        if self.pila_central.currentWidget(): self.pila_central.currentWidget().update()
        if self.pila_derecha.isVisible() and self.pila_derecha.currentWidget(): self.pila_derecha.currentWidget().update()
        self._verificar_integridad_sesion()

    def cambiar_pagina(self, indice):
        self.indice_modulo_actual = indice

        if self.modo_estadisticas:
            self.actualizar_resaltado_menu(indice)
            self._mostrar_vista_estadisticas_actual()
            self.pila_derecha.hide()
            return

        for ctrl in self.controladores:
            if hasattr(ctrl, 'reiniciar_visibilidad_formulario'): ctrl.reiniciar_visibilidad_formulario()
            elif hasattr(ctrl, 'vista') and hasattr(ctrl.vista, 'limpiar_interfaz'):
                try: ctrl.vista.limpiar_interfaz()
                except: pass

        self.actualizar_resaltado_menu(indice)
        self.pila_central.setCurrentIndex(indice)
        self.pila_derecha.setCurrentIndex(indice)

        if self.rol == 'admin': self.pila_derecha.show()
        else:
            modulo_actual = self.mapa_modulos[indice]
            perms = self._obtener_permisos_seguro(modulo_actual)
            puede_editar_o_crear = perms.get('editar', False) or perms.get('crear', False) or perms.get('borrar', False)
            if puede_editar_o_crear: self.pila_derecha.show()
            else: self.pila_derecha.hide()

        self.recargar_todo()

    def actualizar_resaltado_menu(self, indice):
        if not (0 <= indice < len(self.botones_menu)): return
        for i, btn in enumerate(self.botones_menu):
            btn.setProperty("class", "ActiveMenuButton" if i == indice else "MenuButton")
            btn.style().polish(btn)