from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QStackedWidget
)
from Modulos.Config import Conexion
from PySide6.QtCore import QObject, Signal

class ControladorParametro(QObject):
    parametro_guardado = Signal()
    def __init__(self):
        super().__init__()
        self.bd = Conexion().obtener_conexion()
        self.widget_vista = None
        self.widget_formulario = None
        self.tabla = None
        self.modo = 'crear'
        self.id_actual = None
        self.combo_rubro = None
        self.combo_filtro = None 
        self.entrada_nombre = None
        self.combo_estado = None 
        self.pila = None
    
    def _obtener_mapa_param(self, rubro):
        MAPA = {
            "Tipo Usuario": ("param_tipos_usuario", "id_tipo_usuario", "nombre"),
            "Tipo Insumo": ("param_tipos_insumo", "id_tipo_insumo", "nombre"),
            "Autor": ("param_autores", "id_autor", "nombre_completo"),
            "Editorial": ("editoriales", "id_editorial", "nombre_editorial"),
            "Categoría (Libro)": ("categorias_catalogo", "id_categoria", "nombre_categoria"),
            "Género": ("generos", "id_genero", "nombre_genero")
        }
        return MAPA.get(rubro, (None, None, None))
    
    def _obtener_info_param_por_nombre(self, rubro, nombre):
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        if not tabla: return None
        
        cursor = self.bd.cursor(dictionary=True)
        consulta = f"SELECT {col_id} AS id, estado FROM {tabla} WHERE {col_nombre} = %s"
        cursor.execute(consulta, (nombre,))
        res = cursor.fetchone()
        cursor.close()
        return res 
    
    def obtener_tipos_usuario(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_tipo_usuario as id, nombre FROM param_tipos_usuario WHERE estado='ACTIVO'")
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_tipos_insumo(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_tipo_insumo as id, nombre FROM param_tipos_insumo WHERE estado='ACTIVO'")
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_autores(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_autor as id, nombre_completo as nombre FROM param_autores WHERE estado='ACTIVO'")
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_editoriales(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_editorial as id, nombre_editorial as nombre FROM editoriales WHERE estado='ACTIVO'")
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_categorias_libro(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_categoria as id, nombre_categoria as nombre FROM categorias_catalogo WHERE estado='ACTIVO'")
        res = cursor.fetchall()
        cursor.close()
        return res
        
    def obtener_generos(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_genero as id, nombre_genero as nombre FROM generos WHERE estado='ACTIVO'")
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_todos_params(self):
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
            SELECT nombre AS Nombre, 'Tipo Usuario' AS Rubro, estado AS Estado FROM param_tipos_usuario
            UNION ALL
            SELECT nombre, 'Tipo Insumo', estado FROM param_tipos_insumo
            UNION ALL
            SELECT nombre_completo, 'Autor', estado FROM param_autores
            UNION ALL
            SELECT nombre_editorial, 'Editorial', estado FROM editoriales
            UNION ALL
            SELECT nombre_categoria, 'Categoría (Libro)', estado FROM categorias_catalogo
            UNION ALL
            SELECT nombre_genero, 'Género', estado FROM generos
        """
        cursor.execute(consulta)
        res = cursor.fetchall()
        cursor.close()
        return res

    def guardar_param_generico(self, rubro, nombre, estado, es_actualizacion, id_param=None):
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        if not tabla:
            raise ValueError(f"Rubro '{rubro}' no válido.")
            
        cursor = self.bd.cursor()
        try:
            if es_actualizacion and id_param is not None:
                consulta = f"UPDATE {tabla} SET {col_nombre}=%s, estado=%s WHERE {col_id}=%s"
                params = (nombre, estado, id_param)
                cursor.execute(consulta, params)
            else:
                consulta_verif = f"SELECT {col_id} FROM {tabla} WHERE {col_nombre} = %s"
                cursor.execute(consulta_verif, (nombre,))
                if cursor.fetchone():
                    raise Exception(f"El nombre '{nombre}' ya existe en el rubro '{rubro}'.")
                
                if rubro == 'Editorial':
                    consulta = f"INSERT INTO {tabla} ({col_nombre}, pais, estado) VALUES (%s, %s, %s)"
                    params = (nombre, 'NO ESPECIFICADO', 'ACTIVO')
                else:
                    consulta = f"INSERT INTO {tabla} ({col_nombre}, estado) VALUES (%s, %s)"
                    params = (nombre, 'ACTIVO')
                
                cursor.execute(consulta, params)
                
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_por_id(self, rubro, id_param):
        tabla, col_id, _ = self._obtener_mapa_param(rubro)
        if not tabla:
            raise ValueError(f"Rubro '{rubro}' no válido para eliminación.")
            
        cursor = self.bd.cursor()
        try:
            consulta = f"DELETE FROM {tabla} WHERE {col_id} = %s"
            cursor.execute(consulta, (id_param,))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def obtener_widget_vista(self):
        if self.widget_vista: return self.widget_vista
        self.widget_vista = QWidget()
        layout = QVBoxLayout(self.widget_vista)
        layout.addWidget(QLabel("Parámetros")) 
        
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Todos", "Tipo Usuario", "Tipo Insumo", "Autor", "Editorial", "Categoría (Libro)", "Género"])
        self.combo_filtro.currentTextChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.combo_filtro)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Rubro", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)
        
        self.cargar_datos()
        return self.widget_vista

    def obtener_widget_formulario(self):
        if self.widget_formulario: return self.widget_formulario
        self.widget_formulario = QWidget()
        layout = QVBoxLayout(self.widget_formulario)
        
        layout_modo = QHBoxLayout()
        self.btn_crear = QPushButton("Crear")
        self.btn_crear.setCheckable(True); self.btn_crear.setChecked(True)
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setCheckable(True)
        self.btn_crear.clicked.connect(self.establecer_crear)
        self.btn_editar.clicked.connect(self.establecer_editar)
        layout_modo.addWidget(self.btn_crear); layout_modo.addWidget(self.btn_editar)
        layout.addLayout(layout_modo)
        
        layout.addWidget(QLabel("Rubro"))
        self.combo_rubro = QComboBox()
        self.combo_rubro.addItems(["Tipo Usuario", "Tipo Insumo", "Autor", "Editorial", "Categoría (Libro)", "Género"]) 
        self.combo_rubro.currentTextChanged.connect(self.limpiar_formulario)
        layout.addWidget(self.combo_rubro)
        
        layout.addWidget(QLabel("Nombre"))
        self.entrada_nombre = QLineEdit()
        self.entrada_nombre.editingFinished.connect(self.intentar_cargar_edicion)
        layout.addWidget(self.entrada_nombre)
        
        layout.addWidget(QLabel("Estado"))
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["ACTIVO", "INACTIVO", "ELIMINADA"]) 
        self.combo_estado.hide()
        layout.addWidget(self.combo_estado)
        
        layout.addStretch()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.clicked.connect(self.manejar_guardado)
        layout.addWidget(self.btn_guardar)
        
        return self.widget_formulario

    def limpiar_formulario(self):
        self.entrada_nombre.clear()
        self.id_actual = None
        self.combo_estado.setCurrentIndex(0)

    def establecer_crear(self):
        self.modo = 'crear'
        self.btn_crear.setChecked(True); self.btn_editar.setChecked(False)
        self.combo_estado.hide()
        self.limpiar_formulario()

    def establecer_editar(self):
        self.modo = 'editar'
        self.btn_crear.setChecked(False); self.btn_editar.setChecked(True)
        self.combo_estado.show()
        self.limpiar_formulario()

    def cargar_datos(self):
        datos = self.obtener_todos_params()
        self.tabla.setRowCount(0)
        for i, d in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(d['Nombre']))
            self.tabla.setItem(i, 1, QTableWidgetItem(d['Rubro']))
            self.tabla.setItem(i, 2, QTableWidgetItem(d['Estado']))

    def filtrar_tabla(self):
        filtro_rubro = self.combo_filtro.currentText()
        
        for i in range(self.tabla.rowCount()):
            rubro_fila = self.tabla.item(i, 1).text()
            
            if filtro_rubro != "Todos" and rubro_fila != filtro_rubro:
                self.tabla.setRowHidden(i, True)
                continue
            
            self.tabla.setRowHidden(i, False)

    def intentar_cargar_edicion(self):
        if self.modo != 'editar': return
        
        rubro = self.combo_rubro.currentText()
        nombre = self.entrada_nombre.text().strip()
        
        if not nombre: return
        
        info_param = self._obtener_info_param_por_nombre(rubro, nombre)
        
        if info_param:
            self.id_actual = info_param['id']
            estado_frontal = 'ACTIVO' if info_param['estado'] == 'ACTIVO' else 'INACTIVO'
            self.combo_estado.setCurrentText(estado_frontal)
            QMessageBox.information(None, "Éxito", f"Parámetro '{nombre}' cargado para edición. ID interno: {self.id_actual}")
        else:
            self.id_actual = None
            self.combo_estado.setCurrentIndex(0)
            QMessageBox.warning(None, "Aviso", f"Parámetro '{nombre}' no encontrado para el rubro '{rubro}'.")

    def manejar_guardado(self):
        rubro = self.combo_rubro.currentText()
        nombre = self.entrada_nombre.text().strip()
        
        if not nombre:
            QMessageBox.warning(None, "Error", "El campo Nombre es requerido.")
            return

        estado_frontal = self.combo_estado.currentText()
        
        try:
            if self.modo == 'crear':
                self.guardar_param_generico(rubro, nombre, 'ACTIVO', False)
                QMessageBox.information(None, "Éxito", f"'{rubro}' '{nombre}' creado.")
            else: 
                if self.id_actual is None:
                    QMessageBox.warning(None, "Error", "Debe ingresar y cargar un Nombre existente para editar.")
                    return
                
                id_param = self.id_actual
                
                if estado_frontal == 'ELIMINADA':
                    self.eliminar_por_id(rubro, id_param)
                    QMessageBox.information(None, "Info", f"'{rubro}' '{nombre}' eliminado físicamente.")
                else: 
                    estado_bd = 'INACTIVO' if estado_frontal == 'INACTIVO' else 'ACTIVO'
                    self.guardar_param_generico(rubro, nombre, estado_bd, True, id_param)
                    QMessageBox.information(None, "Info", f"'{rubro}' '{nombre}' actualizado/modificado a {estado_bd}.")
                    
            self.cargar_datos()
            self.filtrar_tabla()
            self.limpiar_formulario()
            
            self.parametro_guardado.emit()
            
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))