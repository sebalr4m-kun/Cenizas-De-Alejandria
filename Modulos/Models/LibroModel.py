from Modulos.Config import Conexion

class LibroModel:
    def __init__(self):
        self.conexion_bd = Conexion()
        self.bd = self.conexion_bd.obtener_conexion()

    def verificar_existencia_runa(self, clave_runa):
        """Verifica si una RUNA ya existe en la tabla de insumos."""
        cursor = self.bd.cursor()
        cursor.execute("SELECT 1 FROM insumos WHERE clave_runa = %s", (clave_runa,))
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe

    def obtener_todos_libros(self):
        """Recupera la lista completa de libros con su stock y disponibilidad calculada."""
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
             WHERE l.estado = 'ACTIVO' 
             GROUP BY l.id_libro, l.titulo, l.isbn, l.estado
        """
        cursor.execute(consulta)
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_libro_por_isbn(self, isbn):
        """Obtiene la información detallada de un libro. Se evitan columnas inexistentes."""
        cursor = self.bd.cursor(dictionary=True)
        # Especificamos las columnas reales de la tabla libros para evitar el error 1054
        consulta = """
             SELECT l.id_libro, l.titulo, l.isbn, l.estado,
                    (SELECT COUNT(*) FROM insumos i WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3) AS stock_total,
                    (SELECT id_autor FROM libro_autor WHERE id_libro = l.id_libro LIMIT 1) AS primer_id_autor,
                    (SELECT id_editorial FROM libro_editorial WHERE id_libro = l.id_libro LIMIT 1) AS primer_id_editorial,
                    (SELECT id_categoria FROM libro_categoria WHERE id_libro = l.id_libro LIMIT 1) AS primer_id_categoria,
                    (SELECT id_genero FROM libro_genero WHERE id_libro = l.id_libro LIMIT 1) AS primer_id_genero
             FROM libros l
             WHERE l.isbn = %s
        """
        cursor.execute(consulta, (isbn,))
        resultado = cursor.fetchone()
        cursor.close()
        return resultado

    def guardar_libro_db(self, datos_libro, es_actualizacion):
        """Maneja la persistencia del libro y sus relaciones."""
        cursor = self.bd.cursor()
        try:
            titulo = datos_libro['titulo']
            isbn = datos_libro['isbn']
            estado = datos_libro['estado']
            stock_objetivo = datos_libro.get('stock', 0)

            if es_actualizacion:
                cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
                fila = cursor.fetchone()
                if not fila: raise Exception("Libro no encontrado.")
                id_libro, titulo_anterior = fila
                
                cursor.execute("UPDATE libros SET titulo=%s, estado=%s WHERE id_libro=%s", (titulo, estado, id_libro)) 
                if titulo_anterior != titulo:
                    cursor.execute("UPDATE insumos SET titulo=%s WHERE titulo=%s AND id_tipo_insumo=3", (titulo, titulo_anterior))
            else:
                cursor.execute("INSERT INTO libros (titulo, isbn, estado) VALUES (%s, %s, 'ACTIVO')", (titulo, isbn))
                id_libro = cursor.lastrowid

            self._actualizar_relaciones(cursor, id_libro, datos_libro)

            # Cálculo de diferencia de stock para el Controlador
            cursor.execute("SELECT COUNT(*) FROM insumos WHERE titulo=%s AND id_tipo_insumo=3", (titulo,))
            stock_actual = cursor.fetchone()[0]
            diferencia = stock_objetivo - stock_actual
            
            self.bd.commit()
            return id_libro, diferencia
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def _actualizar_relaciones(self, cursor, id_libro, datos):
        """Actualiza las tablas intermedias de relaciones."""
        tablas = {
            'libro_autor': ('id_autor', datos.get('id_autor')),
            'libro_editorial': ('id_editorial', datos.get('id_editorial')),
            'libro_categoria': ('id_categoria', datos.get('id_categoria')),
            'libro_genero': ('id_genero', datos.get('id_genero'))
        }
        for tabla, (columna, valor) in tablas.items():
            cursor.execute(f"DELETE FROM {tabla} WHERE id_libro=%s", (id_libro,))
            if valor:
                cursor.execute(f"INSERT INTO {tabla} (id_libro, {columna}) VALUES (%s, %s)", (id_libro, valor))

    def insertar_insumo_libro(self, titulo, runa):
        """Inserta una unidad física (insumo) de un libro."""
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
        """Elimina el libro y sus dependencias."""
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
            fila = cursor.fetchone()
            if not fila: raise Exception("Libro no encontrado.")
            id_libro, titulo = fila
            
            relaciones = ['libro_autor', 'libro_editorial', 'libro_categoria', 'libro_genero']
            for tabla in relaciones:
                cursor.execute(f"DELETE FROM {tabla} WHERE id_libro=%s", (id_libro,))
            
            cursor.execute("DELETE FROM insumos WHERE titulo = %s AND id_tipo_insumo = 3", (titulo,))
            cursor.execute("DELETE FROM libros WHERE id_libro = %s", (id_libro,))
            
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()