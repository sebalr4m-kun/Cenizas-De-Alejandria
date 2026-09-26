# ==========================================
# Archivo: Modulos/Controllers/InsumoEstadisticas.py
# ==========================================
import datetime
from datetime import timedelta
import calendar
from Modulos.Config import Conexion

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QFrame, QLineEdit
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import Qt
from PySide6.QtCharts import (
    QChart, QChartView, QBarSet, QBarSeries, QStackedBarSeries, 
    QBarCategoryAxis, QValueAxis
)

class InsumoEstadisticas:
    """
    Controlador estadístico dedicado al módulo de Insumos.
    Ahora actúa como Controlador y Vista simultáneamente, generando su propia
    interfaz gráfica con PySide6 y QtCharts, lista para ser incrustada en MainWindow.
    """

    COLORES_ACCIONES = {
        1: "#00E676",  # Crear -> Verde Neón
        2: "#00B0FF",  # Modificar -> Azul Celeste
        3: "#FF9100",  # Borrado Lógico / Inactivar -> Naranja
        4: "#FF1744"   # Borrado Físico -> Rojo
    }

    NOMBRES_ACCIONES = {
        1: "Crear",
        2: "Modificar",
        3: "Inactivar",
        4: "Borrado Físico"
    }

    COLORES_ESTADOS = {
        "DISPONIBLE": "#00E676",
        "PRESTADO": "#FF9100",
        "MANTENIMIENTO": "#D500F9",
        "INACTIVA": "#7F8C8D",
        "EXTRAVIADO": "#FF1744"
    }
    
    COLORES_TIPOS = [
        "#00B0FF", "#E040FB", "#1DE9B6", "#FFEA00", "#FF3D00", "#76FF03"
    ]

    COLOR_TEXTO_MODO_NEGRO = "#FFFFFF"
    COLOR_FONDO_MODO_NEGRO = "#121212"

    def __init__(self, conexion=None):
        self.conexion_obj = conexion if conexion else Conexion()
        self.bd = self.conexion_obj.obtener_conexion()
        
        # Variables de estado de la vista
        self.offset_periodo = 0
        self.vista = QWidget()
        self._construir_vista()

    # =========================================================================
    # CONSTRUCCIÓN DE LA VISTA (INTERFAZ GRÁFICA)
    # =========================================================================
    
    def _construir_vista(self):
        """Construye el marco de la vista estadística, los controles y el gráfico."""
        layout_principal = QVBoxLayout(self.vista)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        
        # --- Panel de Controles Superiores ---
        panel_controles = QFrame()
        layout_controles = QHBoxLayout(panel_controles)
        layout_controles.setContentsMargins(0, 0, 0, 0)
        layout_controles.setSpacing(15)  # Espaciado extra para las opciones restantes
        
        self.lbl_filtro = QLabel("Filtro/Vista:")
        self.cmb_accion = QComboBox()
        self.cmb_accion.currentIndexChanged.connect(self._al_cambiar_accion)
        
        self.lbl_subfiltro = QLabel("Subfiltro:")
        self.cmb_subfiltro = QComboBox()
        self.cmb_subfiltro.currentIndexChanged.connect(self.actualizar_grafico)
        
        self.lbl_busqueda = QLabel("Buscar:")
        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("Búsqueda rápida...")
        self.txt_busqueda.textChanged.connect(self.actualizar_grafico)
        
        self.lbl_agrupacion = QLabel("Agrupación:")
        self.cmb_agrupacion = QComboBox()
        self.cmb_agrupacion.addItems(["Por Día", "Por Semana", "Por Mes", "Por Año"])
        self.cmb_agrupacion.currentIndexChanged.connect(self.actualizar_grafico)
        
        self.btn_prev = QPushButton("◀ Anterior")
        self.btn_prev.clicked.connect(self._retroceder_periodo)
        
        self.btn_next = QPushButton("Siguiente ▶")
        self.btn_next.clicked.connect(self._avanzar_periodo)
        
        layout_controles.addWidget(self.lbl_filtro)
        layout_controles.addWidget(self.cmb_accion)
        layout_controles.addWidget(self.lbl_subfiltro)
        layout_controles.addWidget(self.cmb_subfiltro)
        layout_controles.addWidget(self.lbl_busqueda)
        layout_controles.addWidget(self.txt_busqueda)
        layout_controles.addWidget(self.lbl_agrupacion)
        layout_controles.addWidget(self.cmb_agrupacion)
        layout_controles.addStretch()
        layout_controles.addWidget(self.btn_prev)
        layout_controles.addWidget(self.btn_next)
        
        layout_principal.addWidget(panel_controles)
        
        # --- Lienzo del Gráfico ---
        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setBackgroundBrush(QColor(self.COLOR_FONDO_MODO_NEGRO))
        self.chart.setTitleBrush(QColor(self.COLOR_TEXTO_MODO_NEGRO))
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        
        layout_principal.addWidget(self.chart_view)

        # Cargar datos iniciales en los controles
        self.cargar_datos()

    def obtener_widget_vista(self):
        """Retorna el widget principal de la vista construido para que MainWindow lo consuma."""
        return self.vista

    def cargar_datos(self):
        """Inicializa/reinicia los comboboxes y recarga el gráfico."""
        self.cmb_accion.blockSignals(True)
        self.cmb_accion.clear()
        acciones = self.obtener_acciones_disponibles()
        for acc in acciones:
            self.cmb_accion.addItem(acc["nombre"], userData=acc["id"])
        self.cmb_accion.blockSignals(False)
        
        self._al_cambiar_accion()

    def _al_cambiar_accion(self):
        """Actualiza los subfiltros disponibles y altera la visibilidad al cambiar de vista."""
        id_accion = self.cmb_accion.currentData()
        
        self.cmb_subfiltro.blockSignals(True)
        self.cmb_subfiltro.clear()
        subfiltros = self.obtener_subfiltros_disponibles(id_accion)
        for sub in subfiltros:
            self.cmb_subfiltro.addItem(sub["nombre"], userData=sub["id"])
        self.cmb_subfiltro.blockSignals(False)
        
        es_vista_estatica = id_accion in ["tipos", "estados"]
        
        # Si es un Catálogo/Inventario estático: ocultar agrupación y navegación
        self.lbl_agrupacion.setVisible(not es_vista_estatica)
        self.cmb_agrupacion.setVisible(not es_vista_estatica)
        self.btn_prev.setVisible(not es_vista_estatica)
        self.btn_next.setVisible(not es_vista_estatica)
        
        # Si es Auditoría (NO estática): ocultar subfiltro y barra de búsqueda
        self.lbl_subfiltro.setVisible(es_vista_estatica)
        self.cmb_subfiltro.setVisible(es_vista_estatica)
        self.lbl_busqueda.setVisible(es_vista_estatica)
        self.txt_busqueda.setVisible(es_vista_estatica)

        # Limpiar la barra de búsqueda al cambiar para evitar filtros residuales
        self.txt_busqueda.blockSignals(True)
        self.txt_busqueda.clear()
        self.txt_busqueda.blockSignals(False)
        
        self.offset_periodo = 0
        self.actualizar_grafico()

    def _retroceder_periodo(self):
        self.offset_periodo -= 1
        self.actualizar_grafico()

    def _avanzar_periodo(self):
        self.offset_periodo += 1
        self.actualizar_grafico()

    def actualizar_grafico(self):
        """Solicita los datos lógicos y dibuja las series y ejes en el QChart."""
        id_accion = self.cmb_accion.currentData()
        id_subfiltro = self.cmb_subfiltro.currentData()
        agrupacion = self.cmb_agrupacion.currentText()
        texto_busqueda = self.txt_busqueda.text()
        
        datos = self.obtener_reporte_estadistico(agrupacion, self.offset_periodo, id_accion, id_subfiltro, texto_busqueda)
        
        self.chart.removeAllSeries()
        for ax in self.chart.axes():
            self.chart.removeAxis(ax)

        modo = datos.get("modo_grafico", "agrupado_lado_a_lado")
        
        if modo == "apilado":
            series_chart = QStackedBarSeries()
        else:
            series_chart = QBarSeries()
            
        for serie_data in datos["series"]:
            bar_set = QBarSet(serie_data["nombre"])
            bar_set.append(serie_data["datos"])
            bar_set.setColor(QColor(serie_data.get("color_barra", "#FFFFFF")))
            series_chart.append(bar_set)
            
        self.chart.addSeries(series_chart)
        self.chart.setTitle(datos["titulo"])
        self.chart.setTitleBrush(QColor(datos.get("estilo_base", {}).get("texto", self.COLOR_TEXTO_MODO_NEGRO)))
        self.chart.setBackgroundBrush(QColor(datos.get("estilo_base", {}).get("fondo", self.COLOR_FONDO_MODO_NEGRO)))
        
        axis_x = QBarCategoryAxis()
        axis_x.append(datos["eje_x"])
        axis_x.setLabelsBrush(QColor(datos.get("estilo_base", {}).get("texto", self.COLOR_TEXTO_MODO_NEGRO)))
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series_chart.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setLabelsBrush(QColor(datos.get("estilo_base", {}).get("texto", self.COLOR_TEXTO_MODO_NEGRO)))
        # Evitar valores flotantes si son conteos
        axis_y.setLabelFormat("%d")
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series_chart.attachAxis(axis_y)

    # =========================================================================
    # LÓGICA DE DATOS
    # =========================================================================

    def _refrescar_transaccion(self):
        if self.bd:
            self.bd.commit()

    def obtener_acciones_disponibles(self):
        """Retorna las acciones de auditoría y las vistas estáticas del inventario."""
        acciones = [{"id": None, "nombre": "Auditoría: Todas las Acciones"}]
        for id_acc, nombre in self.NOMBRES_ACCIONES.items():
            acciones.append({
                "id": id_acc,
                "nombre": f"Auditoría: {nombre} ({id_acc})"
            })
        acciones.append({"id": "tipos", "nombre": "Inventario: Tipos de Insumo"})
        acciones.append({"id": "estados", "nombre": "Inventario: Estados Físicos"})
        return acciones

    def obtener_subfiltros_disponibles(self, id_accion=None):
        """Busca dinámicamente los tipos de insumos registrados."""
        self._refrescar_transaccion()
        filtros = [{"id": None, "nombre": "Todos los Tipos de Insumo"}]
        cursor = self.bd.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_tipo_insumo as id, nombre FROM param_tipos_insumo WHERE estado = 'ACTIVO'")
            for fila in cursor.fetchall():
                filtros.append(fila)
        except Exception:
            pass
        finally:
            cursor.close()
        return filtros

    def obtener_fecha_inicio_sistema(self):
        self._refrescar_transaccion()
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT MIN(fecha_hora) FROM auditorias WHERE modulo = 'Insumos'")
            res = cursor.fetchone()
            if res and res[0]:
                fecha = res[0]
                return fecha.date() if isinstance(fecha, datetime.datetime) else fecha
            return datetime.date.today()
        finally:
            cursor.close()

    def obtener_reporte_estadistico(self, agrupacion="Por Semana", offset_periodo=0, id_accion_filtro=None, id_subfiltro=None, texto_busqueda=""):
        """Punto de entrada. Enruta hacia la línea de tiempo (Auditoría) o fotografía estática (Inventario)."""
        
        # Enrutamiento de vistas estáticas de inventario
        if id_accion_filtro == "tipos":
            return self._generar_reporte_tipos(texto_busqueda)
        elif id_accion_filtro == "estados":
            return self._generar_reporte_estados(id_subfiltro, texto_busqueda)

        # Enrutamiento de vistas temporales de auditoría
        if agrupacion in ["Por Día", "Por Semana"]:
            datos = self.obtener_estadisticas_semanales(offset_periodo, id_accion_filtro, id_subfiltro)
        elif agrupacion == "Por Mes":
            datos = self.obtener_estadisticas_mensuales(offset_periodo, id_accion_filtro, id_subfiltro)
        elif agrupacion == "Por Año":
            datos = self.obtener_estadisticas_anuales(offset_periodo, id_accion_filtro, id_subfiltro)
        else:
            datos = self.obtener_estadisticas_semanales(offset_periodo, id_accion_filtro, id_subfiltro)

        nombre_accion = self.NOMBRES_ACCIONES.get(id_accion_filtro, "Todas las Acciones") if isinstance(id_accion_filtro, int) else "Todas las Acciones"
        titulo = f"Auditoría de Flujo - Insumos ({nombre_accion}) [{agrupacion}]"
        
        if offset_periodo != 0:
            titulo += f" (Offset: {offset_periodo})"

        datos["titulo"] = titulo
        return datos

    def _generar_reporte_tipos(self, texto_busqueda=""):
        self._refrescar_transaccion()
        cursor = self.bd.cursor(dictionary=True)
        series = []
        try:
            sql = """
                SELECT t.nombre, COUNT(i.id_insumo) as total
                FROM param_tipos_insumo t
                LEFT JOIN insumos i ON t.id_tipo_insumo = i.id_tipo_insumo
            """
            params = []
            
            if texto_busqueda:
                sql += " WHERE t.nombre LIKE %s"
                params.append(f"%{texto_busqueda}%")
                
            sql += " GROUP BY t.id_tipo_insumo, t.nombre"
            
            if params:
                cursor.execute(sql, tuple(params))
            else:
                cursor.execute(sql)
                
            filas = cursor.fetchall()
            
            color_idx = 0
            for f in filas:
                color = self.COLORES_TIPOS[color_idx % len(self.COLORES_TIPOS)]
                series.append({
                    "id_accion": "tipo",
                    "nombre": f['nombre'],
                    "color_barra": color,
                    "color_texto": self.COLOR_TEXTO_MODO_NEGRO,
                    "datos": [f['total']]
                })
                color_idx += 1
        finally:
            cursor.close()

        return {
            "modo_grafico": "agrupado_lado_a_lado",
            "estilo_base": {"fondo": self.COLOR_FONDO_MODO_NEGRO, "texto": self.COLOR_TEXTO_MODO_NEGRO},
            "eje_x": ["Distribución del Inventario Físico"],
            "series": series,
            "titulo": "Inventario Global - Absorbido por Tipo de Insumo"
        }

    def _generar_reporte_estados(self, id_subfiltro=None, texto_busqueda=""):
        self._refrescar_transaccion()
        cursor = self.bd.cursor(dictionary=True)
        series = []
        try:
            sql = "SELECT estado, COUNT(id_insumo) as total FROM insumos"
            condiciones = []
            params = []
            
            if id_subfiltro:
                condiciones.append("id_tipo_insumo = %s")
                params.append(id_subfiltro)
                
            if texto_busqueda:
                condiciones.append("titulo LIKE %s")
                params.append(f"%{texto_busqueda}%")
                
            if condiciones:
                sql += " WHERE " + " AND ".join(condiciones)
                
            sql += " GROUP BY estado"
            
            if params:
                cursor.execute(sql, tuple(params))
            else:
                cursor.execute(sql)
                
            filas = cursor.fetchall()
            
            color_idx = 0
            for f in filas:
                estado_str = str(f['estado']).upper()
                color = self.COLORES_ESTADOS.get(estado_str, self.COLORES_TIPOS[color_idx % len(self.COLORES_TIPOS)])
                series.append({
                    "id_accion": "estado",
                    "nombre": f['estado'],
                    "color_barra": color,
                    "color_texto": self.COLOR_TEXTO_MODO_NEGRO,
                    "datos": [f['total']]
                })
                color_idx += 1
        finally:
            cursor.close()

        titulo = "Estado Físico del Inventario (Filtrado)" if id_subfiltro or texto_busqueda else "Estado Físico del Inventario Global"
        return {
            "modo_grafico": "agrupado_lado_a_lado",
            "estilo_base": {"fondo": self.COLOR_FONDO_MODO_NEGRO, "texto": self.COLOR_TEXTO_MODO_NEGRO},
            "eje_x": ["Estados Actuales Registrados"],
            "series": series,
            "titulo": titulo
        }

    def obtener_estadisticas_semanales(self, offset_periodo=0, id_accion_filtro=None, id_subfiltro=None):
        self._refrescar_transaccion()
        base_date = datetime.date.today() + timedelta(weeks=offset_periodo)
        hace_6_dias = base_date - timedelta(days=6)
        fecha_inicio_sys = self.obtener_fecha_inicio_sistema()

        dias_rango = [hace_6_dias + timedelta(days=i) for i in range(7)]
        labels_dias = [d.strftime("%Y-%m-%d") for d in dias_rango]

        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]
        dataset = self._preparar_dataset(acciones_a_procesar, labels_dias)

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT DATE(fecha_hora) AS fecha, id_accion, COUNT(*) AS total
                FROM auditorias
                WHERE fecha_hora >= %s AND fecha_hora <= %s
                  AND modulo = 'Insumos'
            """
            inicio_str = hace_6_dias.strftime("%Y-%m-%d 00:00:00")
            fin_str = base_date.strftime("%Y-%m-%d 23:59:59")
            params = [inicio_str, fin_str]

            if id_accion_filtro:
                sql += " AND id_accion = %s"
                params.append(id_accion_filtro)

            sql += " GROUP BY DATE(fecha_hora), id_accion"

            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                fecha_reg = f['fecha']
                f_str = fecha_reg.strftime("%Y-%m-%d") if isinstance(fecha_reg, (datetime.datetime, datetime.date)) else str(fecha_reg)
                f_date = fecha_reg.date() if isinstance(fecha_reg, datetime.datetime) else (fecha_reg if isinstance(fecha_reg, datetime.date) else datetime.datetime.strptime(f_str, "%Y-%m-%d").date())
                
                acc_id = f['id_accion']
                if f_str in labels_dias and acc_id in dataset:
                    if f_date >= fecha_inicio_sys:
                        dataset[acc_id]["valores"][f_str] = f['total']
        finally:
            cursor.close()

        return self._formatear_respuesta(labels_dias, dataset, id_accion_filtro)

    def obtener_estadisticas_mensuales(self, offset_periodo=0, id_accion_filtro=None, id_subfiltro=None):
        self._refrescar_transaccion()
        anio_actual = datetime.date.today().year + offset_periodo
        labels_meses = [f"{anio_actual}-{mes:02d}" for mes in range(1, 13)]

        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]
        dataset = self._preparar_dataset(acciones_a_procesar, labels_meses)

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT DATE_FORMAT(fecha_hora, '%Y-%m') AS mes_str, id_accion, COUNT(*) AS total
                FROM auditorias
                WHERE YEAR(fecha_hora) = %s
                  AND modulo = 'Insumos'
            """
            params = [anio_actual]

            if id_accion_filtro:
                sql += " AND id_accion = %s"
                params.append(id_accion_filtro)

            sql += " GROUP BY DATE_FORMAT(fecha_hora, '%Y-%m'), id_accion"

            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                m_str = f['mes_str']
                acc_id = f['id_accion']
                if m_str in labels_meses and acc_id in dataset:
                    dataset[acc_id]["valores"][m_str] = f['total']
        finally:
            cursor.close()

        return self._formatear_respuesta(labels_meses, dataset, id_accion_filtro)

    def obtener_estadisticas_anuales(self, offset_periodo=0, id_accion_filtro=None, id_subfiltro=None):
        self._refrescar_transaccion()
        fecha_inicio_sys = self.obtener_fecha_inicio_sistema()
        anio_inicio = fecha_inicio_sys.year
        anio_actual = datetime.date.today().year + offset_periodo

        if anio_inicio > anio_actual:
            anio_inicio = anio_actual

        labels_anios = [str(a) for a in range(anio_inicio, anio_actual + 1)]
        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]
        dataset = self._preparar_dataset(acciones_a_procesar, labels_anios)

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT YEAR(fecha_hora) AS anio_num, id_accion, COUNT(*) AS total
                FROM auditorias
                WHERE YEAR(fecha_hora) >= %s AND YEAR(fecha_hora) <= %s
                  AND modulo = 'Insumos'
            """
            params = [anio_inicio, anio_actual]

            if id_accion_filtro:
                sql += " AND id_accion = %s"
                params.append(id_accion_filtro)

            sql += " GROUP BY YEAR(fecha_hora), id_accion"

            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            for f in filas:
                a_str = str(f['anio_num'])
                acc_id = f['id_accion']
                if a_str in labels_anios and acc_id in dataset:
                    dataset[acc_id]["valores"][a_str] = f['total']
        finally:
            cursor.close()

        return self._formatear_respuesta(labels_anios, dataset, id_accion_filtro)

    def _preparar_dataset(self, acciones, labels_tiempo):
        return {
            acc: {
                "id_accion": acc,
                "nombre": self.NOMBRES_ACCIONES.get(acc, f"Acción {acc}"),
                "color": self.COLORES_ACCIONES.get(acc, "#FFFFFF"),
                "valores": {lbl: 0 for lbl in labels_tiempo}
            }
            for acc in acciones
        }

    def _formatear_respuesta(self, eje_x, dataset, id_accion_filtro):
        series = []
        for acc_id, contenido in dataset.items():
            valores_lista = [contenido["valores"][clave] for clave in eje_x]
            series.append({
                "id_accion": acc_id,
                "nombre": contenido["nombre"],
                "color_barra": contenido["color"],
                "color_texto": self.COLOR_TEXTO_MODO_NEGRO,
                "datos": valores_lista
            })

        return {
            "modo_grafico": "agrupado_lado_a_lado" if not id_accion_filtro else "aislado",
            "estilo_base": {
                "fondo": self.COLOR_FONDO_MODO_NEGRO,
                "texto": self.COLOR_TEXTO_MODO_NEGRO
            },
            "eje_x": eje_x,
            "series": series
        }