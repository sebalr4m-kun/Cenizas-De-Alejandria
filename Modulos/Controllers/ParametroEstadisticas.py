# ==========================================
# Archivo: Modulos/Controllers/ParametroEstadisticas.py
# ==========================================
import datetime
from datetime import timedelta
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFrame, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
from PySide6.QtCore import Qt, QRectF
from Modulos.Config import Conexion

class CanvasGrafico(QWidget):
    """Lienzo interno reutilizado para graficar series."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.datos = None

    def actualizar_datos(self, datos):
        self.datos = datos
        self.update()

    def paintEvent(self, event):
        if not self.datos: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_col = QColor(self.datos.get("estilo_base", {}).get("fondo", "#121212"))
        text_col = QColor(self.datos.get("estilo_base", {}).get("texto", "#FFFFFF"))
        painter.fillRect(0, 0, self.width(), self.height(), bg_col)

        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.setPen(QPen(text_col))
        painter.drawText(20, 25, self.datos.get("titulo", "Estadísticas"))

        series = self.datos.get("series", [])
        eje_x = self.datos.get("eje_x", [])
        if not series or not eje_x: return

        margin_left, margin_right, margin_top, margin_bottom = 50, 30, 70, 40
        max_val = max([max(s["datos"]) if s["datos"] else 0 for s in series])
        val_top = max(10, int(max_val * 1.2))
        
        lx, ly = margin_left, 42
        for s in series:
            col = QColor(s.get("color_barra", "#FFFFFF"))
            painter.fillRect(lx, ly, 10, 10, col)
            painter.drawText(lx + 14, ly + 9, s.get("nombre", ""))
            lx += len(s.get("nombre", "")) * 8 + 30

        chart_w, chart_h = self.width() - margin_left - margin_right, self.height() - margin_top - margin_bottom
        painter.setPen(QPen(QColor(189, 195, 199), 1.5))
        painter.drawLine(margin_left, margin_top, margin_left, margin_top + chart_h)
        painter.drawLine(margin_left, margin_top + chart_h, margin_left + chart_w, margin_top + chart_h)

        cat_w = chart_w / len(eje_x)
        bar_w = max(3, (cat_w * 0.8) / len(series))
        
        for cat_idx, label in enumerate(eje_x):
            cat_x = margin_left + (cat_idx * cat_w) + (cat_w * 0.1)
            for s_idx, serie in enumerate(series):
                val = serie["datos"][cat_idx]
                if val > 0:
                    x_pos = cat_x + (s_idx * bar_w)
                    bar_h = (val / val_top) * chart_h
                    y_pos = margin_top + chart_h - bar_h
                    
                    col_barra = QColor(serie["color_barra"])
                    painter.setBrush(QBrush(col_barra))
                    painter.setPen(QPen(col_barra.darker(110), 1))
                    painter.drawRoundedRect(QRectF(x_pos, y_pos, max(2, bar_w - 1), bar_h), 2, 2)
            
            painter.setPen(QPen(text_col))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(margin_left + (cat_idx * cat_w), margin_top + chart_h + 5, cat_w, 25), Qt.AlignCenter, str(label)[-5:])

class VistaParametroEstadisticas(QWidget):
    """Marco visual exclusivo e integrado del módulo de Parámetros."""
    def __init__(self, controlador, parent=None):
        super().__init__(parent)
        self.controlador = controlador
        self.offset_periodo = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        layout_ctrls = QHBoxLayout()
        layout_ctrls.addWidget(QLabel("📊 Panel de Parámetros"))
        layout_ctrls.addStretch()

        self.combo_agrupacion = QComboBox()
        self.combo_agrupacion.addItems(["Por Semana", "Por Mes", "Por Año"])
        self.combo_accion = QComboBox()

        for acc in self.controlador.obtener_acciones_disponibles():
            self.combo_accion.addItem(acc["nombre"], userData=acc["id"])

        self.btn_ant = QPushButton("◄")
        self.btn_ant.setFixedWidth(35)
        self.lbl_rango = QLabel("Actual")
        self.lbl_rango.setStyleSheet("font-weight: bold; margin: 0 5px;")
        self.btn_sig = QPushButton("►")
        self.btn_sig.setFixedWidth(35)

        layout_ctrls.addWidget(self.btn_ant)
        layout_ctrls.addWidget(self.lbl_rango)
        layout_ctrls.addWidget(self.btn_sig)
        layout_ctrls.addSpacing(15)
        layout_ctrls.addWidget(QLabel("Acción:"))
        layout_ctrls.addWidget(self.combo_accion)
        layout_ctrls.addWidget(QLabel("Línea de Tiempo:"))
        layout_ctrls.addWidget(self.combo_agrupacion)

        layout.addLayout(layout_ctrls)
        
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        layout.addWidget(linea)

        self.canvas = CanvasGrafico()
        layout.addWidget(self.canvas, 1)

        self.combo_agrupacion.currentIndexChanged.connect(self._reset_y_actualizar)
        self.combo_accion.currentIndexChanged.connect(self._reset_y_actualizar)
        self.btn_ant.clicked.connect(lambda: self._desplazar(-1))
        self.btn_sig.clicked.connect(lambda: self._desplazar(1))

    def _reset_y_actualizar(self):
        self.offset_periodo = 0
        self.actualizar_vista_grafico()

    def _desplazar(self, delta):
        if self.offset_periodo + delta > 0: return
        self.offset_periodo += delta
        self.actualizar_vista_grafico()

    def actualizar_vista_grafico(self):
        self.lbl_rango.setText("Actual" if self.offset_periodo == 0 else str(self.offset_periodo))
        datos = self.controlador.obtener_reporte_estadistico(
            self.combo_agrupacion.currentText(), self.offset_periodo, self.combo_accion.currentData()
        )
        self.canvas.actualizar_datos(datos)

class ParametroEstadisticas:
    """
    Controlador estadístico dedicado exclusivamente al módulo de Parámetros.
    """

    COLORES_ACCIONES = {
        1: "#00E676",  # Crear -> Verde Neón
        2: "#00B0FF",  # Modificar -> Azul Celeste Vibrante
        3: "#FF9100",  # Inactivar -> Naranja Neón
        4: "#FF1744"   # Borrado Físico -> Rojo Vivo
    }

    NOMBRES_ACCIONES = {
        1: "Crear",
        2: "Modificar",
        3: "Inactivar",
        4: "Borrado Físico"
    }

    COLOR_TEXTO_MODO_NEGRO = "#FFFFFF"
    COLOR_FONDO_MODO_NEGRO = "#121212"

    def __init__(self):
        self.conexion_obj = Conexion()
        self.bd = self.conexion_obj.obtener_conexion()
        self.vista = None

    def obtener_widget_vista(self):
        if not self.vista:
            self.vista = VistaParametroEstadisticas(self)
        return self.vista

    def _refrescar_transaccion(self):
        if self.bd:
            self.bd.commit()

    def obtener_acciones_disponibles(self):
        acciones = [{"id": None, "nombre": "Todas las Acciones"}]
        for id_acc, nombre in self.NOMBRES_ACCIONES.items():
            acciones.append({
                "id": id_acc,
                "nombre": f"{nombre} ({id_acc})"
            })
        return acciones

    def obtener_fecha_inicio_sistema(self):
        self._refrescar_transaccion()
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT MIN(fecha_hora) FROM auditorias WHERE modulo = 'Parámetros'")
            res = cursor.fetchone()
            if res and res[0]:
                fecha = res[0]
                return fecha.date() if isinstance(fecha, datetime.datetime) else fecha
            return datetime.date.today()
        finally:
            cursor.close()

    def obtener_reporte_estadistico(self, agrupacion="Por Semana", offset_periodo=0, id_accion_filtro=None):
        if agrupacion in ["Por Día", "Por Semana"]:
            datos = self.obtener_estadisticas_semanales(offset_periodo=offset_periodo, id_accion_filtro=id_accion_filtro)
        elif agrupacion == "Por Mes":
            datos = self.obtener_estadisticas_mensuales(offset_periodo=offset_periodo, id_accion_filtro=id_accion_filtro)
        elif agrupacion == "Por Año":
            datos = self.obtener_estadisticas_anuales(offset_periodo=offset_periodo, id_accion_filtro=id_accion_filtro)
        else:
            datos = self.obtener_estadisticas_semanales(offset_periodo=offset_periodo, id_accion_filtro=id_accion_filtro)

        nombre_accion = self.NOMBRES_ACCIONES.get(id_accion_filtro, "Todas las Acciones") if id_accion_filtro else "Todas las Acciones"
        titulo = f"Estadísticas - Parámetros ({nombre_accion}) [{agrupacion}]"
        
        if offset_periodo != 0:
            titulo += f" (Offset: {offset_periodo})"

        datos["titulo"] = titulo
        return datos

    def obtener_estadisticas_semanales(self, offset_periodo=0, id_accion_filtro=None):
        self._refrescar_transaccion()
        base_date = datetime.date.today() + timedelta(weeks=offset_periodo)
        hace_6_dias = base_date - timedelta(days=6)
        fecha_inicio_sys = self.obtener_fecha_inicio_sistema()

        dias_rango = [hace_6_dias + timedelta(days=i) for i in range(7)]
        labels_dias = [d.strftime("%Y-%m-%d") for d in dias_rango]

        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]

        dataset = {
            acc: {
                "id_accion": acc,
                "nombre": self.NOMBRES_ACCIONES.get(acc, f"Acción {acc}"),
                "color": self.COLORES_ACCIONES.get(acc, "#FFFFFF"),
                "valores": {d_str: 0 for d_str in labels_dias}
            }
            for acc in acciones_a_procesar
        }

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT DATE(fecha_hora) AS fecha, id_accion, COUNT(*) AS total
                FROM auditorias
                WHERE fecha_hora >= %s AND fecha_hora <= %s
                  AND modulo = 'Parámetros'
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
                if isinstance(fecha_reg, (datetime.datetime, datetime.date)):
                    f_str = fecha_reg.strftime("%Y-%m-%d")
                    f_date = fecha_reg.date() if isinstance(fecha_reg, datetime.datetime) else fecha_reg
                else:
                    f_str = str(fecha_reg)
                    f_date = datetime.datetime.strptime(f_str, "%Y-%m-%d").date()

                acc_id = f['id_accion']

                if f_str in labels_dias and acc_id in dataset:
                    if f_date >= fecha_inicio_sys:
                        dataset[acc_id]["valores"][f_str] = f['total']
        finally:
            cursor.close()

        return self._formatear_respuesta(labels_dias, dataset, id_accion_filtro)

    def obtener_estadisticas_mensuales(self, offset_periodo=0, id_accion_filtro=None):
        self._refrescar_transaccion()
        anio_actual = datetime.date.today().year + offset_periodo
        labels_meses = [f"{anio_actual}-{mes:02d}" for mes in range(1, 13)]

        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]

        dataset = {
            acc: {
                "id_accion": acc,
                "nombre": self.NOMBRES_ACCIONES.get(acc, f"Acción {acc}"),
                "color": self.COLORES_ACCIONES.get(acc, "#FFFFFF"),
                "valores": {m_str: 0 for m_str in labels_meses}
            }
            for acc in acciones_a_procesar
        }

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT DATE_FORMAT(fecha_hora, '%Y-%m') AS mes_str, id_accion, COUNT(*) AS total
                FROM auditorias
                WHERE YEAR(fecha_hora) = %s
                  AND modulo = 'Parámetros'
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

    def obtener_estadisticas_anuales(self, offset_periodo=0, id_accion_filtro=None):
        self._refrescar_transaccion()
        fecha_inicio_sys = self.obtener_fecha_inicio_sistema()
        anio_inicio = fecha_inicio_sys.year
        anio_actual = datetime.date.today().year + offset_periodo

        if anio_inicio > anio_actual:
            anio_inicio = anio_actual

        labels_anios = [str(a) for a in range(anio_inicio, anio_actual + 1)]

        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]

        dataset = {
            acc: {
                "id_accion": acc,
                "nombre": self.NOMBRES_ACCIONES.get(acc, f"Acción {acc}"),
                "color": self.COLORES_ACCIONES.get(acc, "#FFFFFF"),
                "valores": {a_str: 0 for a_str in labels_anios}
            }
            for acc in acciones_a_procesar
        }

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT YEAR(fecha_hora) AS anio_num, id_accion, COUNT(*) AS total
                FROM auditorias
                WHERE YEAR(fecha_hora) >= %s AND YEAR(fecha_hora) <= %s
                  AND modulo = 'Parámetros'
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