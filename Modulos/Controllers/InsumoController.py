from PySide6.QtCore import Qt, Signal, QObject 
from Modulos.Config import Conexion
from Modulos.Views.InsumoViews import VistaTablaInsumo, FormularioInsumo
from PySide6.QtWidgets import QMessageBox
import random
import string

class ControladorInsumo(QObject): 
    datos_actualizados = Signal()

    def __init__(self):
        super().__init__()
        self.bd = Conexion().obtener_conexion()
        self.ctrl_param = None
        
        # Referencias a las vistas (Lazy loading)
        self.widget_vista = None
        self.widget_formulario = None
        
    # --- LÓGICA DE BASE DE DATOS Y ABM ---
    
    def verificar_existencia_runa(self, clave_runa):
        cursor = self.bd.cursor()
        cursor.execute("SELECT 1 FROM insumos WHERE clave_runa = %s", (clave_runa,))
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe

    def generar_runa_unica(self):
        caracteres = string.ascii_uppercase
        longitud = 5
        for _ in range(100): 
            runa = ''.join(random.choice(caracteres) for _ in range(longitud))
            if not self.verificar_existencia_runa(runa):
                return runa
        raise Exception("No se pudo generar una Clave RUNA única.")

    def obtener_todos(self):
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
        cursor.execute(consulta)
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_uno(self, clave_runa):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT * FROM insumos WHERE clave_runa=%s", (clave_runa,))
        res = cursor.fetchone()
        cursor.close()
        return res

    def guardar_bd(self, titulo, id_tipo, fecha, estado, clave_runa, es_actualizacion):
        cursor = self.bd.cursor()
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
            self.bd.commit()
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

    # --- MÉTODOS DE INTEGRACIÓN (PUENTE) ---

    def cargar_datos(self):
        if self.widget_vista:
            datos = self.obtener_todos()
            self.widget_vista.actualizar_datos(datos)

    def obtener_widget_vista(self):
        if not self.widget_vista:
            self.widget_vista = VistaTablaInsumo(self)
            self.cargar_datos()
        return self.widget_vista

    def obtener_widget_formulario(self, ctrl_param):
        self.ctrl_param = ctrl_param
        if not self.widget_formulario:
            self.widget_formulario = FormularioInsumo(self)
            # FIX: Corregido el nombre de la señal de 'parameter_guardado' a 'parametro_guardado'
            self.ctrl_param.parametro_guardado.connect(self.cargar_combos)
            self.cargar_combos()
        return self.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        if self.widget_formulario:
            self.widget_formulario.widget_contenido.hide()
            self.widget_formulario.establecer_modo('crear', inicial=True)

    def cargar_combos(self):
        if not self.ctrl_param or not self.widget_formulario: return
        self.widget_formulario.combo_cat.clear()
        
        # Obtenemos la lista de activos desde el modelo del controlador de parámetros
        cats = self.ctrl_param.model.obtener_lista_activos("Tipo Insumo")
        
        for c in cats:
            self.widget_formulario.combo_cat.addItem(c['nombre'], c['id']) 

    def manejar_guardado(self, datos):
        modo = datos['modo']
        titulo = datos['titulo']
        id_tipo = datos['id_tipo']
        
        if not titulo or id_tipo is None:
            QMessageBox.warning(None, "Error", "Título y Categoría requeridos")
            return
            
        if modo == 'crear':
            if self.es_libro(id_tipo):
                QMessageBox.warning(None, "Error", "No se pueden crear libros aquí. Use el módulo 'Libros'.")
                return

            import datetime
            fecha_adq = datetime.date.today().strftime("%Y-%m-%d")
            try:
                clave_runa = self.generar_runa_unica()
                self.guardar_bd(titulo, id_tipo, fecha_adq, "DISPONIBLE", clave_runa, False)
                QMessageBox.information(None, "Éxito", f"Insumo creado: {clave_runa}")
                self.finalizar_accion()
            except Exception as e:
                QMessageBox.critical(None, "Error", str(e))
                
        else: # MODO EDICIÓN
            clave_runa = datos['clave_runa']
            if not clave_runa: return

            item = self.obtener_uno(clave_runa)
            if not item: return
            
            estado_frontend = datos['estado_ui']
            es_libro = self.es_libro(item.get('id_tipo_insumo'))
            
            titulo_guardar = item.get('titulo') if es_libro else titulo
            id_tipo_guardar = item.get('id_tipo_insumo') if es_libro else id_tipo
            fecha_guardar = item.get('fecha_adquisicion') if es_libro else datos['fecha_ui']

            try:
                if estado_frontend == 'ELIMINADA':
                    self.eliminar_fisico(clave_runa)
                    QMessageBox.information(None, "Info", "Eliminado físicamente.")
                else:
                    estado_bd = "INACTIVA" if estado_frontend == 'SUSPENDIDA' else estado_frontend
                    self.guardar_bd(titulo_guardar, id_tipo_guardar, fecha_guardar, estado_bd, clave_runa, True) 
                    QMessageBox.information(None, "Info", f"Actualizado.")
                
                self.finalizar_accion()
            except Exception as e:
                QMessageBox.critical(None, "Error", str(e))

    def finalizar_accion(self):
        self.datos_actualizados.emit()
        self.cargar_datos()
        if self.widget_formulario:
            self.widget_formulario.limpiar()