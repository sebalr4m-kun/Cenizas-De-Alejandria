from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate, Signal, QObject 
from Modulos.Config import Conexion
from datetime import datetime
import random
import string

class ControladorInsumo(QObject): 
    datos_actualizados = Signal()

    def __init__(self):
        super().__init__()
        self.bd = Conexion().obtener_conexion()
        self.ctrl_param = None
        self.widget_vista = None
        self.widget_formulario = None
        self.widget_contenido_formulario = None 
        self.tabla = None
        self.modo = 'crear'
        
        self.etiqueta_fecha = None
        self.entrada_fecha = None
        self.etiqueta_estado = None
        self.combo_estado = None
        self.combo_cat = None
        self.entrada_nombre = None
        self.etiqueta_runa = None
        self.entrada_runa = None
        
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

    def cargar_datos(self, *args):
        datos = self.obtener_todos()
        self.tabla.setRowCount(0)
        for i, d in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(d['Titulo']))
            self.tabla.setItem(i, 1, QTableWidgetItem(d['Clave RUNA']))
            self.tabla.setItem(i, 2, QTableWidgetItem(d['Categoria']))
            self.tabla.setItem(i, 3, QTableWidgetItem(d['Estado']))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(d['Adquisicion'])))

    def obtener_widget_vista(self):
        if self.widget_vista: return self.widget_vista
        self.widget_vista = QWidget()
        layout = QVBoxLayout(self.widget_vista)
        
        titulo = QLabel("Catálogo de Insumos")
        titulo.setProperty("isTitle", True) 
        layout.addWidget(titulo)
        
        self.entrada_busqueda = QLineEdit(placeholderText="Filtrar...")
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla) 
        layout.addWidget(self.entrada_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Título", "Clave RUNA", "Categoría", "Estado", "Adquisición"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)
        
        self.cargar_datos()
        return self.widget_vista

    def reiniciar_visibilidad_formulario(self):
        if self.widget_contenido_formulario:
            self.widget_contenido_formulario.hide() 
        self.establecer_crear(inicial=True) 

    def obtener_widget_formulario(self, ctrl_param):
        self.ctrl_param = ctrl_param
        if self.widget_formulario:
            return self.widget_formulario
        
        self.widget_formulario = QWidget()
        layout_principal = QVBoxLayout(self.widget_formulario)
        
        layout_principal.addWidget(QLabel("Acciones"))
        layout_modo = QHBoxLayout()
        self.btn_crear = QPushButton("Crear Nuevo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setChecked(True)
        self.btn_crear.clicked.connect(lambda: self.establecer_modo('crear'))
        
        self.btn_editar = QPushButton("Editar Existente")
        self.btn_editar.setCheckable(True)
        self.btn_editar.clicked.connect(lambda: self.establecer_modo('editar'))
        
        layout_modo.addWidget(self.btn_crear)
        layout_modo.addWidget(self.btn_editar)
        layout_principal.addLayout(layout_modo)
        
        self.widget_contenido_formulario = QWidget()
        layout_contenido = QVBoxLayout(self.widget_contenido_formulario)

        self.etiqueta_runa = QLabel("Clave RUNA (ID Único)")
        layout_contenido.addWidget(self.etiqueta_runa)
        self.entrada_runa = QLineEdit()
        self.entrada_runa.setPlaceholderText("Ingrese Clave RUNA para buscar")
        self.entrada_runa.textChanged.connect(self.intentar_cargar_edicion)
        layout_contenido.addWidget(self.entrada_runa)

        layout_contenido.addWidget(QLabel("Nombre"))
        self.entrada_nombre = QLineEdit()
        layout_contenido.addWidget(self.entrada_nombre)
        
        layout_contenido.addWidget(QLabel("Categoría"))
        self.combo_cat = QComboBox()
        self.cargar_combos()
        layout_contenido.addWidget(self.combo_cat)
        
        self.etiqueta_fecha = QLabel("Fecha Adquisición") 
        layout_contenido.addWidget(self.etiqueta_fecha)
        self.entrada_fecha = QDateEdit(calendarPopup=True)
        self.entrada_fecha.setDisplayFormat("yyyy-MM-dd")
        self.entrada_fecha.setDate(QDate.currentDate())
        layout_contenido.addWidget(self.entrada_fecha)
        
        self.etiqueta_estado = QLabel("Estado")
        layout_contenido.addWidget(self.etiqueta_estado)
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["DISPONIBLE", "PRESTADO", "MANTENIMIENTO", "SUSPENDIDA", "ELIMINADA"])
        layout_contenido.addWidget(self.combo_estado)
        
        layout_contenido.addStretch()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.clicked.connect(self.manejar_guardado)
        layout_contenido.addWidget(self.btn_guardar)
        
        layout_principal.addWidget(self.widget_contenido_formulario)
        layout_principal.addStretch() 
        
        self.widget_contenido_formulario.hide() 
        self.establecer_modo('crear', inicial=True)
        return self.widget_formulario

    def cargar_combos(self):
        if not self.ctrl_param: return
        self.combo_cat.clear()
        cats = self.ctrl_param.obtener_tipos_insumo() 
        for c in cats:
            self.combo_cat.addItem(c['nombre'], c['id']) 

    def establecer_modo(self, modo, inicial=False):
        self.modo = modo
        es_crear = (modo == 'crear')
        
        self.btn_crear.setChecked(es_crear)
        self.btn_editar.setChecked(not es_crear)
        
        if self.etiqueta_runa: self.etiqueta_runa.setText("Clave RUNA (Auto-Generada)" if es_crear else "Clave RUNA (ID Único)")
        if self.entrada_runa: 
            self.entrada_runa.setReadOnly(es_crear)
            if es_crear: self.entrada_runa.hide()
            else: self.entrada_runa.show()
            
        if self.entrada_nombre: self.entrada_nombre.setReadOnly(False)
        if self.combo_cat: self.combo_cat.setEnabled(True)
        
        if self.etiqueta_estado: self.etiqueta_estado.setVisible(not es_crear)
        if self.combo_estado: self.combo_estado.setVisible(not es_crear)
        if self.etiqueta_fecha: self.etiqueta_fecha.setVisible(not es_crear)
        if self.entrada_fecha: self.entrada_fecha.setVisible(not es_crear)

        self.limpiar_formulario()
        if not inicial and self.widget_contenido_formulario:
            self.widget_contenido_formulario.show()

    def establecer_crear(self, inicial=False):
        self.establecer_modo('crear', inicial) 

    def establecer_editar(self):
        self.establecer_modo('editar')

    def limpiar_formulario(self):
        if self.entrada_runa: self.entrada_runa.clear()
        self.entrada_nombre.clear()
        self.entrada_fecha.setDate(QDate.currentDate())
        if self.combo_cat.count() > 0:
            self.combo_cat.setCurrentIndex(0)
        if self.combo_estado:
            self.combo_estado.setCurrentText("DISPONIBLE")

    def filtrar_tabla(self, texto):
        texto = texto.lower()
        for i in range(self.tabla.rowCount()):
            coincidencia = False
            for j in range(self.tabla.columnCount()):
                item = self.tabla.item(i, j)
                if item and texto in item.text().lower():
                    coincidencia = True
                    break
            self.tabla.setRowHidden(i, not coincidencia)

    def intentar_cargar_edicion(self):
        if self.modo != 'editar': return
        clave_runa = self.entrada_runa.text().strip()
        if not clave_runa: return
        
        item = self.obtener_uno(clave_runa) 
        if item:
            self.entrada_nombre.setText(item.get('titulo', ''))
            id_tipo = item.get('id_tipo_insumo')
            indice = self.combo_cat.findData(id_tipo)
            if indice != -1: self.combo_cat.setCurrentIndex(indice)
            
            fecha_adquisicion = item.get('fecha_adquisicion')
            if isinstance(fecha_adquisicion, datetime):
                fecha_bd_str = fecha_adquisicion.strftime("%Y-%m-%d")
                fecha_bd = QDate.fromString(fecha_bd_str, "yyyy-MM-dd")
                self.entrada_fecha.setDate(fecha_bd)
            
            estado_ui = 'SUSPENDIDA' if item['estado'] == 'INACTIVA' else item['estado']
            self.combo_estado.setCurrentText(estado_ui)
            
            if self.es_libro(id_tipo):
                self.entrada_nombre.setReadOnly(True)
                self.combo_cat.setEnabled(False)
                self.entrada_fecha.setReadOnly(True)
                QMessageBox.information(None, "Libro Detectado", "Este insumo es un Libro. Solo puede editar su Estado.")
            else:
                self.entrada_nombre.setReadOnly(False)
                self.combo_cat.setEnabled(True)
                self.entrada_fecha.setReadOnly(False)

    def manejar_guardado(self):
        titulo = self.entrada_nombre.text().strip()
        id_tipo = self.combo_cat.currentData()
        
        if not titulo or id_tipo is None:
            QMessageBox.warning(None, "Error", "Título y Categoría requeridos")
            return
            
        if self.modo == 'crear':
            if self.es_libro(id_tipo):
                QMessageBox.warning(None, "Error", "No se pueden crear libros aquí. Use el módulo 'Libros'.")
                return

            fecha_adq = QDate.currentDate().toString("yyyy-MM-dd")
            try:
                clave_runa = self.generar_runa_unica()
                self.guardar_bd(titulo, id_tipo, fecha_adq, "DISPONIBLE", clave_runa, False)
                QMessageBox.information(None, "Éxito", f"Insumo creado: {clave_runa}")
                self.datos_actualizados.emit() 
            except Exception as e:
                QMessageBox.critical(None, "Error", str(e))
                
        else:
            clave_runa = self.entrada_runa.text().strip()
            if not clave_runa: return

            item = self.obtener_uno(clave_runa)
            if not item: return
            
            estado_frontend = self.combo_estado.currentText()
            
            es_libro = self.es_libro(item.get('id_tipo_insumo'))
            
            titulo_guardar = item.get('titulo') if es_libro else titulo
            id_tipo_guardar = item.get('id_tipo_insumo') if es_libro else id_tipo
            
            fecha_entrada = self.entrada_fecha.date().toString("yyyy-MM-dd")
            fecha_guardar = item.get('fecha_adquisicion') if es_libro else fecha_entrada

            try:
                if estado_frontend == 'ELIMINADA':
                    self.eliminar_fisico(clave_runa)
                    QMessageBox.information(None, "Info", "Eliminado físicamente.")
                else:
                    estado_bd = "INACTIVA" if estado_frontend == 'SUSPENDIDA' else estado_frontend
                    self.guardar_bd(titulo_guardar, id_tipo_guardar, fecha_guardar, estado_bd, clave_runa, True) 
                    QMessageBox.information(None, "Info", f"Actualizado.")
                
                self.datos_actualizados.emit()
            except Exception as e:
                QMessageBox.critical(None, "Error", str(e))
                
        self.cargar_datos()
        self.limpiar_formulario()