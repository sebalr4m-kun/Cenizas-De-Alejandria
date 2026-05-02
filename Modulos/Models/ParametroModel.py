from Modulos.Config import Conexion

class ParametroModel:
    def __init__(self):
        self.conexion = Conexion()

    def _obtener_mapa_param(self, rubro):
        """
        MAPA MAESTRO: Define la relación entre el rubro de la UI y la BD.
        Asegúrate de que el ComboBox en la View use exactamente estos nombres.
        """
        MAPA = {
            "Tipo Usuario": ("param_tipos_usuario", "id_tipo_usuario", "nombre"),
            "Tipo Insumo": ("param_tipos_insumo", "id_tipo_insumo", "nombre"),
            "Autor": ("param_autores", "id_autor", "nombre_completo"),
            "Editorial": ("editoriales", "id_editorial", "nombre_editorial"),
            "Categoría": ("categorias_catalogo", "id_categoria", "nombre_categoria"),
            "Género": ("generos", "id_genero", "nombre_genero")
        }
        return MAPA.get(rubro, (None, None, None))

    def _propagar_inactivacion(self, rubro, id_param):
        """Pone en INACTIVA todos los registros que usan este parámetro"""
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor()
        try:
            # Sincronización con el rubro "Tipo Usuario"
            if rubro == "Tipo Usuario":
                cursor.execute("UPDATE usuarios SET estado_cuenta = 'INACTIVA' WHERE id_tipo_usuario = %s", (id_param,))
            elif rubro == "Tipo Insumo":
                cursor.execute("UPDATE insumos SET estado = 'INACTIVA' WHERE id_tipo_insumo = %s", (id_param,))
            elif rubro in ["Autor", "Editorial", "Categoría", "Género"]:
                # Lógica simplificada para libros mediante mapeo dinámico si fuera necesario, 
                # pero mantenemos tus queries específicas por seguridad.
                if rubro == "Autor":
                    cursor.execute("UPDATE libros l JOIN libro_autor la ON l.id_libro = la.id_libro SET l.estado = 'INACTIVA' WHERE la.id_autor = %s", (id_param,))
                elif rubro == "Editorial":
                    cursor.execute("UPDATE libros l JOIN libro_editorial le ON l.id_libro = le.id_libro SET l.estado = 'INACTIVA' WHERE le.id_editorial = %s", (id_param,))
                elif rubro == "Categoría":
                    cursor.execute("UPDATE libros l JOIN libro_categoria lc ON l.id_libro = lc.id_libro SET l.estado = 'INACTIVA' WHERE lc.id_categoria = %s", (id_param,))
                elif rubro == "Género":
                    cursor.execute("UPDATE libros l JOIN libro_genero lg ON l.id_libro = lg.id_libro SET l.estado = 'INACTIVA' WHERE lg.id_genero = %s", (id_param,))
            
            bd.commit()
        except Exception as e:
            bd.rollback()
            raise e
        finally:
            cursor.close()

    def obtener_info_por_nombre(self, rubro, nombre):
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        if not tabla: return None
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor(dictionary=True)
        try:
            consulta = f"SELECT {col_id} AS id, {col_nombre} AS nombre, '{rubro}' AS rubro, estado FROM {tabla} WHERE {col_nombre} = %s"
            cursor.execute(consulta, (nombre,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def obtener_lista_activos(self, rubro):
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        if not tabla: return []
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor(dictionary=True)
        try:
            cursor.execute(f"SELECT {col_id} as id, {col_nombre} as nombre FROM {tabla} WHERE estado='ACTIVO'")
            return cursor.fetchall()
        finally:
            cursor.close()

    def obtener_todos(self, rubro_filtro="Todos"):
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor(dictionary=True)
        
        # Diccionario de consultas sincronizado con las keys del MAPA
        consultas = {
            "Tipo Usuario": "SELECT id_tipo_usuario AS id, nombre, 'Tipo Usuario' AS rubro, estado FROM param_tipos_usuario",
            "Tipo Insumo": "SELECT id_tipo_insumo AS id, nombre, 'Tipo Insumo' AS rubro, estado FROM param_tipos_insumo",
            "Autor": "SELECT id_autor AS id, nombre_completo AS nombre, 'Autor' AS rubro, estado FROM param_autores",
            "Editorial": "SELECT id_editorial AS id, nombre_editorial AS nombre, 'Editorial' AS rubro, estado FROM editoriales",
            "Categoría": "SELECT id_categoria AS id, nombre_categoria AS nombre, 'Categoría' AS rubro, estado FROM categorias_catalogo",
            "Género": "SELECT id_genero AS id, nombre_genero AS nombre, 'Género' AS rubro, estado FROM generos"
        }
        
        try:
            if rubro_filtro == "Todos":
                consulta_final = " UNION ALL ".join(consultas.values())
                cursor.execute(consulta_final)
            elif rubro_filtro in consultas:
                cursor.execute(consultas[rubro_filtro])
            else:
                return []
            return cursor.fetchall()
        finally:
            cursor.close()

    def guardar(self, rubro, nombre, estado, es_actualizacion, id_param=None):
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        
        if not tabla: 
            raise ValueError(f"Error Crítico: El rubro '{rubro}' no existe en el mapa del modelo.")
            
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor()
        try:
            if es_actualizacion and id_param is not None:
                consulta = f"UPDATE {tabla} SET {col_nombre}=%s, estado=%s WHERE {col_id}=%s"
                cursor.execute(consulta, (nombre, estado, id_param))
            else:
                # Verificación de duplicados antes de insertar
                cursor.execute(f"SELECT {col_id} FROM {tabla} WHERE {col_nombre} = %s", (nombre,))
                if cursor.fetchone():
                    raise Exception(f"El nombre '{nombre}' ya existe en {rubro}.")
                
                consulta = f"INSERT INTO {tabla} ({col_nombre}, estado) VALUES (%s, %s)"
                cursor.execute(consulta, (nombre, 'ACTIVO'))
            
            bd.commit()
        except Exception as e:
            bd.rollback()
            raise e
        finally:
            cursor.close()

    def inactivar_parametro_y_dependientes(self, rubro, id_param):
        """Soft-delete con cascade: pone el parámetro en INACTIVO y propaga"""
        tabla, col_id, _ = self._obtener_mapa_param(rubro)
        if not tabla: 
            raise ValueError(f"Rubro '{rubro}' no válido para inactivación.")
            
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor()
        try:
            # Actualizar el estado del parámetro a 'INACTIVO' (o 'INACTIVA' según tu estándar de BD)
            # Nota: Asegúrate si en la BD usas 'INACTIVO' o 'INACTIVA'.
            cursor.execute(f"UPDATE {tabla} SET estado = 'INACTIVO' WHERE {col_id} = %s", (id_param,))
            
            # Propagar a los registros que dependen de este parámetro
            self._propagar_inactivacion(rubro, id_param)
            
            bd.commit()
        except Exception as e:
            bd.rollback()
            raise e
        finally:
            cursor.close()