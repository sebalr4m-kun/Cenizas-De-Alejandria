# ==========================================
# Archivo: Modulos/Controllers/InsumoEstadisticas.py
# ==========================================
import datetime
from datetime import timedelta
import calendar
from Modulos.Config import Conexion

class InsumoEstadisticas:
    """
    Controlador estadístico dedicado al módulo de Insumos.
    Ofrece vistas temporales de auditoría (flujo) y vistas estáticas de inventario físico.
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

    def __init__(self):
        self.conexion_obj = Conexion()
        self.bd = self.conexion_obj.obtener_conexion()

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

    def obtener_subfiltros_disponibles(self):
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

    def obtener_reporte_estadistico(self, agrupacion="Por Semana", offset_periodo=0, id_accion_filtro=None, id_subfiltro=None):
        """Punto de entrada. Enruta hacia la línea de tiempo (Auditoría) o fotografía estática (Inventario)."""
        
        # Enrutamiento de vistas estáticas de inventario
        if id_accion_filtro == "tipos":
            return self._generar_reporte_tipos()
        elif id_accion_filtro == "estados":
            return self._generar_reporte_estados(id_subfiltro)

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

    # =========================================================================
    # VISTAS ESTÁTICAS DE INVENTARIO
    # =========================================================================

    def _generar_reporte_tipos(self):
        self._refrescar_transaccion()
        cursor = self.bd.cursor(dictionary=True)
        series = []
        try:
            sql = """
                SELECT t.nombre, COUNT(i.id_insumo) as total
                FROM param_tipos_insumo t
                LEFT JOIN insumos i ON t.id_tipo_insumo = i.id_tipo_insumo
                GROUP BY t.id_tipo_insumo, t.nombre
            """
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

    def _generar_reporte_estados(self, id_subfiltro=None):
        self._refrescar_transaccion()
        cursor = self.bd.cursor(dictionary=True)
        series = []
        try:
            sql = "SELECT estado, COUNT(id_insumo) as total FROM insumos"
            params = []
            if id_subfiltro:
                sql += " WHERE id_tipo_insumo = %s"
                params.append(id_subfiltro)
            sql += " GROUP BY estado"
            
            cursor.execute(sql, tuple(params))
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

        titulo = "Estado Físico del Inventario (Filtrado)" if id_subfiltro else "Estado Físico del Inventario Global"
        return {
            "modo_grafico": "agrupado_lado_a_lado",
            "estilo_base": {"fondo": self.COLOR_FONDO_MODO_NEGRO, "texto": self.COLOR_TEXTO_MODO_NEGRO},
            "eje_x": ["Estados Actuales Registrados"],
            "series": series,
            "titulo": titulo
        }

    # =========================================================================
    # VISTAS TEMPORALES DE AUDITORÍA
    # =========================================================================

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
            if id_subfiltro:
                # El id_subfiltro aplica un Like sobre el elemento registrado de la auditoria
                # Asumiendo registro de formato, esto es una aproximación, aunque
                # es más útil en inventarios que en la tabla limpia de auditoría.
                pass

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