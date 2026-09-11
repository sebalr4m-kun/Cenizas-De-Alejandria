import random
import string
import time
from Modulos.Config import Conexion
from Modulos.Auditorias import auditoria_global


class LibroModel:
    def __init__(self):
        self.conexion_bd = Conexion()
        self.bd = self.conexion_bd.obtener_conexion()

    # ==================== CONSULTAS Y LECTURA ====================

    def verificar_existencia_runa(self, clave_runa):
        """Verifica si una RUNA ya existe en la tabla de insumos."""
        if not self.bd:
            return False
        self.bd.commit()  # Sincronización cruzada para leer datos frescos
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT 1 FROM insumos WHERE clave_runa = %s", (clave_runa,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error en verificación de RUNA (Model): {e}")
            return False
        finally:
            cursor.close()

    def generar_runa_unica(self):
        """Genera un código numérico único de 6 dígitos para cada ejemplar físico."""
        caracteres = string.digits
        longitud = 6
        for _ in range(100):
            runa = ''.join(random.choice(caracteres) for _ in range(longitud))
            if not self.verificar_existencia_runa(runa):
                return runa
        return str(int(time.time() * 1000000))[-longitud:]

    def obtener_todos_libros(self):
        """Recupera la lista completa de libros con su stock y disponibilidad calculada."""
        if not self.bd:
            return []
        self.bd.commit()  # Asegura que los conteos de insumos reflejen cambios al instante
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
             SELECT l.id_libro, l.titulo, l.isbn, l.estado,
                    COALESCE(GROUP_CONCAT(DISTINCT a.nombre_completo SEPARATOR ', '), '-') AS autor,
                    (SELECT COUNT(*) FROM insumos i2 WHERE i2.titulo = l.titulo AND i2.id_tipo_insumo = 3) AS stock,
                    (SELECT COUNT(*) FROM insumos i3 WHERE i3.titulo = l.titulo AND i3.id_tipo_insumo = 3 AND i3.estado = 'DISPONIBLE') AS cantidad_disponible
             FROM libros l
             LEFT JOIN libro_autor la ON l.id_libro = la.id_libro
             LEFT JOIN param_autores a ON la.id_autor = a.id_autor
             WHERE l.estado = 'ACTIVO'
             GROUP BY l.id_libro, l.titulo, l.isbn, l.estado
             ORDER BY l.titulo
        """
        try:
            cursor.execute(consulta)
            res = cursor.fetchall()
            return res if res else []
        except Exception as e:
            print(f"Error al obtener libros en Modelo: {e}")
            return []
        finally:
            cursor.close()

    # Alias estandarizados para acoplamiento con ControladorLibro
    def obtener_todos(self):
        return self.obtener_todos_libros()

    def obtener_libros(self):
        return self.obtener_todos_libros()

    def obtener_por_isbn(self, isbn):
        """Busca un libro por ISBN y retorna sus datos junto con los IDs paramétricos."""
        if not self.bd:
            return None
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
             SELECT l.*, 
                    (SELECT COUNT(*) FROM insumos i WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3) AS stock_total,
                    (SELECT id_autor FROM libro_autor WHERE id_libro = l.id_libro LIMIT 1) AS primer_id_autor,
                    (SELECT id_editorial FROM libro_editorial WHERE id_libro = l.id_libro LIMIT 1) AS primer_id_editorial,
                    (SELECT id_categoria FROM libro_categoria WHERE id_libro = l.id_libro LIMIT 1) AS primer_id_categoria,
                    (SELECT id_genero FROM libro_genero WHERE id_libro = l.id_libro LIMIT 1) AS primer_id_genero
             FROM libros l
             WHERE l.isbn = %s
        """
        try:
            cursor.execute(consulta, (isbn,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener libro por ISBN en Modelo: {e}")
            return None
        finally:
            cursor.close()

    # ==================== OPERACIONES Y PERSISTENCIA ====================

    def guardar_libro(self, titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, estado, es_actualizacion):
        """
        Guarda o actualiza la entidad libro, gestiona las relaciones paramétricas
        y sincroniza automáticamente los ejemplares físicos en la tabla de insumos.
        """
        cursor = self.bd.cursor()
        try:
            if es_actualizacion:
                cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
                fila = cursor.fetchone()
                if not fila:
                    raise Exception("Libro no encontrado para actualizar.")
                id_libro, titulo_ant = fila

                # Actualización de datos maestros
                cursor.execute("UPDATE libros SET titulo=%s, estado=%s WHERE id_libro=%s",
                               (titulo, estado, id_libro))
                auditoria_global.auditar_accion(2, "Libros", f"Actualización de libro ISBN: {isbn}")

                # Propagación de cambio de título hacia la tabla general de insumos
                if titulo_ant != titulo:
                    cursor.execute("""
                        UPDATE insumos 
                        SET titulo = %s 
                        WHERE titulo = %s AND id_tipo_insumo = 3
                    """, (titulo, titulo_ant))

                # Propagación de estado si el libro pasa a INACTIVO
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
            else:
                # Inserción de nuevo registro maestro
                cursor.execute("""
                    INSERT INTO libros (titulo, isbn, estado) 
                    VALUES (%s, %s, %s)
                """, (titulo, isbn, estado if estado else 'ACTIVO'))
                id_libro = cursor.lastrowid
                auditoria_global.auditar_accion(1, "Libros", f"Creación de libro ISBN: {isbn}")

            # Sincronización de tablas relacionales intermedias
            relaciones = [
                ('libro_autor', 'id_autor', id_autor),
                ('libro_editorial', 'id_editorial', id_editorial),
                ('libro_categoria', 'id_categoria', id_categoria),
                ('libro_genero', 'id_genero', id_genero)
            ]
            for tabla, columna, id_val in relaciones:
                cursor.execute(f"DELETE FROM {tabla} WHERE id_libro = %s", (id_libro,))
                if id_val:
                    if isinstance(id_val, (list, tuple)):
                        for r_id in id_val:
                            cursor.execute(f"INSERT INTO {tabla} (id_libro, {columna}) VALUES (%s, %s)", (id_libro, r_id))
                    else:
                        cursor.execute(f"INSERT INTO {tabla} (id_libro, {columna}) VALUES (%s, %s)", (id_libro, id_val))

            # Ajuste dinámico de ejemplares físicos (Stock en Insumos)
            cursor.execute("SELECT COUNT(*) FROM insumos WHERE titulo=%s AND id_tipo_insumo=3", (titulo,))
            stock_actual = cursor.fetchone()[0]
            diferencia = stock - stock_actual

            if diferencia > 0:
                for _ in range(diferencia):
                    runa = self.generar_runa_unica()
                    cursor.execute("""
                        INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa)
                        VALUES (%s, 3, 'DISPONIBLE', CURDATE(), %s)
                    """, (titulo, runa))
                auditoria_global.auditar_accion(1, "Insumos", f"Agregados {diferencia} ejemplares para: {titulo}")
            elif diferencia < 0:
                cursor.execute("""
                    DELETE FROM insumos 
                    WHERE titulo=%s AND id_tipo_insumo=3 AND estado = 'DISPONIBLE' 
                    LIMIT %s
                """, (titulo, abs(diferencia)))
                auditoria_global.auditar_accion(4, "Insumos", f"Retirados {abs(diferencia)} ejemplares para: {titulo}")

            self.bd.commit()
            return id_libro
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def guardar_o_actualizar_libro(self, id_libro, titulo, isbn, estado, titulo_original=None, autor_ids=None, editorial_ids=None, categoria_ids=None, genero_ids=None):
        """Firma alternativa para mantener compatibilidad con implementaciones previas."""
        es_act = True if id_libro else False
        id_autor = autor_ids[0] if (isinstance(autor_ids, list) and autor_ids) else autor_ids
        id_editorial = editorial_ids[0] if (isinstance(editorial_ids, list) and editorial_ids) else editorial_ids
        id_categoria = categoria_ids[0] if (isinstance(categoria_ids, list) and categoria_ids) else categoria_ids
        id_genero = genero_ids[0] if (isinstance(genero_ids, list) and genero_ids) else genero_ids
        
        # Obtener el stock actual si no se pasa explícitamente
        cursor = self.bd.cursor()
        cursor.execute("SELECT COUNT(*) FROM insumos WHERE titulo=%s AND id_tipo_insumo=3", (titulo,))
        stock_val = cursor.fetchone()[0]
        cursor.close()

        return self.guardar_libro(titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock_val, estado, es_act)

    def agregar_unidades_libro_como_insumo(self, titulo, runa):
        """Registra un libro físico individual en la tabla general de insumos."""
        cursor = self.bd.cursor()
        try:
            cursor.execute("""
                INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa)
                VALUES (%s, 3, 'DISPONIBLE', CURDATE(), %s)
            """, (titulo, runa))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_insumos_disponibles(self, titulo, cantidad):
        """Elimina unidades físicas excedentes de insumos."""
        cursor = self.bd.cursor()
        try:
            cursor.execute("""
                DELETE FROM insumos 
                WHERE titulo=%s AND id_tipo_insumo=3 AND estado = 'DISPONIBLE' LIMIT %s
            """, (titulo, int(cantidad)))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_libro(self, isbn):
        """Elimina un libro y todas sus dependencias en cascada limpia."""
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
            fila = cursor.fetchone()
            if not fila:
                raise Exception("Libro no encontrado para eliminar.")
            id_libro, titulo = fila

            # Limpieza en tablas asociativas
            for tabla in ['libro_autor', 'libro_editorial', 'libro_categoria', 'libro_genero']:
                cursor.execute(f"DELETE FROM {tabla} WHERE id_libro=%s", (id_libro,))

            # Eliminación de ejemplares vinculados en insumos
            cursor.execute("DELETE FROM insumos WHERE titulo = %s AND id_tipo_insumo = 3", (titulo,))

            # Eliminación del registro maestro
            cursor.execute("DELETE FROM libros WHERE id_libro = %s", (id_libro,))

            auditoria_global.auditar_accion(4, "Libros", f"Borrado físico total del libro ISBN: {isbn}")
            self.bd.commit()
            return True
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_libro_db(self, isbn):
        """Alias para mantener compatibilidad técnica con llamadas legadas."""
        return self.eliminar_libro(isbn)