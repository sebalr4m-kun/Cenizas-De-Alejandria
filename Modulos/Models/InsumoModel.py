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
        self.conexion_bd.commit() # CORRECCIÓN: Evita el Stale Snapshot
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
        self.conexion_bd.commit() # CORRECCIÓN: Evita el Stale Snapshot
        cursor = self.conexion_bd.cursor(dictionary=True)
        consulta = """
            SELECT i.titulo AS 'Titulo', 
                   i.clave_runa AS 'Clave RUNA', 
                   COALESCE(t.nombre, 'Sin categoría') AS Categoria,
                   i.estado AS Estado, 
                   DATE_FORMAT(i.fecha_adquisicion, '%Y-%m-%d') AS 'Fecha Adquisicion'
            FROM insumos i
            LEFT JOIN param_tipos_insumo t ON i.id_tipo_insumo = t.id_tipo_insumo
            WHERE i.estado != 'ELIMINADA'
            ORDER BY i.fecha_adquisicion DESC
        """
        cursor.execute(consulta)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados

    def obtener_insumo_por_runa(self, clave_runa):
        """
        Busca un insumo específico mediante su clave RUNA.
        Llamada por: intentar_cargar_edicion (vía Controlador)
        """
        self.conexion_bd.commit() # CORRECCIÓN: Evita el Stale Snapshot
        cursor = self.conexion_bd.cursor(dictionary=True)
        consulta = """
            SELECT titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa
            FROM insumos
            WHERE clave_runa = %s
        """
        cursor.execute(consulta, (clave_runa,))
        resultado = cursor.fetchone()
        cursor.close()
        return resultado

    def registrar_o_actualizar_insumo(self, modo, titulo, id_tipo, estado, fecha, clave_runa, anterior_runa=None):
        """
        Inserta un nuevo registro o actualiza uno existente en la tabla insumos.
        Llamada por: manejar_guardado (vía Controlador)
        """
        cursor = self.conexion_bd.cursor()
        try:
            if modo == 'editar':
                # Si se edita, se localiza por la clave RUNA previa o actual
                target_runa = anterior_runa if anterior_runa else clave_runa
                consulta = """
                    UPDATE insumos 
                    SET titulo = %s, id_tipo_insumo = %s, estado = %s, fecha_adquisicion = %s, clave_runa = %s
                    WHERE clave_runa = %s
                """
                cursor.execute(consulta, (titulo, id_tipo, estado, fecha, clave_runa, target_runa))
            else:
                # Modo crear
                consulta = """
                    INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(consulta, (titulo, id_tipo, estado, fecha, clave_runa))
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
        Llamada al iniciar el módulo para rellenar los combos de la vista.
        """
        if hasattr(ctrl_param, 'model'):
            # Obtiene los parámetros bajo el rubro exacto mapeado en la BD para tipos de insumo
            return ctrl_param.model.obtener_todos("Tipo Insumo")
        return []