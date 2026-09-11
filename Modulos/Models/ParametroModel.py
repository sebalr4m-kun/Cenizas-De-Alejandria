from Modulos.Config import Conexion

class ParametroModel:
    def __init__(self):
        self.conexion = Conexion()

    def _obtener_mapa_param(self, rubro):
        """
        MAPA MAESTRO: Asocia de forma exacta cada rubro de la interfaz de usuario 
        con su respectiva tabla, columna identificadora (ID) y columna nominal en la BD.
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

    def obtener_todos(self, rubro_filtro="Todos"):
        """
        Retorna los registros con ALIAS universales ('id', 'nombre') para evitar KeyErrors.
        Soporta la carga del panel general mediante un UNION ALL de todas las tablas.
        """
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor(dictionary=True)
        
        # Consultas estandarizadas para que los Controladores siempre lean 'id' y 'nombre'
        consultas = {
            "Tipo Usuario": "SELECT id_tipo_usuario AS id, nombre AS nombre, 'Tipo Usuario' AS rubro, estado, admitido, permisos FROM param_tipos_usuario",
            "Tipo Insumo": "SELECT id_tipo_insumo AS id, nombre AS nombre, 'Tipo Insumo' AS rubro, estado, NULL AS admitido, NULL AS permisos FROM param_tipos_insumo",
            "Autor": "SELECT id_autor AS id, nombre_completo AS nombre, 'Autor' AS rubro, estado, NULL AS admitido, NULL AS permisos FROM param_autores",
            "Editorial": "SELECT id_editorial AS id, nombre_editorial AS nombre, 'Editorial' AS rubro, estado, NULL AS admitido, NULL AS permisos FROM editoriales",
            "Categoría": "SELECT id_categoria AS id, nombre_categoria AS nombre, 'Categoría' AS rubro, estado, NULL AS admitido, NULL AS permisos FROM categorias_catalogo",
            "Género": "SELECT id_genero AS id, nombre_genero AS nombre, 'Género' AS rubro, estado, NULL AS admitido, NULL AS permisos FROM generos"
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
        except Exception as e:
            raise e
        finally:
            cursor.close()

    def obtener_lista_activos(self, rubro):
        """
        Retorna únicamente los registros 'ACTIVOS'.
        Aplica los alias 'AS id' y 'AS nombre' para prevenir el KeyError en los QComboBox.
        """
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        if not tabla:
            return []

        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor(dictionary=True)
        try:
            consulta = f"""
                SELECT {col_id} AS id, {col_nombre} AS nombre 
                FROM {tabla} 
                WHERE estado IN ('ACTIVO', 'ACTIVA')
                ORDER BY {col_nombre} ASC
            """
            cursor.execute(consulta)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error crítico en obtener_lista_activos para {rubro}: {e}")
            return []
        finally:
            cursor.close()

    def obtener_por_id(self, rubro, id_param):
        """
        Retorna un único registro filtrado por su ID.
        """
        tabla, col_id, _ = self._obtener_mapa_param(rubro)
        if not tabla:
            return None

        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor(dictionary=True)
        try:
            consulta = f"SELECT * FROM {tabla} WHERE {col_id} = %s"
            cursor.execute(consulta, (id_param,))
            return cursor.fetchone()
        except Exception as e:
            raise e
        finally:
            cursor.close()

    def obtener_info_por_nombre(self, rubro, nombre):
        """
        Busca un registro por su nombre exacto y añade el atributo genérico 'id'.
        """
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        if not tabla:
            return None
            
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor(dictionary=True)
        try:
            consulta = f"SELECT * FROM {tabla} WHERE {col_nombre} = %s"
            cursor.execute(consulta, (nombre,))
            fila = cursor.fetchone()
            if fila:
                fila['id'] = fila[col_id] # Inyección genérica preventiva
            return fila
        except Exception as e:
            raise e
        finally:
            cursor.close()

    def guardar(self, rubro, nombre, estado='ACTIVO', editar=False, id_param=None, admitido=None, permisos=None):
        """
        Maneja la creación y actualización de parámetros integrando los campos JSON.
        """
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        if not tabla:
            raise ValueError(f"Rubro '{rubro}' no válido para guardar.")

        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor()
        try:
            if editar:
                if id_param is None:
                    raise ValueError("Debe proporcionar el ID del parámetro para efectuar la edición.")
                
                cursor.execute(f"SELECT {col_id} FROM {tabla} WHERE {col_nombre} = %s AND {col_id} != %s", (nombre, id_param))
                if cursor.fetchone():
                    raise Exception(f"El nombre '{nombre}' ya se encuentra registrado en otro elemento de {rubro}.")

                if rubro == "Tipo Usuario":
                    val_admitido = 1 if admitido else 0
                    val_permisos = permisos if permisos else "{}"
                    consulta = f"UPDATE {tabla} SET {col_nombre} = %s, estado = %s, admitido = %s, permisos = %s WHERE {col_id} = %s"
                    cursor.execute(consulta, (nombre, estado, val_admitido, val_permisos, id_param))
                else:
                    consulta = f"UPDATE {tabla} SET {col_nombre} = %s, estado = %s WHERE {col_id} = %s"
                    cursor.execute(consulta, (nombre, estado, id_param))
            else:
                cursor.execute(f"SELECT {col_id} FROM {tabla} WHERE {col_nombre} = %s", (nombre,))
                if cursor.fetchone():
                    raise Exception(f"El nombre '{nombre}' ya existe en el rubro {rubro}.")

                if rubro == "Tipo Usuario":
                    val_admitido = 1 if admitido else 0
                    val_permisos = permisos if permisos else "{}"
                    consulta = f"INSERT INTO {tabla} ({col_nombre}, estado, admitido, permisos) VALUES (%s, %s, %s, %s)"
                    cursor.execute(consulta, (nombre, 'ACTIVO', val_admitido, val_permisos))
                else:
                    consulta = f"INSERT INTO {tabla} ({col_nombre}, estado) VALUES (%s, %s)"
                    cursor.execute(consulta, (nombre, 'ACTIVO'))

            bd.commit()
        except Exception as e:
            bd.rollback()
            raise e
        finally:
            cursor.close()

    def inactivar_parametro_y_dependientes(self, rubro, id_param):
        """
        Soft-delete en cascada que propaga la restricción a registros vinculados.
        """
        tabla, col_id, _ = self._obtener_mapa_param(rubro)
        if not tabla: 
            raise ValueError(f"Rubro '{rubro}' no válido para inactivación.")
            
        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor()
        try:
            cursor.execute(f"UPDATE {tabla} SET estado = 'INACTIVO' WHERE {col_id} = %s", (id_param,))
            self._propagar_inactivacion(cursor, rubro, id_param)
            bd.commit()
        except Exception as e:
            bd.rollback()
            raise e
        finally:
            cursor.close()

    def _propagar_inactivacion(self, cursor, rubro, id_param):
        if rubro == "Tipo Usuario":
            cursor.execute("UPDATE usuarios SET estado_cuenta = 'INACTIVA' WHERE id_tipo_usuario = %s", (id_param,))
        elif rubro == "Tipo Insumo":
            cursor.execute("UPDATE insumos SET estado = 'INACTIVA' WHERE id_tipo_insumo = %s", (id_param,))
        elif rubro == "Autor":
            cursor.execute("UPDATE libros SET estado = 'INACTIVO' WHERE id_libro IN (SELECT id_libro FROM libro_autor WHERE id_autor = %s)", (id_param,))
        elif rubro == "Editorial":
            cursor.execute("UPDATE libros SET estado = 'INACTIVO' WHERE id_libro IN (SELECT id_libro FROM libro_editorial WHERE id_editorial = %s)", (id_param,))
        elif rubro == "Categoría":
            cursor.execute("UPDATE libros SET estado = 'INACTIVO' WHERE id_libro IN (SELECT id_libro FROM libro_categoria WHERE id_categoria = %s)", (id_param,))
        elif rubro == "Género":
            cursor.execute("UPDATE libros SET estado = 'INACTIVO' WHERE id_libro IN (SELECT id_libro FROM libro_genero WHERE id_genero = %s)", (id_param,))

    def eliminar_fisicamente(self, rubro, id_param):
        """
        Borrado físico destructivo.
        """
        tabla, col_id, _ = self._obtener_mapa_param(rubro)
        if not tabla:
            raise ValueError(f"Rubro '{rubro}' no válido para eliminación física.")

        bd = self.conexion.obtener_conexion()
        cursor = bd.cursor()
        try:
            if rubro == "Tipo Usuario":
                cursor.execute("DELETE FROM usuarios WHERE id_tipo_usuario = %s", (id_param,))
            elif rubro == "Tipo Insumo":
                cursor.execute("DELETE FROM insumos WHERE id_tipo_insumo = %s", (id_param,))
            
            cursor.execute(f"DELETE FROM {tabla} WHERE {col_id} = %s", (id_param,))
            bd.commit()
        except Exception as e:
            bd.rollback()
            raise e
        finally:
            cursor.close()