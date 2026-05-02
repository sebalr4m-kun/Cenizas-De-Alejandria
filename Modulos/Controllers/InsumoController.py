import string
import random
import datetime

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import QMessageBox

from Modulos.Config import Conexion
from Modulos.Views.InsumoViews import VistaTablaInsumo, FormularioInsumo


class ControladorInsumo(QObject):
    """
    Controlador central para el módulo de Insumos.
    Solo maneja lógica de negocio y datos. No toca UI directamente.
    """
    datos_actualizados = Signal()
    insumo_actualizado = Signal()

    def __init__(self):
        super().__init__()
        self.conexion_obj = Conexion()
        self.bd = self.conexion_obj.obtener_conexion()
        self.ctrl_param = None

        # Referencias a las vistas (Lazy loading)
        self.widget_vista = None
        self.widget_formulario = None

        # Bandera para evitar recursión
        self._esta_cargando = False

    # ====================== LÓGICA DE BASE DE DATOS ======================

    def verificar_existencia_runa(self, clave_runa):
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT 1 FROM insumos WHERE clave_runa = %s", (clave_runa,))
            existe = cursor.fetchone() is not None
            return existe
        except Exception as e:
            print(f"Error en verificación de RUNA: {e}")
            return False
        finally:
            cursor.close()

    def generar_runa_unica(self):
        caracteres = string.ascii_uppercase
        longitud = 5
        for _ in range(100):
            runa = ''.join(random.choice(caracteres) for _ in range(longitud))
            if not self.verificar_existencia_runa(runa):
                return runa
        raise Exception("Falla crítica: No se pudo generar una Clave RUNA única tras 100 intentos.")

    def obtener_todos(self):
        """Recupera todos los insumos activos."""
        cursor = self.bd.cursor(dictionary=True)
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
        try:
            cursor.execute(consulta)
            res = cursor.fetchall()
            return res
        except Exception as e:
            print(f"Error al obtener insumos: {e}")
            return []
        finally:
            cursor.close()

    def obtener_uno(self, clave_runa):
        cursor = self.bd.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM insumos WHERE clave_runa=%s", (clave_runa,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def guardar_bd(self, titulo, id_tipo, fecha, estado, clave_runa, es_actualizacion):
        cursor = self.bd.cursor()
        try:
            if es_actualizacion:
                consulta = """
                    UPDATE insumos 
                    SET estado=%s, titulo=%s, id_tipo_insumo=%s, fecha_adquisicion=%s
                    WHERE clave_runa=%s
                """
                cursor.execute(consulta, (estado, titulo, id_tipo, fecha, clave_runa))
            else:
                consulta = """
                    INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(consulta, (titulo, id_tipo, estado, fecha, clave_runa))

            self.bd.commit()
            self.insumo_actualizado.emit()  # Emitir señal después de guardar
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_fisico(self, clave_runa):
        cursor = self.bd.cursor()
        try:
            cursor.execute("DELETE FROM insumos WHERE clave_runa=%s", (clave_runa,))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def es_libro(self, id_tipo):
        return id_tipo == 3

    # ====================== MÉTODOS DE VISTA ======================

    def cargar_datos(self):
        """Obtiene los datos y le pide a la vista que los muestre"""
        if self._esta_cargando:
            return

        try:
            self._esta_cargando = True
            if self.widget_vista:
                datos = self.obtener_todos()
                self.widget_vista.actualizar_datos(datos)   # ← Llama a la vista
                self.datos_actualizados.emit()
        finally:
            self._esta_cargando = False

    def obtener_widget_vista(self):
        if not self.widget_vista:
            self.widget_vista = VistaTablaInsumo(self)
            self.cargar_datos()
        return self.widget_vista

    def obtener_widget_formulario(self, ctrl_param):
        self.ctrl_param = ctrl_param
        if not self.widget_formulario:
            self.widget_formulario = FormularioInsumo(self)

            if hasattr(self.ctrl_param, 'parametro_guardado'):
                self.ctrl_param.parametro_guardado.connect(self.cargar_combos)

            self.cargar_combos()
        return self.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        if self.widget_formulario:
            self.widget_formulario.widget_contenido.hide()
            self.widget_formulario.establecer_modo('crear', inicial=True)

    def cargar_combos(self):
        if not self.ctrl_param or not self.widget_formulario:
            return

        try:
            self.widget_formulario.combo_cat.clear()
            cats = self.ctrl_param.model.obtener_lista_activos("Tipo Insumo")
            for c in cats:
                self.widget_formulario.combo_cat.addItem(c['nombre'], c['id'])
        except Exception as e:
            print(f"Error al cargar combos de insumos: {e}")

    # ====================== MANEJADOR PRINCIPAL ======================

    def manejar_guardado(self, datos):
        modo = datos.get('modo', 'crear')
        titulo = datos.get('titulo')
        id_tipo = datos.get('id_tipo')

        if not titulo or id_tipo is None:
            QMessageBox.warning(None, "Validación", "El Título y la Categoría son campos obligatorios.")
            return

        if modo == 'crear':
            if self.es_libro(id_tipo):
                QMessageBox.warning(None, "Restricción de Flujo",
                                   "Los Libros deben gestionarse exclusivamente desde el módulo 'Libros (Clase)'.")
                return

            fecha_adq = datetime.date.today().strftime("%Y-%m-%d")
            try:
                clave_runa = self.generar_runa_unica()
                self.guardar_bd(titulo, id_tipo, fecha_adq, "DISPONIBLE", clave_runa, False)
                QMessageBox.information(None, "Éxito", f"Insumo registrado con éxito.\nRUNA: {clave_runa}")
                self.finalizar_accion()
            except Exception as e:
                QMessageBox.critical(None, "Error de Base de Datos", str(e))

        else:  # MODO EDICIÓN
            clave_runa = datos.get('clave_runa')
            if not clave_runa:
                return

            item_original = self.obtener_uno(clave_runa)
            if not item_original:
                return

            estado_frontend = datos.get('estado_ui')
            es_un_libro = self.es_libro(item_original.get('id_tipo_insumo'))

            titulo_final = item_original.get('titulo') if es_un_libro else titulo
            id_tipo_final = item_original.get('id_tipo_insumo') if es_un_libro else id_tipo
            fecha_final = item_original.get('fecha_adquisicion') if es_un_libro else datos.get('fecha_ui')

            try:
                if estado_frontend == 'ELIMINADA':
                    self.eliminar_fisico(clave_runa)
                    QMessageBox.information(None, "Registro Eliminado",
                                          f"El insumo {clave_runa} ha sido borrado físicamente.")
                else:
                    estado_bd = "INACTIVA" if estado_frontend == 'SUSPENDIDA' else estado_frontend
                    self.guardar_bd(titulo_final, id_tipo_final, fecha_final, estado_bd, clave_runa, True)
                    QMessageBox.information(None, "Actualización exitosa",
                                          "Los datos del insumo han sido actualizados.")

                self.finalizar_accion()
            except Exception as e:
                QMessageBox.critical(None, "Error en Actualización", str(e))

    def finalizar_accion(self):
        """Disparador maestro después de guardar o eliminar"""
        try:
            self.cargar_datos()                    # Actualiza su propia vista
            if self.widget_formulario:
                self.widget_formulario.limpiar()
                self.widget_formulario.widget_contenido.hide()

            self.datos_actualizados.emit()         # Notifica a MainWindow

        except Exception as e:
            print(f"Error en finalizar_accion de Insumo: {e}")
            
    def forzar_refresco_total(self):
        self.cargar_datos()
        self.cargar_combos()