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
        self.widget_contenido_formulario = None # Sub-widget para ocultación
        self.tabla = None
        self.modo = 'crear'
        self.id_actual = None
        
        # Elementos de UI
        self.btn_modo_crear = None
        self.btn_modo_editar = None
        self.combo_rubro = None
        self.combo_filtro = None 
        self.entrada_nombre = None
        self.combo_estado = None 
    
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

    # --- MÉTODOS DE COMPATIBILIDAD ---
    def obtener_tipos_usuario(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_tipo_usuario as id, nombre FROM param_tipos_usuario WHERE estado='ACTIVO'")
        res = cursor.fetchall(); cursor.close()
        return res

    def obtener_tipos_insumo(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_tipo_insumo as id, nombre FROM param_tipos_insumo WHERE estado='ACTIVO'")
        res = cursor.fetchall(); cursor.close()
        return res

    def obtener_autores(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_autor as id, nombre_completo as nombre FROM param_autores WHERE estado='ACTIVO'")
        res = cursor.fetchall(); cursor.close()
        return res

    def obtener_editoriales(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_editorial as id, nombre_editorial as nombre FROM editoriales WHERE estado='ACTIVO'")
        res = cursor.fetchall(); cursor.close()
        return res

    def obtener_categorias_libro(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_categoria as id, nombre_categoria as nombre FROM categorias_catalogo WHERE estado='ACTIVO'")
        res = cursor.fetchall(); cursor.close()
        return res
        
    def obtener_generos(self):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT id_genero as id, nombre_genero as nombre FROM generos WHERE estado='ACTIVO'")
        res = cursor.fetchall(); cursor.close()
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
        res = cursor.fetchall(); cursor.close()
        return res

    def obtener_widget_vista(self):
        if self.widget_vista: return self.widget_vista
        self.widget_vista = QWidget()
        layout = QVBoxLayout(self.widget_vista)
        layout.addWidget(QLabel("<h2>Gestión de Parámetros</h2>")) 
        
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
        layout_principal = QVBoxLayout(self.widget_formulario)
        
        # Botones de Modo (Selector)
        layout_modo = QHBoxLayout()
        self.btn_modo_crear = QPushButton("Crear")
        self.btn_modo_crear.setCheckable(True)
        self.btn_modo_editar = QPushButton("Editar")
        self.btn_modo_editar.setCheckable(True)
        
        self.btn_modo_crear.clicked.connect(self.establecer_crear)
        self.btn_modo_editar.clicked.connect(self.establecer_editar)
        
        layout_modo.addWidget(self.btn_modo_crear)
        layout_modo.addWidget(self.btn_modo_editar)
        layout_principal.addLayout(layout_modo)

        # CONTENEDOR DE FORMULARIO (Empieza oculto)
        self.widget_contenido_formulario = QWidget()
        layout_cont = QVBoxLayout(self.widget_contenido_formulario)
        self.widget_contenido_formulario.hide()
        
        layout_cont.addWidget(QLabel("Rubro"))
        self.combo_rubro = QComboBox()
        self.combo_rubro.addItems(["Tipo Usuario", "Tipo Insumo", "Autor", "Editorial", "Categoría (Libro)", "Género"]) 
        self.combo_rubro.currentTextChanged.connect(self.limpiar_formulario)
        layout_cont.addWidget(self.combo_rubro)
        
        layout_cont.addWidget(QLabel("Nombre"))
        self.entrada_nombre = QLineEdit()
        self.entrada_nombre.editingFinished.connect(self.intentar_cargar_edicion)
        layout_cont.addWidget(self.entrada_nombre)
        
        self.etiqueta_estado = QLabel("Estado")
        layout_cont.addWidget(self.etiqueta_estado)
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["ACTIVO", "INACTIVO", "ELIMINADA"]) 
        layout_cont.addWidget(self.combo_estado)
        
        layout_cont.addStretch()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.clicked.connect(self.manejar_guardado)
        layout_cont.addWidget(self.btn_guardar)

        layout_principal.addWidget(self.widget_contenido_formulario)
        layout_principal.addStretch()
        
        return self.widget_formulario

    def limpiar_formulario(self):
        if self.entrada_nombre: self.entrada_nombre.clear()
        self.id_actual = None
        if self.combo_estado: self.combo_estado.setCurrentIndex(0)

    def establecer_crear(self):
        self.modo = 'crear'
        self.btn_modo_crear.setChecked(True)
        self.btn_modo_editar.setChecked(False)
        self.etiqueta_estado.hide()
        self.combo_estado.hide()
        self.widget_contenido_formulario.show() # Despliegue por toque
        self.limpiar_formulario()

    def establecer_editar(self):
        self.modo = 'editar'
        self.btn_modo_crear.setChecked(False)
        self.btn_modo_editar.setChecked(True)
        self.etiqueta_estado.show()
        self.combo_estado.show()
        self.widget_contenido_formulario.show() # Despliegue por toque
        self.limpiar_formulario()

    def cargar_datos(self):
        datos = self.obtener_todos_params()
        if not self.tabla: return
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
            self.tabla.setRowHidden(i, filtro_rubro != "Todos" and rubro_fila != filtro_rubro)

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
        else:
            self.id_actual = None

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
                    QMessageBox.warning(None, "Error", "Nombre no encontrado.")
                    return
                if estado_frontal == 'ELIMINADA':
                    self.eliminar_por_id(rubro, self.id_actual)
                else: 
                    estado_bd = 'INACTIVO' if estado_frontal == 'INACTIVO' else 'ACTIVO'
                    self.guardar_param_generico(rubro, nombre, estado_bd, True, self.id_actual)
            self.cargar_datos()
            self.parametro_guardado.emit()
            # Al guardar, solemos ocultar o limpiar
            self.widget_contenido_formulario.hide()
            self.btn_modo_crear.setChecked(False)
            self.btn_modo_editar.setChecked(False)
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    def guardar_param_generico(self, rubro, nombre, estado, es_actualizacion, id_param=None):
        tabla, col_id, col_nombre = self._obtener_mapa_param(rubro)
        cursor = self.bd.cursor()
        if es_actualizacion:
            consulta = f"UPDATE {tabla} SET {col_nombre}=%s, estado=%s WHERE {col_id}=%s"
            cursor.execute(consulta, (nombre, estado, id_param))
        else:
            if rubro == 'Editorial':
                consulta = f"INSERT INTO {tabla} ({col_nombre}, pais, estado) VALUES (%s, %s, %s)"
                cursor.execute(consulta, (nombre, 'NO ESPECIFICADO', 'ACTIVO'))
            else:
                consulta = f"INSERT INTO {tabla} ({col_nombre}, estado) VALUES (%s, %s)"
                cursor.execute(consulta, (nombre, 'ACTIVO'))
        self.bd.commit(); cursor.close()

    def eliminar_por_id(self, rubro, id_param):
        tabla, col_id, _ = self._obtener_mapa_param(rubro)
        cursor = self.bd.cursor()
        cursor.execute(f"DELETE FROM {tabla} WHERE {col_id} = %s", (id_param,))
        self.bd.commit(); cursor.close()