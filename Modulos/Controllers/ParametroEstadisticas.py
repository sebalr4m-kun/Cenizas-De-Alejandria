# ==========================================
# Archivo: Modulos/Controllers/ParametroEstadisticas.py
# ==========================================
import datetime
from datetime import timedelta
from Modulos.Config import Conexion

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