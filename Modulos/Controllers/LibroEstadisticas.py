# ==========================================
# Archivo: Modulos/Controllers/LibroEstadisticas.py
# ==========================================
import datetime
from datetime import timedelta
import calendar
from Modulos.Config import Conexion

class LibroEstadisticas:
    """
    Controlador estadístico dedicado al módulo de Libros.
    Ofrece vistas temporales de auditoría (flujo) y vistas estáticas del catálogo con soporte de subfiltros.
    """

    COLORES_ACCIONES = {
        1: "#00E676",  # Crear -> Verde Neón
        2: "#00B0FF",  # Modificar -> Azul Celeste
        3: "#FF9100",  # Borrado Lógico -> Naranja
        4: "#FF1744"   # Borrado Físico -> Rojo
    }

    NOMBRES_ACCIONES = {
        1: "Crear",
        2: "Modificar",
        3: "Inactivar",
        4: "Borrado Físico"
    }

    COLORES_ESTADOS = {
        "ACTIVO": "#00E676",
        "INACTIVO": "#7F8C8D",
        "SUSPENDIDO": "#FF9100"
    }
    
    COLORES_PARAMETROS = [
        "#00B0FF", "#E040FB", "#1DE9B6", "#FFEA00", "#FF3D00", "#76FF03", "#FF4081", "#D500F9"
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
        acciones = [{"id": None, "nombre": "Auditoría: Todas las Acciones"}]
        for id_acc, nombre in self.NOMBRES_ACCIONES.items():
            acciones.append({
                "id": id_acc,
                "nombre": f"Auditoría: {nombre} ({id_acc})"
            })
        acciones.append({"id": "autores", "nombre": "Catálogo: Top Libros por Autor"})
        acciones.append({"id": "editoriales", "nombre": "Catálogo: Top Libros por Editorial"})
        acciones.append({"id": "categorias", "nombre": "Catálogo: Libros por Categoría"})
        acciones.append({"id": "generos", "nombre": "Catálogo: Libros por Género"})
        acciones.append({"id": "estados", "nombre": "Catálogo: Estados Operativos"})
        return acciones

    def obtener_subfiltros_disponibles(self, id_accion=None):
        self._refrescar_transaccion()
        filtros = []
        cursor = self.bd.cursor(dictionary=True)
        try:
            if id_accion == "autores":
                filtros.append({"id": None, "nombre": "Todos los Autores"})
                cursor.execute("SELECT id_autor as id, nombre_completo as nombre FROM param_autores")
            elif id_accion == "editoriales":
                filtros.append({"id": None, "nombre": "Todas las Editoriales"})
                cursor.execute("SELECT id_editorial as id, nombre_editorial as nombre FROM editoriales")
            elif id_accion == "categorias":
                filtros.append({"id": None, "nombre": "Todas las Categorías"})
                cursor.execute("SELECT id_categoria as id, nombre_categoria as nombre FROM categorias_catalogo")
            elif id_accion == "generos":
                filtros.append({"id": None, "nombre": "Todos los Géneros"})
                cursor.execute("SELECT id_genero as id, nombre_genero as nombre FROM generos")
            else:
                return []
            
            for fila in cursor.fetchall():
                filtros.append(fila)
        except Exception as e:
            pass
        finally:
            cursor.close()
        return filtros

    def obtener_fecha_inicio_sistema(self):
        self._refrescar_transaccion()
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT MIN(fecha_hora) FROM auditorias WHERE modulo = 'Libros'")
            res = cursor.fetchone()
            if res and res[0]:
                fecha = res[0]
                return fecha.date() if isinstance(fecha, datetime.datetime) else fecha
            return datetime.date.today()
        finally:
            cursor.close()

    def obtener_reporte_estadistico(self, agrupacion="Por Semana", offset_periodo=0, id_accion_filtro=None, id_subfiltro=None):
        
        if id_accion_filtro == "autores":
            return self._generar_reporte_parametros("param_autores", "libro_autor", "id_autor", "nombre_completo", "Densidad de Autores", id_subfiltro)
        elif id_accion_filtro == "editoriales":
            return self._generar_reporte_parametros("editoriales", "libro_editorial", "id_editorial", "nombre_editorial", "Distribución por Editorial", id_subfiltro)
        elif id_accion_filtro == "categorias":
            return self._generar_reporte_parametros("categorias_catalogo", "libro_categoria", "id_categoria", "nombre_categoria", "Clasificación por Categorías", id_subfiltro)
        elif id_accion_filtro == "generos":
            return self._generar_reporte_parametros("generos", "libro_genero", "id_genero", "nombre_genero", "Distribución por Géneros Literarios", id_subfiltro)
        elif id_accion_filtro == "estados":
            return self._generar_reporte_estados()

        if agrupacion in ["Por Día", "Por Semana"]:
            datos = self.obtener_estadisticas_semanales(offset_periodo, id_accion_filtro)
        elif agrupacion == "Por Mes":
            datos = self.obtener_estadisticas_mensuales(offset_periodo, id_accion_filtro)
        elif agrupacion == "Por Año":
            datos = self.obtener_estadisticas_anuales(offset_periodo, id_accion_filtro)
        else:
            datos = self.obtener_estadisticas_semanales(offset_periodo, id_accion_filtro)

        nombre_accion = self.NOMBRES_ACCIONES.get(id_accion_filtro, "Todas las Acciones") if isinstance(id_accion_filtro, int) else "Todas las Acciones"
        titulo = f"Auditoría de Flujo - Libros ({nombre_accion}) [{agrupacion}]"
        
        if offset_periodo != 0:
            titulo += f" (Offset: {offset_periodo})"

        datos["titulo"] = titulo
        return datos

    def _generar_reporte_parametros(self, tabla_param, tabla_puente, col_id, col_nombre, titulo_grafico, id_subfiltro=None):
        self._refrescar_transaccion()
        cursor = self.bd.cursor(dictionary=True)
        series = []
        try:
            if id_subfiltro:
                sql = f"""
                    SELECT l.titulo as nombre, 
                           (SELECT COUNT(*) FROM insumos i WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3) as total
                    FROM libros l
                    INNER JOIN {tabla_puente} p ON l.id_libro = p.id_libro
                    WHERE p.{col_id} = %s
                    ORDER BY total DESC, l.titulo ASC
                    LIMIT 30
                """
                cursor.execute(sql, (id_subfiltro,))
                filas = cursor.fetchall()
                
                color_idx = 0
                for f in filas:
                    color = self.COLORES_PARAMETROS[color_idx % len(self.COLORES_PARAMETROS)]
                    nombre_corto = f['nombre'][:20] + "..." if len(f['nombre']) > 20 else f['nombre']
                    series.append({
                        "id_accion": "libro",
                        "nombre": nombre_corto,
                        "color_barra": color,
                        "color_texto": self.COLOR_TEXTO_MODO_NEGRO,
                        "datos": [f['total']]
                    })
                    color_idx += 1
                
                titulo_final = f"{titulo_grafico} (Desglose Específico)"
                eje_x_label = "Títulos del Elemento Seleccionado"
            else:
                sql = f"""
                    SELECT p.{col_nombre} as nombre, COUNT(l.id_libro) as total
                    FROM {tabla_param} p
                    LEFT JOIN {tabla_puente} l ON p.{col_id} = l.{col_id}
                    GROUP BY p.{col_id}, p.{col_nombre}
                    ORDER BY total DESC, p.{col_nombre} ASC
                    LIMIT 20
                """
                cursor.execute(sql)
                filas = cursor.fetchall()
                
                color_idx = 0
                for f in filas:
                    color = self.COLORES_PARAMETROS[color_idx % len(self.COLORES_PARAMETROS)]
                    series.append({
                        "id_accion": "parametro",
                        "nombre": f['nombre'],
                        "color_barra": color,
                        "color_texto": self.COLOR_TEXTO_MODO_NEGRO,
                        "datos": [f['total']]
                    })
                    color_idx += 1
                
                titulo_final = f"{titulo_grafico} (Top 20 General)"
                eje_x_label = "Entidades Registradas en Catálogo"
        finally:
            cursor.close()

        return {
            "modo_grafico": "agrupado_lado_a_lado",
            "estilo_base": {"fondo": self.COLOR_FONDO_MODO_NEGRO, "texto": self.COLOR_TEXTO_MODO_NEGRO},
            "eje_x": [eje_x_label],
            "series": series,
            "titulo": titulo_final
        }

    def _generar_reporte_estados(self):
        self._refrescar_transaccion()
        cursor = self.bd.cursor(dictionary=True)
        series = []
        try:
            sql = "SELECT estado, COUNT(id_libro) as total FROM libros GROUP BY estado"
            cursor.execute(sql)
            filas = cursor.fetchall()
            
            color_idx = 0
            for f in filas:
                estado_str = str(f['estado']).upper()
                color = self.COLORES_ESTADOS.get(estado_str, self.COLORES_PARAMETROS[color_idx % len(self.COLORES_PARAMETROS)])
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

        return {
            "modo_grafico": "agrupado_lado_a_lado",
            "estilo_base": {"fondo": self.COLOR_FONDO_MODO_NEGRO, "texto": self.COLOR_TEXTO_MODO_NEGRO},
            "eje_x": ["Estados Actuales de Títulos"],
            "series": series,
            "titulo": "Metadatos - Estados Operativos del Catálogo"
        }

    def obtener_estadisticas_semanales(self, offset_periodo=0, id_accion_filtro=None):
        self._refrescar_transaccion()
        base_date = datetime.date.today() + timedelta(weeks=offset_periodo)
        hace_6_dias = base_date - timedelta(days=6)
        
        dias_rango = [hace_6_dias + timedelta(days=i) for i in range(7)]
        labels_dias = [d.strftime("%Y-%m-%d") for d in dias_rango]

        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]
        dataset = self._preparar_dataset(acciones_a_procesar, labels_dias)

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT DATE(fecha_hora) as dia, id_accion, COUNT(*) as cantidad
                FROM auditorias
                WHERE modulo = 'Libros' 
                  AND DATE(fecha_hora) >= %s 
                  AND DATE(fecha_hora) <= %s
            """
            params = [hace_6_dias, base_date]
            if id_accion_filtro:
                sql += " AND id_accion = %s"
                params.append(id_accion_filtro)
            sql += " GROUP BY DATE(fecha_hora), id_accion"
            
            cursor.execute(sql, tuple(params))
            for fila in cursor.fetchall():
                dia_str = str(fila['dia'])
                if dia_str in labels_dias:
                    idx = labels_dias.index(dia_str)
                    if fila['id_accion'] in dataset:
                        dataset[fila['id_accion']][idx] = fila['cantidad']
        finally:
            cursor.close()

        return self._formatear_respuesta(labels_dias, dataset, acciones_a_procesar)

    def obtener_estadisticas_mensuales(self, offset_periodo=0, id_accion_filtro=None):
        self._refrescar_transaccion()
        hoy = datetime.date.today()
        mes_actual = hoy.replace(day=1)
        
        for _ in range(abs(offset_periodo)):
            if offset_periodo < 0:
                mes_actual = (mes_actual - timedelta(days=1)).replace(day=1)
            else:
                siguiente = mes_actual.replace(day=28) + timedelta(days=4)
                mes_actual = siguiente.replace(day=1)

        _, dias_en_mes = calendar.monthrange(mes_actual.year, mes_actual.month)
        fecha_fin = mes_actual.replace(day=dias_en_mes)

        labels_dias = [(mes_actual + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(dias_en_mes)]
        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]
        dataset = self._preparar_dataset(acciones_a_procesar, labels_dias)

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT DATE(fecha_hora) as dia, id_accion, COUNT(*) as cantidad
                FROM auditorias
                WHERE modulo = 'Libros' 
                  AND DATE(fecha_hora) >= %s 
                  AND DATE(fecha_hora) <= %s
            """
            params = [mes_actual, fecha_fin]
            if id_accion_filtro:
                sql += " AND id_accion = %s"
                params.append(id_accion_filtro)
            sql += " GROUP BY DATE(fecha_hora), id_accion"
            
            cursor.execute(sql, tuple(params))
            for fila in cursor.fetchall():
                dia_str = str(fila['dia'])
                if dia_str in labels_dias:
                    idx = labels_dias.index(dia_str)
                    if fila['id_accion'] in dataset:
                        dataset[fila['id_accion']][idx] = fila['cantidad']
        finally:
            cursor.close()

        return self._formatear_respuesta(labels_dias, dataset, acciones_a_procesar)

    def obtener_estadisticas_anuales(self, offset_periodo=0, id_accion_filtro=None):
        self._refrescar_transaccion()
        ano_actual = datetime.date.today().year + offset_periodo
        
        labels_meses = [f"{ano_actual}-{str(m).zfill(2)}" for m in range(1, 13)]
        acciones_a_procesar = [id_accion_filtro] if id_accion_filtro else [1, 2, 3, 4]
        dataset = self._preparar_dataset(acciones_a_procesar, labels_meses)

        cursor = self.bd.cursor(dictionary=True)
        try:
            sql = """
                SELECT DATE_FORMAT(fecha_hora, '%Y-%m') as mes, id_accion, COUNT(*) as cantidad
                FROM auditorias
                WHERE modulo = 'Libros' AND YEAR(fecha_hora) = %s
            """
            params = [ano_actual]
            if id_accion_filtro:
                sql += " AND id_accion = %s"
                params.append(id_accion_filtro)
            sql += " GROUP BY DATE_FORMAT(fecha_hora, '%Y-%m'), id_accion"
            
            cursor.execute(sql, tuple(params))
            for fila in cursor.fetchall():
                mes_str = str(fila['mes'])
                if mes_str in labels_meses:
                    idx = labels_meses.index(mes_str)
                    if fila['id_accion'] in dataset:
                        dataset[fila['id_accion']][idx] = fila['cantidad']
        finally:
            cursor.close()

        return self._formatear_respuesta(labels_meses, dataset, acciones_a_procesar)

    def _preparar_dataset(self, acciones, labels):
        return {acc: [0]*len(labels) for acc in acciones}

    def _formatear_respuesta(self, eje_x, dataset, acciones_a_procesar):
        series = []
        for acc in acciones_a_procesar:
            series.append({
                "id_accion": acc,
                "nombre": self.NOMBRES_ACCIONES.get(acc, "Desconocida"),
                "color_barra": self.COLORES_ACCIONES.get(acc, "#FFFFFF"),
                "color_texto": self.COLOR_TEXTO_MODO_NEGRO,
                "datos": dataset[acc]
            })

        return {
            "modo_grafico": "apilado",
            "estilo_base": {"fondo": self.COLOR_FONDO_MODO_NEGRO, "texto": self.COLOR_TEXTO_MODO_NEGRO},
            "eje_x": eje_x,
            "series": series
        }