from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMessageBox

from Modulos.Config import Conexion
from Modulos.Views.LibroViews import VistaLibro
import random
import string
import time


class ControladorLibro(QObject):
    libro_guardado = Signal()  # Señal para notificar cambios a MainWindow

    def __init__(self):
        super().__init__()
        self.bd = Conexion().obtener_conexion()
        self.modo = 'crear'

        # Referencias
        self.vista = None
        self.widget_vista = None
        self.widget_formulario = None
        self.tabla = None

    # ==================== CARGA DE DATOS (SOLO LÓGICA) ====================
    def cargar_datos(self):
        """Obtiene la lista de libros con stock calculado para la tabla del catálogo"""
        if not self.vista: return
        try:
            # Sincronización cruzada: Limpia la transacción para asegurar datos frescos de Insumos
            self.bd.commit() 
            
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
            print(f"Error crítico en controlador al cargar datos: {e}")

    def obtener_por_isbn(self, isbn):
        """
        Busca un libro y recupera los IDs de sus relaciones paramétricas 
        para auto-completar el formulario de edición.
        """
        try:
            # Sincronización cruzada: Limpia la transacción para asegurar datos frescos
            self.bd.commit() 
            
            cursor = self.bd.cursor(dictionary=True)
            # SE CORRIGIÓ EL ERROR TIPOGRÁFICO: id_libro = l.id_libro (antes decía l.id_categoria)
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
        cursor = self.bd.cursor()
        try:
            if es_actualizacion:
                cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
                fila = cursor.fetchone()
                if not fila: raise Exception("Libro no encontrado para actualizar.")
                id_libro, titulo_ant = fila

                # Actualizar datos básicos
                cursor.execute("UPDATE libros SET titulo=%s, estado=%s WHERE id_libro=%s",
                               (titulo, estado, id_libro))

                # Si el título cambió, debemos actualizar los registros de insumos vinculados
                if titulo_ant != titulo:
                    cursor.execute("UPDATE insumos SET titulo=%s WHERE titulo=%s AND id_tipo_insumo=3",
                                   (titulo, titulo_ant))
            else:
                # Insertar nuevo libro
                cursor.execute("INSERT INTO libros (titulo, isbn, estado) VALUES (%s, %s, 'ACTIVO')",
                               (titulo, isbn))
                id_libro = cursor.lastrowid

            # Actualizar relaciones (Autor, Editorial, Categoría, Género)
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

            # Sincronización de ejemplares físicos (Stock)
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
            elif diferencia < 0:
                # Eliminar solo los que están disponibles (no prestados)
                cursor.execute("""
                    DELETE FROM insumos 
                    WHERE titulo=%s AND id_tipo_insumo=3 AND estado = 'DISPONIBLE' 
                    LIMIT %s
                """, (titulo, abs(diferencia)))

            self.bd.commit()
            self.finalizar_accion()

        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_todo(self, isbn):
        """Borrado físico completo de un libro y sus dependencias"""
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
            fila = cursor.fetchone()
            if not fila: raise Exception("No se encontró el libro a eliminar.")
            id_l, tit = fila

            # Limpiar relaciones paramétricas
            for t in ['libro_autor', 'libro_editorial', 'libro_categoria', 'libro_genero']:
                cursor.execute(f"DELETE FROM {t} WHERE id_libro=%s", (id_l,))

            # Limpiar ejemplares e información de libro
            cursor.execute("DELETE FROM insumos WHERE titulo = %s AND id_tipo_insumo = 3", (tit,))
            cursor.execute("DELETE FROM libros WHERE id_libro = %s", (id_l,))

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
            # Asegurar que la vista esté instanciada
            if not self.vista:
                self.vista = VistaLibro(self)
            
            self.widget_formulario = self.vista.construir_formulario(ctrl_param)
            
            # Conexión para actualizar combos cuando se crean nuevos parámetros (Autores, etc.)
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