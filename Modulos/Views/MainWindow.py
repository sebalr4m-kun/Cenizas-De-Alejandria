# ==========================================
# Archivo: MainWindow.py
# ==========================================
import sys
import os
import json
import importlib
import inspect

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget,
    QMessageBox, QApplication, QLabel, QComboBox, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QLineEdit
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush

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


class CanvasGraficoBarras(QWidget):
    """Lienzo dinámico para la visualización gráfica de estadísticas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.eje_x = []
        self.series = []
        self.titulo_grafico = "Vista de Estadísticas"
        self.bg_override = None
        self.text_override = None

    def actualizar_datos_estructurados(self, datos_dict, titulo="Vista de Estadísticas"):
        self.titulo_grafico = titulo
        if not datos_dict or not isinstance(datos_dict, dict):
            self.eje_x = []
            self.series = []
            self.bg_override = None
            self.text_override = None
        else:
            self.eje_x = datos_dict.get("eje_x", [])
            self.series = datos_dict.get("series", [])
            estilo = datos_dict.get("estilo_base", {})
            self.bg_override = QColor(estilo.get("fondo")) if estilo.get("fondo") else None
            self.text_override = QColor(estilo.get("texto")) if estilo.get("texto") else None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        ancho = self.width()
        alto = self.height()

        bg_color = self.bg_override if self.bg_override else self.palette().window().color()
        text_color = self.text_override if self.text_override else self.palette().text().color()
        painter.fillRect(0, 0, ancho, alto, bg_color)

        font_titulo = QFont("Segoe UI", 11, QFont.Bold)
        painter.setFont(font_titulo)
        painter.setPen(QPen(text_color))
        painter.drawText(20, 25, self.titulo_grafico)

        tiene_datos = False
        max_val = 0
        for s in self.series:
            for v in s.get("datos", []):
                if v > 0:
                    tiene_datos = True
                if v > max_val:
                    max_val = v

        if not self.eje_x or not self.series or not tiene_datos:
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(QRectF(0, 0, ancho, alto), Qt.AlignCenter, "Sin datos cargados para este módulo / período")
            return

        margin_top = 50
        margin_bottom = 40
        margin_left = 50
        margin_right = 30

        if len(self.series) > 1:
            margin_top = 70
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            lx = margin_left
            ly = 42
            for s in self.series:
                col = QColor(s.get("color_barra", "#FFFFFF"))
                painter.fillRect(lx, ly, 10, 10, col)
                painter.setPen(QPen(text_color))
                painter.drawText(lx + 14, ly + 9, s.get("nombre", ""))
                lx += len(s.get("nombre", "")) * 9 + 30
                if lx > ancho - 50:
                    lx = margin_left
                    ly += 15

        chart_w = ancho - margin_left - margin_right
        chart_h = alto - margin_top - margin_bottom
        val_top = max(10, int(max_val * 1.2))

        painter.setPen(QPen(QColor(189, 195, 199), 1.5))
        painter.drawLine(margin_left, margin_top, margin_left, margin_top + chart_h)
        painter.drawLine(margin_left, margin_top + chart_h, margin_left + chart_w, margin_top + chart_h)

        num_guias = 4
        font_axis = QFont("Segoe UI", 8)
        painter.setFont(font_axis)

        for i in range(num_guias + 1):
            y_val = int((val_top / num_guias) * i)
            y_pos = margin_top + chart_h - (i * (chart_h / num_guias))

            line_col = QColor(60, 60, 60) if bg_color.lightness() < 128 else QColor(220, 220, 220)
            painter.setPen(QPen(line_col, 1, Qt.DashLine))
            painter.drawLine(margin_left, int(y_pos), margin_left + chart_w, int(y_pos))

            painter.setPen(QPen(text_color))
            painter.drawText(5, int(y_pos + 4), margin_left - 10, 15, Qt.AlignRight, str(y_val))

        n_cat = len(self.eje_x)
        n_series = len(self.series)
        if n_cat == 0 or n_series == 0:
            return

        cat_w = chart_w / n_cat
        gap_cat = cat_w * 0.20
        usable_cat_w = cat_w - gap_cat
        bar_w = max(3, usable_cat_w / n_series)

        for cat_idx, label in enumerate(self.eje_x):
            cat_x_start = margin_left + (cat_idx * cat_w) + (gap_cat / 2)

            for s_idx, serie in enumerate(self.series):
                val = serie["datos"][cat_idx] if cat_idx < len(serie["datos"]) else 0
                col_barra = QColor(serie.get("color_barra", "#3498db"))

                x_pos = cat_x_start + (s_idx * bar_w)
                bar_h = (val / val_top) * chart_h
                y_pos = margin_top + chart_h - bar_h

                if val > 0:
                    painter.setBrush(QBrush(col_barra))
                    painter.setPen(QPen(col_barra.darker(110), 1))
                    painter.drawRoundedRect(QRectF(x_pos, y_pos, max(2, bar_w - 1), bar_h), 2, 2)

                    if bar_w >= 14 or n_series == 1:
                        painter.setPen(QPen(text_color))
                        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
                        painter.drawText(QRectF(x_pos - 5, y_pos - 14, bar_w + 10, 12), Qt.AlignCenter, str(val))

            painter.setFont(font_axis)
            painter.setPen(QPen(text_color))
            lbl_str = str(label)
            if len(lbl_str) > 10 and n_cat > 7:
                lbl_str = lbl_str[-5:]
            painter.drawText(QRectF(margin_left + (cat_idx * cat_w), margin_top + chart_h + 5, cat_w, 25), Qt.AlignCenter, lbl_str)


class WidgetGraficosAuditoria(QWidget):
    """Marco contenedor orquestador dinámico de controladores de estadística con soporte para subfiltros y búsquedas integradas."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.modulo_actual = "Usuarios"
        self.offset_periodo = 0
        self.controladores_stats = {} 
        self.subfiltros_cache = []

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)

        layout_controles = QHBoxLayout()

        lbl_titulo = QLabel("📊 Panel de Estadísticas")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout_controles.addWidget(lbl_titulo)
        layout_controles.addSpacing(10)

        # Barra de búsqueda exclusiva de subfiltros anclada al título
        self.barra_busqueda = QLineEdit()
        self.barra_busqueda.setPlaceholderText("Buscar en Subfiltro...")
        self.barra_busqueda.setFixedWidth(160)
        self.barra_busqueda.textChanged.connect(self.filtrar_subfiltros)
        layout_controles.addWidget(self.barra_busqueda)

        layout_controles.addStretch()

        self.combo_agrupacion = QComboBox()
        self.combo_agrupacion.addItems(["Por Semana", "Por Mes", "Por Año"])

        self.combo_accion = QComboBox()
        self.combo_accion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.lbl_subfiltro = QLabel("Tipo / Subfiltro:")
        self.combo_subfiltro = QComboBox()
        self.combo_subfiltro.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_anterior = QPushButton("◄")
        self.btn_anterior.setFixedWidth(35)
        self.lbl_rango_temporal = QLabel("Actual")
        self.lbl_rango_temporal.setStyleSheet("font-weight: bold; margin: 0 5px;")
        self.btn_siguiente = QPushButton("►")
        self.btn_siguiente.setFixedWidth(35)

        # Variables de instancia para ocultar partes de la UI
        self.lbl_navegacion = QLabel("Navegación:")
        self.lbl_linea_tiempo = QLabel("Línea de Tiempo:")
        self.lbl_filtrar_accion = QLabel("Filtrar Acción:")

        layout_controles.addWidget(self.lbl_navegacion)
        layout_controles.addWidget(self.btn_anterior)
        layout_controles.addWidget(self.lbl_rango_temporal)
        layout_controles.addWidget(self.btn_siguiente)
        layout_controles.addSpacing(15)

        layout_controles.addWidget(self.lbl_subfiltro)
        layout_controles.addWidget(self.combo_subfiltro)
        layout_controles.addWidget(self.lbl_filtrar_accion)
        layout_controles.addWidget(self.combo_accion)
        layout_controles.addWidget(self.lbl_linea_tiempo)
        layout_controles.addWidget(self.combo_agrupacion)

        layout_principal.addLayout(layout_controles)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFrameShadow(QFrame.Sunken)
        layout_principal.addWidget(linea)

        self.canvas_grafico = CanvasGraficoBarras(self)
        layout_principal.addWidget(self.canvas_grafico, 1)

        # Conexiones de los controles
        self.combo_agrupacion.currentIndexChanged.connect(self._al_cambiar_agrupacion)
        self.combo_accion.currentIndexChanged.connect(self._al_cambiar_accion)
        self.combo_subfiltro.currentIndexChanged.connect(self.actualizar_vista_grafico)
        self.btn_anterior.clicked.connect(lambda: self.desplazar_periodo(-1))
        self.btn_siguiente.clicked.connect(lambda: self.desplazar_periodo(1))

        self.poblar_combo_acciones()
        self.poblar_combo_subfiltros()
        self.actualizar_vista_grafico()

    def ajustar_visibilidad_controles(self):
        """Muestra u oculta la navegación y línea de tiempo dependiendo de si es auditoría o catálogo."""
        ocultar_navegacion = False
        
        # Aplicamos la regla SÓLO para el módulo de Libros, tal como fue solicitado.
        if self.modulo_actual == "Libros":
            texto_accion = self.combo_accion.currentText().upper()
            # Si la opción no menciona "AUDITOR", la consideramos de Catálogo
            if "AUDITOR" not in texto_accion:
                ocultar_navegacion = True
                
        if ocultar_navegacion:
            self.lbl_navegacion.hide()
            self.btn_anterior.hide()
            self.lbl_rango_temporal.hide()
            self.btn_siguiente.hide()
            self.lbl_linea_tiempo.hide()
            self.combo_agrupacion.hide()
        else:
            self.lbl_navegacion.show()
            self.btn_anterior.show()
            self.lbl_rango_temporal.show()
            self.btn_siguiente.show()
            self.lbl_linea_tiempo.show()
            self.combo_agrupacion.show()

    def _obtener_controlador_stats(self, modulo):
        """Carga y cachea dinámicamente el controlador de estadísticas requerido."""
        if modulo in self.controladores_stats:
            return self.controladores_stats[modulo]

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
            instancia = clase()
            self.controladores_stats[modulo] = instancia
            return instancia
        except (ImportError, ModuleNotFoundError, AttributeError):
            return None

    def poblar_combo_acciones(self):
        """Consulta las acciones disponibles al controlador del módulo activo."""
        self.combo_accion.blockSignals(True)
        self.combo_accion.clear()

        ctrl = self._obtener_controlador_stats(self.modulo_actual)
        if ctrl and hasattr(ctrl, "obtener_acciones_disponibles"):
            acciones = ctrl.obtener_acciones_disponibles()
            for acc in acciones:
                self.combo_accion.addItem(acc["nombre"], userData=acc["id"])
        else:
            self.combo_accion.addItem("Todas las Acciones", userData=None)

        self.combo_accion.blockSignals(False)
        self.ajustar_visibilidad_controles()

    def _al_cambiar_accion(self):
        self.ajustar_visibilidad_controles()
        self.poblar_combo_subfiltros()
        self.actualizar_vista_grafico()

    def poblar_combo_subfiltros(self):
        """Reúne el contenido que corresponderá a Tipo/Subfiltro dictaminado por la acción actual."""
        ctrl = self._obtener_controlador_stats(self.modulo_actual)
        id_accion = self.combo_accion.currentData()
        self.subfiltros_cache = []

        if ctrl and hasattr(ctrl, "obtener_subfiltros_disponibles"):
            sig = inspect.signature(ctrl.obtener_subfiltros_disponibles)
            if "id_accion" in sig.parameters:
                self.subfiltros_cache = ctrl.obtener_subfiltros_disponibles(id_accion=id_accion)
            else:
                self.subfiltros_cache = ctrl.obtener_subfiltros_disponibles()

        if self.subfiltros_cache:
            self.lbl_subfiltro.show()
            self.combo_subfiltro.show()
            self.barra_busqueda.show()
        else:
            self.lbl_subfiltro.hide()
            self.combo_subfiltro.hide()
            self.barra_busqueda.hide()
            self.barra_busqueda.clear()

        self.filtrar_subfiltros(self.barra_busqueda.text())

    def filtrar_subfiltros(self, texto):
        """Procesa el input de la barra de búsqueda exclusivamente sobre la cache del combo de subfiltro."""
        self.combo_subfiltro.blockSignals(True)
        self.combo_subfiltro.clear()
        
        texto_busqueda = texto.lower()
        for sf in self.subfiltros_cache:
            if texto_busqueda in sf["nombre"].lower():
                self.combo_subfiltro.addItem(sf["nombre"], userData=sf["id"])
                
        self.combo_subfiltro.blockSignals(False)
        self.actualizar_vista_grafico()

    def _al_cambiar_agrupacion(self):
        self.offset_periodo = 0
        self.actualizar_vista_grafico()

    def desplazar_periodo(self, delta):
        nuevas_unidades = self.offset_periodo + delta
        if nuevas_unidades > 0:
            return  
        self.offset_periodo = nuevas_unidades
        self.actualizar_vista_grafico()

    def establecer_modulo_activo(self, nombre_modulo):
        if self.modulo_actual != nombre_modulo:
            self.modulo_actual = nombre_modulo
            self.offset_periodo = 0
            self.poblar_combo_acciones()
            self.poblar_combo_subfiltros()
        self.ajustar_visibilidad_controles()
        self.actualizar_vista_grafico()

    def actualizar_vista_grafico(self):
        """Consulta el reporte al controlador específico inspeccionando la firma de la función."""
        agrupacion = self.combo_agrupacion.currentText()
        id_accion = self.combo_accion.currentData()
        id_subfiltro = self.combo_subfiltro.currentData() if self.combo_subfiltro.isVisible() else None

        if self.offset_periodo == 0:
            self.lbl_rango_temporal.setText("Actual")
        else:
            self.lbl_rango_temporal.setText(f"{self.offset_periodo}")

        ctrl = self._obtener_controlador_stats(self.modulo_actual)

        if ctrl and hasattr(ctrl, "obtener_reporte_estadistico"):
            metodo = ctrl.obtener_reporte_estadistico
            sig = inspect.signature(metodo)
            
            kwargs_invocacion = {
                "agrupacion": agrupacion,
                "offset_periodo": self.offset_periodo,
                "id_accion_filtro": id_accion
            }
            
            acepta_subfiltro = "id_subfiltro" in sig.parameters
            acepta_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            
            if acepta_subfiltro or acepta_kwargs:
                kwargs_invocacion["id_subfiltro"] = id_subfiltro

            reporte = metodo(**kwargs_invocacion)
            titulo_render = reporte.get("titulo", f"Estadísticas - {self.modulo_actual}")
            self.canvas_grafico.actualizar_datos_estructurados(reporte, titulo=titulo_render)
        else:
            datos_vacios = {
                "modo_grafico": "aislado",
                "estilo_base": {"fondo": "#121212", "texto": "#FFFFFF"},
                "eje_x": [],
                "series": []
            }
            self.canvas_grafico.actualizar_datos_estructurados(datos_vacios, titulo=f"Estadísticas - {self.modulo_actual} (En desarrollo)")


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

        self.widget_graficos = WidgetGraficosAuditoria()
        self.widget_historial = WidgetHistorialAuditorias(self.conexion)

        self.pila_central = QStackedWidget()
        self.pila_central.addWidget(self.ctrl_usuario.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_insumo.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_libro.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_prestamo.obtener_widget_vista())
        self.pila_central.addWidget(self.ctrl_param.obtener_widget_vista())
        self.pila_central.addWidget(self.widget_graficos) 
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
            modulo_nombre = self.mapa_modulos[self.indice_modulo_actual]
            self.widget_graficos.establecer_modulo_activo(modulo_nombre)
            self.pila_central.setCurrentIndex(5) 
        else:
            self.btn_estadisticas.setText("Estadísticas")
            self.btn_historial.hide()
            self.cambiar_pagina(self.indice_modulo_actual)

    def alternar_colores(self):
        self.colores_invertidos = self.modo_estadisticas

        if self.colores_invertidos:
            estilo_invertido = """
                QWidget {
                    background-color: #121212;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #2c2c2c;
                    color: #ffffff;
                    border: 1px solid #7f8c8d;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QPushButton#ActiveMenuButton {
                    background-color: #555555;
                    color: #ffffff;
                    font-weight: bold;
                    border-left: 4px solid #ffffff;
                }
                QLineEdit, QComboBox, QTableWidget, QListWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QHeaderView::section {
                    background-color: #333333;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QTableWidget::item:selected, QListWidget::item:selected {
                    background-color: #34495e;
                    color: #ffffff;
                }
            """
            self.setStyleSheet(estilo_invertido)
        else:
            self.setStyleSheet("")

    def _obtener_permisos_seguro(self, nombre_modulo):
        mapeo_db = {
            "Usuarios": "usuarios",
            "Insumos": "insumos",
            "Libros": "libros",
            "Préstamos": "prestamos", 
            "Parámetros": "parámetros" 
        }
        clave_ideal = mapeo_db.get(nombre_modulo, nombre_modulo.lower())

        if clave_ideal in self.permisos:
            return self.permisos[clave_ideal]

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

        for i, modulo in enumerate(self.mapa_modulos):
            perms = self._obtener_permisos_seguro(modulo)
            puede_ver = perms.get('ver', False)
            self.botones_menu[i].setVisible(puede_ver)

            if puede_ver and not al_menos_uno_visible:
                al_menos_uno_visible = True
                primer_indice_visible = i

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

                if self.permisos != permisos_db_dict:
                    expulsar = True
                    razon = "Sus privilegios de acceso al sistema han sido modificados remotamente."

        except Exception:
            pass
        finally:
            cursor.close()

        if expulsar:
            auditoria_global.auditar_sesion(f"Cierre forzado: {razon}")

            QMessageBox.critical(self, "Sesión Terminada por Seguridad", f"{razon}\n\nPor favor, vuelva a iniciar sesión.")
            try:
                QApplication.quit()
                os.execl(sys.executable, sys.executable, *sys.argv)
            except Exception:
                sys.exit(1)

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
        if hasattr(self.ctrl_libro, 'datos_actualizados'):
            self.ctrl_libro.datos_actualizados.connect(self.recargar_todo)

        if hasattr(self.ctrl_insumo, 'datos_actualizados'):
            self.ctrl_insumo.datos_actualizados.connect(self.recargar_todo)

        if hasattr(self.ctrl_param, 'parametro_guardado'):
            self.ctrl_param.parametro_guardado.connect(self.recargar_todo)

        if hasattr(self.ctrl_prestamo, 'datos_actualizados'):
            self.ctrl_prestamo.datos_actualizados.connect(self.recargar_todo)

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
        self.indice_modulo_actual = indice

        if self.modo_estadisticas:
            self.actualizar_resaltado_menu(indice)
            modulo_actual = self.mapa_modulos[indice]
            self.widget_graficos.establecer_modulo_activo(modulo_actual)
            self.pila_central.setCurrentWidget(self.widget_graficos) 
            self.pila_derecha.hide()
            return

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