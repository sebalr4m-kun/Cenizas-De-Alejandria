from PySide6.QtCore import Signal, QObject 
from Modulos.Config import Conexion
from Modulos.Views.LibroViews import VistaLibro
import random
import string
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSpinBox
)

class ControladorLibro(QObject): 
    libro_guardado = Signal() 
    
    def __init__(self):
        super().__init__() 
        self.bd = Conexion().obtener_conexion()
        self.modo = 'crear'
        
        # FIX: Inicializar tabla como None para evitar AttributeError
        self.tabla = None
        
        # Instanciamos la Vista pasándole este controlador
        self.vista = VistaLibro(self)
        
        # Mantenemos las referencias a los widgets para no romper MainWindow.py
        self.widget_vista = None
        self.widget_formulario = None
    
    def cargar_datos(self):
        """Consulta la base de datos y refresca la tabla de libros"""
        if not hasattr(self, 'tabla') or self.tabla is None:
            return

        try:
            cursor = self.bd.cursor(dictionary=True)
            # CORRECCIÓN: Eliminado l.stock y l.estado_libro. Usamos COUNT y l.estado.
            consulta = """
                SELECT l.titulo, l.isbn, 
                       COALESCE(GROUP_CONCAT(DISTINCT a.nombre_completo SEPARATOR ', '), '-') AS autor, 
                       e.nombre_editorial AS editorial, 
                       (SELECT COUNT(*) FROM insumos i WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3) AS stock, 
                       l.estado
                FROM libros l
                LEFT JOIN libro_autor la ON l.id_libro = la.id_libro
                LEFT JOIN param_autores a ON la.id_autor = a.id_autor
                LEFT JOIN libro_editorial le ON l.id_libro = le.id_libro
                LEFT JOIN editoriales e ON le.id_editorial = e.id_editorial
                WHERE l.estado != 'ELIMINADA'
                GROUP BY l.id_libro, l.titulo, l.isbn, e.nombre_editorial, l.estado
            """
            cursor.execute(consulta)
            libros = cursor.fetchall()
            cursor.close()

            self.tabla.setRowCount(0)
            for row_number, libro in enumerate(libros):
                self.tabla.insertRow(row_number)
                self.tabla.setItem(row_number, 0, QTableWidgetItem(str(libro['titulo'])))
                self.tabla.setItem(row_number, 1, QTableWidgetItem(str(libro['isbn'])))
                self.tabla.setItem(row_number, 2, QTableWidgetItem(str(libro['autor'])))
                self.tabla.setItem(row_number, 3, QTableWidgetItem(str(libro['editorial'] if libro['editorial'] else "-")))
                self.tabla.setItem(row_number, 4, QTableWidgetItem(str(libro['stock'])))
                self.tabla.setItem(row_number, 5, QTableWidgetItem(str(libro['estado'])))
        except Exception as e:
            print(f"Error al cargar libros: {e}")

    # --- MÉTODOS DE LÓGICA Y BASE DE DATOS ---

    def verificar_existencia_runa(self, clave_runa):
        cursor = self.bd.cursor()
        cursor.execute("SELECT 1 FROM insumos WHERE clave_runa = %s", (clave_runa,))
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe

    def generar_runa_unica(self):
        caracteres = string.digits
        longitud = 6
        for _ in range(100): 
            runa = ''.join(random.choice(caracteres) for _ in range(longitud))
            if not self.verificar_existencia_runa(runa):
                return runa
        return str(int(time.time() * 1000000))[-longitud:]

    def obtener_todos(self):
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
             SELECT l.titulo, l.isbn, 
                    COALESCE(GROUP_CONCAT(DISTINCT a.nombre_completo SEPARATOR ', '), '-') AS Autor,
                    COALESCE(COUNT(i.clave_runa), 0) AS Stock,
                    COALESCE(SUM(CASE WHEN i.estado = 'DISPONIBLE' THEN 1 ELSE 0 END), 0) AS Cantidad_Disponible
             FROM libros l
             LEFT JOIN libro_autor la ON l.id_libro = la.id_libro
             LEFT JOIN param_autores a ON la.id_autor = a.id_autor
             LEFT JOIN insumos i ON i.titulo = l.titulo AND i.id_tipo_insumo = 3
             WHERE l.estado = 'ACTIVO' 
             GROUP BY l.id_libro, l.titulo, l.isbn
        """
        cursor.execute(consulta)
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_por_isbn(self, isbn):
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
             SELECT l.*, 
                    (SELECT COUNT(*) FROM insumos i WHERE i.titulo = l.titulo AND i.id_tipo_insumo = 3) AS stock_total,
                    GROUP_CONCAT(DISTINCT la.id_autor) AS autores,
                    GROUP_CONCAT(DISTINCT le.id_editorial) AS editoriales,
                    GROUP_CONCAT(DISTINCT lc.id_categoria) AS categorias,
                    GROUP_CONCAT(DISTINCT lg.id_genero) AS generos
             FROM libros l
             LEFT JOIN libro_autor la ON l.id_libro = la.id_libro
             LEFT JOIN libro_editorial le ON l.id_libro = le.id_libro
             LEFT JOIN libro_categoria lc ON l.id_libro = lc.id_libro
             LEFT JOIN libro_genero lg ON l.id_libro = lg.id_libro
             WHERE l.isbn = %s
             GROUP BY l.id_libro, l.titulo, l.isbn
        """
        cursor.execute(consulta, (isbn,))
        resultado = cursor.fetchone()
        cursor.close()
        
        if resultado:
            for key in ['autores', 'editoriales', 'categorias', 'generos']:
                val = resultado.get(key)
                if val:
                    resultado[f'primer_id_{key[:-1]}'] = int(str(val).split(',')[0])
                else:
                    resultado[f'primer_id_{key[:-1]}'] = None
        return resultado

    def guardar_bd(self, titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, estado, es_actualizacion):
        cursor = self.bd.cursor()
        try:
            if es_actualizacion:
                cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
                fila = cursor.fetchone()
                if not fila: raise Exception("Libro no encontrado.")
                id_libro, titulo_ant = fila
                cursor.execute("UPDATE libros SET titulo=%s, estado=%s WHERE id_libro=%s", (titulo, estado, id_libro)) 
                if titulo_ant != titulo:
                    cursor.execute("UPDATE insumos SET titulo=%s WHERE titulo=%s AND id_tipo_insumo=3", (titulo, titulo_ant))
            else:
                cursor.execute("INSERT INTO libros (titulo, isbn, estado) VALUES (%s, %s, 'ACTIVO')", (titulo, isbn))
                id_libro = cursor.lastrowid

            # Relaciones Paramétricas
            for tabla, col, id_val in [('libro_autor', 'id_autor', id_autor), 
                                       ('libro_editorial', 'id_editorial', id_editorial),
                                       ('libro_categoria', 'id_categoria', id_categoria),
                                       ('libro_genero', 'id_genero', id_genero)]:
                cursor.execute(f"DELETE FROM {tabla} WHERE id_libro=%s", (id_libro,))
                if id_val: cursor.execute(f"INSERT INTO {tabla} (id_libro, {col}) VALUES (%s, %s)", (id_libro, id_val))
            
            # Gestión de Stock (Insumos)
            cursor.execute("SELECT COUNT(*) FROM insumos WHERE titulo=%s AND id_tipo_insumo=3", (titulo,))
            stock_actual = cursor.fetchone()[0]
            diferencia = stock - stock_actual
            
            if diferencia > 0:
                for _ in range(diferencia):
                    runa = self.generar_runa_unica()
                    cursor.execute("INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa) VALUES (%s, 3, 'DISPONIBLE', CURDATE(), %s)", (titulo, runa))
            elif diferencia < 0:
                cursor.execute("DELETE FROM insumos WHERE titulo=%s AND id_tipo_insumo=3 AND estado = 'DISPONIBLE' LIMIT %s", (titulo, abs(diferencia)))
            
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_todo(self, isbn): 
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
            fila = cursor.fetchone()
            if not fila: raise Exception("No encontrado.")
            id_l, tit = fila
            for t in ['libro_autor', 'libro_editorial', 'libro_categoria', 'libro_genero']:
                cursor.execute(f"DELETE FROM {t} WHERE id_libro=%s", (id_l,))
            cursor.execute("DELETE FROM insumos WHERE titulo = %s AND id_tipo_insumo = 3", (tit,))
            cursor.execute("DELETE FROM libros WHERE id_libro = %s", (id_l,))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def obtener_widget_vista(self):
        if not self.widget_vista:
            self.widget_vista = self.vista.construir_vista_catalogo()
        return self.widget_vista

    def obtener_widget_formulario(self, ctrl_param):
        if not self.widget_formulario:
            self.widget_formulario = self.vista.construir_formulario(ctrl_param)
            ctrl_param.parametro_guardado.connect(lambda: self.vista.actualizar_combos(ctrl_param))
        return self.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        if self.vista.widget_contenido_formulario:
            self.vista.widget_contenido_formulario.hide() 
        self.vista.establecer_modo('crear', inicial=True)