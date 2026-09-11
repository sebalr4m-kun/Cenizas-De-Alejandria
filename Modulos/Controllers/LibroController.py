import random
import string
import time
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMessageBox

from Modulos.Config import Conexion
from Modulos.Views.LibroViews import VistaLibro
from Modulos.Auditorias import auditoria_global

# Importación desacoplada del modelo MVC
try:
    from Modulos.Models.LibroModel import ModeloLibro
except ImportError:
    try:
        from Modulos.Models.LibroModel import LibroModel as ModeloLibro
    except ImportError:
        ModeloLibro = None


class ControladorLibro(QObject):
    # Emisión dual de señales para máxima sincronización en MainWindow
    libro_guardado = Signal()
    datos_actualizados = Signal()

    def __init__(self):
        super().__init__()
        self.conexion_obj = Conexion()
        self.bd = self.conexion_obj.obtener_conexion()
        self.modo = 'crear'

        # Instanciación segura del Modelo MVC
        if ModeloLibro:
            try:
                self.model = ModeloLibro()
            except Exception as e:
                print(f"[ADVERTENCIA] No se pudo instanciar ModeloLibro: {e}")
                self.model = None
        else:
            self.model = None

        # Referencias de la interfaz gráfica
        self.vista = None
        self.widget_vista = None
        self.widget_formulario = None
        self.tabla = None

    # ==================== CARGA Y OBTENCIÓN DE DATOS ====================

    def cargar_datos(self):
        """Obtiene la lista de libros con stock calculado para la tabla del catálogo"""
        if not self.vista:
            return
        try:
            # Sincronización cruzada: Limpia la transacción para asegurar datos frescos de Insumos
            if self.bd:
                self.bd.commit()

            libros = []
            if self.model and hasattr(self.model, 'obtener_todos'):
                libros = self.model.obtener_todos()
            elif self.model and hasattr(self.model, 'obtener_libros'):
                libros = self.model.obtener_libros()
            else:
                cursor = self.bd.cursor(dictionary=True)
                consulta = """
                    SELECT l.titulo, l.isbn, 
                           COALESCE(GROUP_CONCAT(DISTINCT a.nombre_completo SEPARATOR ', '), '-') AS autor, 
                           (SELECT COUNT(*) FROM insumos i 
                            WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3) AS stock,
                           (SELECT COUNT(*) FROM insumos i 
                            WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3 
                              AND i.estado = 'DISPONIBLE') AS cantidad_disponible
                    FROM libros l
                    LEFT JOIN libro_autor la ON l.id_libro = la.id_libro
                    LEFT JOIN param_autores a ON la.id_autor = a.id_autor
                    WHERE l.estado = 'ACTIVO'
                    GROUP BY l.id_libro, l.titulo, l.isbn
                    ORDER BY l.titulo
                """
                cursor.execute(consulta)
                libros = cursor.fetchall()
                cursor.close()

            self.vista.actualizar_tabla(libros)
        except Exception as e:
            print(f"Error crítico en controlador al cargar datos de libros: {e}")

    def obtener_todos(self):
        """Método de extracción utilizado para la exportación masiva en MainWindow"""
        try:
            if self.bd:
                self.bd.commit()

            if self.model and hasattr(self.model, 'obtener_todos'):
                return self.model.obtener_todos()
            elif self.model and hasattr(self.model, 'obtener_libros'):
                return self.model.obtener_libros()

            cursor = self.bd.cursor(dictionary=True)
            consulta = """
                SELECT l.titulo, l.isbn, 
                       COALESCE(GROUP_CONCAT(DISTINCT a.nombre_completo SEPARATOR ', '), '-') AS autor, 
                       (SELECT COUNT(*) FROM insumos i 
                        WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3) AS stock,
                       (SELECT COUNT(*) FROM insumos i 
                        WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3 
                          AND i.estado = 'DISPONIBLE') AS cantidad_disponible
                FROM libros l
                LEFT JOIN libro_autor la ON l.id_libro = la.id_libro
                LEFT JOIN param_autores a ON la.id_autor = a.id_autor
                WHERE l.estado = 'ACTIVO'
                GROUP BY l.id_libro, l.titulo, l.isbn
                ORDER BY l.titulo
            """
            cursor.execute(consulta)
            libros = cursor.fetchall()
            cursor.close()
            return libros
        except Exception as e:
            print(f"Error al obtener todos los libros: {e}")
            return []

    def obtener_por_isbn(self, isbn):
        """
        Busca un libro y recupera los IDs de sus relaciones paramétricas 
        para auto-completar el formulario de edición.
        """
        try:
            if self.bd:
                self.bd.commit()

            if self.model and hasattr(self.model, 'obtener_por_isbn'):
                return self.model.obtener_por_isbn(isbn)

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
            cursor.execute(consulta, (isbn,))
            resultado = cursor.fetchone()
            cursor.close()
            return resultado
        except Exception as e:
            print(f"Error al obtener libro por ISBN: {e}")
            return None

    # ==================== GESTIÓN DE RUNAS Y STOCK ====================

    def verificar_existencia_runa(self, clave_runa):
        """Verifica si una clave RUNA ya está registrada en la tabla insumos"""
        if self.model and hasattr(self.model, 'verificar_existencia_runa'):
            return self.model.verificar_existencia_runa(clave_runa)

        if not self.bd:
            return False
        self.bd.commit()
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT 1 FROM insumos WHERE clave_runa = %s", (clave_runa,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error en verificación de RUNA: {e}")
            return False
        finally:
            cursor.close()

    def generar_runa_unica(self):
        """Genera un código numérico único de 6 dígitos para cada ejemplar físico"""
        if self.model and hasattr(self.model, 'generar_runa_unica'):
            return self.model.generar_runa_unica()

        caracteres = string.digits
        longitud = 6
        for _ in range(100):
            runa = ''.join(random.choice(caracteres) for _ in range(longitud))
            if not self.verificar_existencia_runa(runa):
                return runa
        return str(int(time.time() * 1000000))[-longitud:]

    # ==================== OPERACIONES DE BASE DE DATOS ====================

    def guardar_bd(self, titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, estado, es_actualizacion):
        """Procesa el guardado lógico (Libros) y físico (Insumos)"""
        if self.model and hasattr(self.model, 'guardar_libro'):
            try:
                res = self.model.guardar_libro(titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, estado, es_actualizacion)
                self.finalizar_accion()
                return res
            except Exception as e:
                raise e

        cursor = self.bd.cursor()
        try:
            if es_actualizacion:
                cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
                fila = cursor.fetchone()
                if not fila:
                    raise Exception("Libro no encontrado para actualizar.")
                id_libro, titulo_ant = fila

                # Actualizar datos básicos
                cursor.execute("UPDATE libros SET titulo=%s, estado=%s WHERE id_libro=%s",
                               (titulo, estado, id_libro))
                auditoria_global.auditar_accion(2, "Libros", f"Actualización de libro ISBN: {isbn}")

                # Si el título cambió, actualizar registros de insumos vinculados
                if titulo_ant != titulo:
                    cursor.execute("UPDATE insumos SET titulo=%s WHERE titulo=%s AND id_tipo_insumo=3",
                                   (titulo, titulo_ant))
            else:
                # Insertar nuevo libro
                cursor.execute("INSERT INTO libros (titulo, isbn, estado) VALUES (%s, %s, 'ACTIVO')",
                               (titulo, isbn))
                id_libro = cursor.lastrowid
                auditoria_global.auditar_accion(1, "Libros", f"Creación de libro ISBN: {isbn}")

            # Actualizar relaciones paramétricas
            relaciones = [
                ('libro_autor', 'id_autor', id_autor),
                ('libro_editorial', 'id_editorial', id_editorial),
                ('libro_categoria', 'id_categoria', id_categoria),
                ('libro_genero', 'id_genero', id_genero)
            ]
            for tabla, col, id_val in relaciones:
                cursor.execute(f"DELETE FROM {tabla} WHERE id_libro=%s", (id_libro,))
                if id_val:
                    cursor.execute(f"INSERT INTO {tabla} (id_libro, {col}) VALUES (%s, %s)",
                                   (id_libro, id_val))

            # Sincronización de ejemplares físicos (Stock en Insumos)
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
                auditoria_global.auditar_accion(1, "Insumos", f"Agregados {diferencia} ejemplares físicos para el libro: {titulo}")
            elif diferencia < 0:
                # Eliminar solo ejemplares 'DISPONIBLE'
                cursor.execute("""
                    DELETE FROM insumos 
                    WHERE titulo=%s AND id_tipo_insumo=3 AND estado = 'DISPONIBLE' 
                    LIMIT %s
                """, (titulo, abs(diferencia)))
                auditoria_global.auditar_accion(4, "Insumos", f"Retirados {abs(diferencia)} ejemplares físicos del libro: {titulo}")

            self.bd.commit()
            self.finalizar_accion()

        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_todo(self, isbn):
        """Borrado físico completo de un libro y sus dependencias"""
        if self.model and hasattr(self.model, 'eliminar_libro'):
            try:
                res = self.model.eliminar_libro(isbn)
                self.finalizar_accion()
                return res
            except Exception as e:
                raise e

        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
            fila = cursor.fetchone()
            if not fila:
                raise Exception("No se encontró el libro a eliminar.")
            id_l, tit = fila

            # Limpiar relaciones paramétricas
            for t in ['libro_autor', 'libro_editorial', 'libro_categoria', 'libro_genero']:
                cursor.execute(f"DELETE FROM {t} WHERE id_libro=%s", (id_l,))

            # Limpiar ejemplares e información de libro
            cursor.execute("DELETE FROM insumos WHERE titulo = %s AND id_tipo_insumo = 3", (tit,))
            cursor.execute("DELETE FROM libros WHERE id_libro = %s", (id_l,))

            auditoria_global.auditar_accion(4, "Libros", f"Borrado físico total del libro ISBN: {isbn} y sus ejemplares")

            self.bd.commit()
            self.finalizar_accion()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    # ==================== MANEJO DE VISTAS Y FLUJO ====================

    def obtener_widget_vista(self):
        if not self.widget_vista:
            self.vista = VistaLibro(self)
            self.widget_vista = self.vista.construir_vista_catalogo()
            if hasattr(self.vista, 'tabla'):
                self.tabla = self.vista.tabla
            self.cargar_datos()
        return self.widget_vista

    def obtener_widget_formulario(self, ctrl_param):
        if not self.widget_formulario:
            if not self.vista:
                self.vista = VistaLibro(self)
            
            self.widget_formulario = self.vista.construir_formulario(ctrl_param)
            
            if hasattr(ctrl_param, 'parametro_guardado'):
                ctrl_param.parametro_guardado.connect(
                    lambda: self.vista._cargar_datos_combo(self.vista.combo_autor, "Autor", ctrl_param)
                )
                ctrl_param.parametro_guardado.connect(
                    lambda: self.vista._cargar_datos_combo(self.vista.combo_editorial, "Editorial", ctrl_param)
                )
        return self.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        """Resetea el formulario al estado inicial (oculto y modo creación)"""
        if self.vista:
            self.vista.establecer_modo('crear', inicial=True)
            if hasattr(self.vista, 'limpiar_formulario'):
                self.vista.limpiar_formulario()

    def finalizar_accion(self):
        """Refresca los datos locales y notifica al sistema global"""
        self.cargar_datos()
        self.libro_guardado.emit()
        self.datos_actualizados.emit()