from Modulos.Config import Conexion

class ParametroModel:
    def __init__(self):
        self.conexion = Conexion()

    def _obtener_mapa_param(self, rubro):
        # NORMALIZACIÓN: Mapeamos los nombres de la UI a las tablas reales
        # He cambiado "Categoría (Libro)" por "Categoría" para que coincida con tu ComboBox
        MAPA = {
            "Tipo Usuario": ("param_tipos_usuario", "id_tipo_usuario", "nombre"),
            "Tipo Insumo": ("param_tipos_insumo", "id_tipo_insumo", "nombre"),
            "Autor": ("param_autores", "id_autor", "nombre_completo"),
            "Editorial": ("editoriales", "id_editorial", "nombre_editorial"),
            "Categoría": ("categorias_catalogo", "id_categoria", "nombre_categoria"),
            "Género": ("generos", "id_genero", "nombre_genero")
        }
        return MAPA.get(rubro, (None, None, None))

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
        
        # Las claves aquí también deben coincidir con la UI
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
                # Verificación de duplicados
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

    def eliminar(self, rubro, id_param):
        tabla, col_id, _ = self._obtener_mapa_param(rubro)
        if not tabla: raise ValueError("Rubro no válido.")
            
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor()
        try:
            cursor.execute(f"DELETE FROM {tabla} WHERE {col_id} = %s", (id_param,))
            bd.commit()
        except Exception as e:
            bd.rollback()
            raise e
        finally:
            cursor.close()