from Modulos.Config import Conexion
from datetime import datetime
import random
import string

class InsumoModel:
    def __init__(self):
        """
        Gestiona la persistencia y consultas de los insumos en la base de datos.
        Se comunica con: Modulos.Config.Conexion
        """
        self.conexion_bd = Conexion().obtener_conexion()

    def verificar_existencia_runa(self, clave_runa):
        """
        Verifica si una clave RUNA ya está registrada.
        Llamada por: generar_runa_unica, manejar_guardado (vía Controlador)
        """
        cursor = self.conexion_bd.cursor()
        cursor.execute("SELECT 1 FROM insumos WHERE clave_runa = %s", (clave_runa,))
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe

    def obtener_todos_insumos(self):
        """
        Recupera el listado completo de insumos activos con sus categorías.
        Llamada por: cargar_datos (vía Controlador)
        """
        cursor = self.conexion_bd.cursor(dictionary=True)
        consulta = """
            SELECT i.titulo AS 'Titulo', 
                   i.clave_runa AS 'Clave RUNA', 
                   COALESCE(t.nombre, 'Sin categoría') AS Categoria,
                   i.estado AS Estado, 
                   DATE_FORMAT(i.fecha_adquisicion, '%Y-%m-%d') AS Adquisicion,
                   i.id_tipo_insumo
            FROM insumos i
            LEFT JOIN param_tipos_insumo t ON i.id_tipo_insumo = t.id_tipo_insumo
            WHERE i.estado != 'INACTIVA' 
            ORDER BY i.titulo
        """
        cursor.execute(consulta)
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_insumo_por_runa(self, clave_runa):
        """
        Obtiene los detalles de un insumo específico.
        Llamada por: intentar_cargar_edicion, manejar_guardado (vía Controlador)
        """
        cursor = self.conexion_bd.cursor(dictionary=True)
        cursor.execute("SELECT * FROM insumos WHERE clave_runa=%s", (clave_runa,))
        res = cursor.fetchone()
        cursor.close()
        return res

    def registrar_o_actualizar_insumo(self, titulo, id_tipo, fecha, estado, clave_runa, es_actualizacion):
        """
        Inserta un nuevo registro o actualiza uno existente.
        Llamada por: manejar_guardado (vía Controlador)
        """
        cursor = self.conexion_bd.cursor()
        try:
            if es_actualizacion:
                cursor.execute("""
                    UPDATE insumos SET estado=%s, titulo=%s, id_tipo_insumo=%s, fecha_adquisicion=%s
                    WHERE clave_runa=%s
                """, (estado, titulo, id_tipo, fecha, clave_runa))
            else:
                cursor.execute("""
                    INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa)
                    VALUES (%s, %s, %s, %s, %s)
                """, (titulo, id_tipo, estado, fecha, clave_runa))
            self.conexion_bd.commit()
        except Exception as e:
            self.conexion_bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_insumo_fisico(self, clave_runa):
        """
        Elimina permanentemente un insumo de la base de datos.
        Llamada por: manejar_guardado (vía Controlador)
        """
        cursor = self.conexion_bd.cursor()
        try:
            cursor.execute("DELETE FROM insumos WHERE clave_runa=%s", (clave_runa,))
            self.conexion_bd.commit()
        except Exception as e:
            self.conexion_bd.rollback()
            raise e
        finally:
            cursor.close()

    def es_tipo_libro(self, id_tipo):
        """
        Identificador lógico para diferenciar libros de otros insumos.
        Llamada por: intentar_cargar_edicion, manejar_guardado (vía Controlador)
        """
        return id_tipo == 3

    def solicitar_categorias_parametros(self, ctrl_param):
        """
        Solicita las categorías disponibles al controlador de parámetros.
        Llamada a: Modulos.ParametroController.obtener_tipos_insumo
        """
        if not ctrl_param:
            return []
        return ctrl_param.obtener_tipos_insumo()