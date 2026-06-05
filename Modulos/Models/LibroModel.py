from Modulos.Config import Conexion

class LibroModel:
    def __init__(self):
        self.conexion_bd = Conexion()
        self.bd = self.conexion_bd.obtener_conexion()

    def verificar_existencia_runa(self, clave_runa):
        """Verifica si una RUNA ya existe en la tabla de insumos."""
        self.bd.commit()  # <--- Sincronización cruzada: limpia caché para leer datos frescos en tiempo real
        cursor = self.bd.cursor()
        cursor.execute("SELECT 1 FROM insumos WHERE clave_runa = %s", (clave_runa,))
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe

    def obtener_todos_libros(self):
        """Recupera la lista completa de libros con su stock y disponibilidad calculada."""
        self.bd.commit()  # <--- Cruce absoluto: asegura que los conteos de insumos reflejen cambios externos al instante
        cursor = self.bd.cursor(dictionary=True)
        # Eliminamos cualquier referencia a l.stock y usamos el COUNT de insumos
        consulta = """
             SELECT l.id_libro, l.titulo, l.isbn, l.estado,
                    COALESCE(GROUP_CONCAT(DISTINCT a.nombre_completo SEPARATOR ', '), '-') AS Autor,
                    (SELECT COUNT(*) FROM insumos i2 WHERE i2.titulo = l.titulo AND i2.id_tipo_insumo = 3) AS Stock,
                    (SELECT COUNT(*) FROM insumos i3 WHERE i3.titulo = l.titulo AND i3.id_tipo_insumo = 3 AND i3.estado = 'DISPONIBLE') AS Cantidad_Disponible
             FROM libros l
             LEFT JOIN libro_autor la ON l.id_libro = la.id_libro
             LEFT JOIN param_autores a ON la.id_autor = a.id_autor
             GROUP BY l.id_libro
        """
        cursor.execute(consulta)
        res = cursor.fetchall()
        cursor.close()
        return res

    def guardar_o_actualizar_libro(self, id_libro, titulo, isbn, estado, titulo_original=None, autor_ids=None, editorial_ids=None, categoria_ids=None, genero_ids=None):
        """
        Guarda o actualiza un libro y propaga obligatoriamente los cambios de forma cruzada 
        hacia la tabla general de insumos para mantener la integridad en conjunto.
        """
        cursor = self.bd.cursor()
        try:
            if id_libro:
                # 1. ACTUALIZACIÓN CRUZADA DE TÍTULO: Si el nombre del libro cambió, se propaga a todas sus copias físicas en insumos
                if titulo_original and titulo_original != titulo:
                    cursor.execute("""
                        UPDATE insumos 
                        SET titulo = %s 
                        WHERE titulo = %s AND id_tipo_insumo = 3
                    """, (titulo, titulo_original))
                
                # 2. ACTUALIZACIÓN CRUZADA DE ESTADOS: Sincroniza la disponibilidad general del ítem
                if estado in ('INACTIVO', 'INACTIVA', 'SUSPENDIDA'):
                    cursor.execute("""
                        UPDATE insumos 
                        SET estado = 'INACTIVO' 
                        WHERE titulo = %s AND id_tipo_insumo = 3
                    """, (titulo,))
                elif estado in ('ACTIVO', 'ACTIVA', 'DISPONIBLE'):
                    cursor.execute("""
                        UPDATE insumos 
                        SET estado = 'DISPONIBLE' 
                        WHERE titulo = %s AND id_tipo_insumo = 3 AND estado = 'INACTIVO'
                    """, (titulo,))

                # Actualizar entidad raíz del libro
                cursor.execute("""
                    UPDATE libros 
                    SET titulo = %s, isbn = %s, estado = %s 
                    WHERE id_libro = %s
                """, (titulo, isbn, estado, id_libro))
            else:
                # Insertar libro nuevo
                cursor.execute("""
                    INSERT INTO libros (titulo, isbn, estado) 
                    VALUES (%s, %s, %s)
                """, (titulo, isbn, estado))
                id_libro = cursor.lastrowid

            # 3. Sincronización de tablas intermedias (RBAC / Relacionales) si se especifican arrays de IDs
            tablas_relacionales = [
                ('libro_autor', 'id_autor', autor_ids),
                ('libro_editorial', 'id_editorial', editorial_ids),
                ('libro_categoria', 'id_categoria', categoria_ids),
                ('libro_genero', 'id_genero', genero_ids)
            ]
            
            for tabla, columna, ids in tablas_relacionales:
                if ids is not None:
                    cursor.execute(f"DELETE FROM {tabla} WHERE id_libro = %s", (id_libro,))
                    for rel_id in ids:
                        cursor.execute(f"INSERT INTO {tabla} (id_libro, {columna}) VALUES (%s, %s)", (id_libro, rel_id))

            self.bd.commit()
            return id_libro
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def agregar_unidades_libro_como_insumo(self, titulo, runa):
        """Registra un libro físico individual en la tabla general de insumos."""
        cursor = self.bd.cursor()
        cursor.execute("""
            INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa)
            VALUES (%s, 3, 'DISPONIBLE', CURDATE(), %s)
        """, (titulo, runa))
        self.bd.commit()
        cursor.close()

    def eliminar_insumos_disponibles(self, titulo, cantidad):
        """Elimina unidades físicas excedentes."""
        cursor = self.bd.cursor()
        cursor.execute("""
            DELETE FROM insumos 
            WHERE titulo=%s AND id_tipo_insumo=3 AND estado = 'DISPONIBLE' LIMIT %s
        """, (titulo, int(cantidad)))
        self.bd.commit()
        cursor.close()

    def eliminar_libro_db(self, isbn):
        """Elimina el libro y sus dependencias de forma destructiva limpia."""
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
            fila = cursor.fetchone()
            if not fila: 
                raise Exception("Libro no encontrado.")
            id_libro, titulo = fila
            
            # Limpieza cruzada de tablas relacionales asociativas
            relaciones = ['libro_autor', 'libro_editorial', 'libro_categoria', 'libro_genero']
            for tabla in relaciones:
                cursor.execute(f"DELETE FROM {tabla} WHERE id_libro=%s", (id_libro,))
            
            # Sincronización cruzada: eliminar copias físicas ligadas en insumos
            cursor.execute("DELETE FROM insumos WHERE titulo = %s AND id_tipo_insumo = 3", (titulo,))
            
            # Eliminar registro maestro del libro
            cursor.execute("DELETE FROM libros WHERE id_libro = %s", (id_libro,))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()