from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSpinBox
)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Signal, QObject 
from Modulos.Config import Conexion
import random
import string
import time 

class ControladorLibro(QObject): 
    libro_guardado = Signal() 
    
    def __init__(self):
        super().__init__() 
        self.bd = Conexion().obtener_conexion()
        self.ctrl_param = None
        self.widget_vista = None
        self.widget_formulario = None
        self.tabla = None
        self.modo = 'crear'
        
        self.widget_contenido_formulario = None 
        self.etiqueta_isbn = None
        self.entrada_isbn = None
        self.etiqueta_titulo = None
        self.entrada_titulo = None
        self.etiqueta_stock = None
        self.entrada_stock = None
        self.etiqueta_estado = None
        self.combo_estado = None
        self.combo_autor = None
        self.combo_editorial = None
        self.combo_categoria = None
        self.combo_genero = None
        self.datos_libro_actual = None 

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
        runa_reserva = str(int(time.time() * 1000000))[-longitud:]
        if not self.verificar_existencia_runa(runa_reserva): return runa_reserva
        raise Exception("Error generando RUNA.")

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
        
        def obtener_primer_id(clave):
             cadena_ids = resultado.get(clave)
             if cadena_ids:
                 try: return int(str(cadena_ids).split(',')[0])
                 except: return None
             return None
        
        if resultado:
             resultado['primer_id_autor'] = obtener_primer_id('autores')
             resultado['primer_id_editorial'] = obtener_primer_id('editoriales')
             resultado['primer_id_categoria'] = obtener_primer_id('categorias')
             resultado['primer_id_genero'] = obtener_primer_id('generos')
        return resultado

    def guardar_bd(self, titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, estado, es_actualizacion):
        cursor = self.bd.cursor()
        try:
            if es_actualizacion:
                cursor.execute("SELECT id_libro, titulo FROM libros WHERE isbn = %s", (isbn,))
                fila = cursor.fetchone()
                if not fila: raise Exception("Libro no encontrado.")
                id_libro = fila[0]
                titulo_anterior = fila[1]
                
                cursor.execute("UPDATE libros SET titulo=%s, estado=%s WHERE id_libro=%s", (titulo, estado, id_libro)) 
                if titulo_anterior != titulo:
                     cursor.execute("UPDATE insumos SET titulo=%s WHERE titulo=%s AND id_tipo_insumo=3", (titulo, titulo_anterior))
            else:
                cursor.execute("SELECT id_libro FROM libros WHERE isbn=%s", (isbn,))
                if cursor.fetchone(): raise Exception("El ISBN ya existe.")
                cursor.execute("INSERT INTO libros (titulo, isbn, estado) VALUES (%s, %s, 'ACTIVO')", (titulo, isbn))
                id_libro = cursor.lastrowid

            cursor.execute("DELETE FROM libro_autor WHERE id_libro=%s", (id_libro,))
            if id_autor: cursor.execute("INSERT INTO libro_autor (id_libro, id_autor) VALUES (%s, %s)", (id_libro, id_autor))
            cursor.execute("DELETE FROM libro_editorial WHERE id_libro=%s", (id_libro,))
            if id_editorial: cursor.execute("INSERT INTO libro_editorial (id_libro, id_editorial) VALUES (%s, %s)", (id_libro, id_editorial))
            cursor.execute("DELETE FROM libro_categoria WHERE id_libro=%s", (id_libro,))
            if id_categoria: cursor.execute("INSERT INTO libro_categoria (id_libro, id_categoria) VALUES (%s, %s)", (id_libro, id_categoria))
            cursor.execute("DELETE FROM libro_genero WHERE id_libro=%s", (id_libro,))
            if id_genero: cursor.execute("INSERT INTO libro_genero (id_libro, id_genero) VALUES (%s, %s)", (id_libro, id_genero))
            
            cursor.execute("SELECT COUNT(*) FROM insumos WHERE titulo=%s AND id_tipo_insumo=3", (titulo,))
            stock_actual = cursor.fetchone()[0]
            diferencia = stock - stock_actual
            
            if diferencia > 0:
                for _ in range(diferencia):
                    clave_runa = self.generar_runa_unica()
                    cursor.execute("INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa) VALUES (%s, 3, 'DISPONIBLE', CURDATE(), %s)", (titulo, clave_runa))
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
            if not fila:
                raise Exception("Libro no encontrado para eliminación.")
            id_libro = fila[0]
            titulo = fila[1]
            
            cursor.execute("DELETE FROM libro_autor WHERE id_libro=%s", (id_libro,))
            cursor.execute("DELETE FROM libro_editorial WHERE id_libro=%s", (id_libro,))
            cursor.execute("DELETE FROM libro_categoria WHERE id_libro=%s", (id_libro,))
            cursor.execute("DELETE FROM libro_genero WHERE id_libro=%s", (id_libro,))
            
            cursor.execute("DELETE FROM insumos WHERE titulo = %s AND id_tipo_insumo = 3", (titulo,))
            
            cursor.execute("DELETE FROM libros WHERE id_libro = %s", (id_libro,))
            
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
        
        titulo = QLabel("Catálogo de Libros")
        titulo.setProperty("isTitle", True) 
        layout.addWidget(titulo) 
        
        self.entrada_busqueda = QLineEdit(placeholderText="Filtrar...")
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.entrada_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Título", "ISBN", "Autor", "Stock", "Disponible"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)
        self.cargar_datos()
        return self.widget_vista
    
    def reiniciar_visibilidad_formulario(self):
        if self.widget_contenido_formulario:
            self.widget_contenido_formulario.hide() 
        self.establecer_modo('crear', inicial=True) 

    def obtener_widget_formulario(self, ctrl_param):
        self.ctrl_param = ctrl_param
        self.ctrl_param.parametro_guardado.connect(self.cargar_combos)
        
        if self.widget_formulario: return self.widget_formulario
        self.widget_formulario = QWidget()
        layout_principal = QVBoxLayout(self.widget_formulario)
        
        layout_principal.addWidget(QLabel("Acciones"))
        layout_modo = QHBoxLayout()
        self.btn_crear = QPushButton("Crear Nuevo")
        self.btn_crear.setCheckable(True); self.btn_crear.setChecked(True)
        self.btn_editar = QPushButton("Editar Existente")
        self.btn_editar.setCheckable(True)
        self.btn_crear.clicked.connect(lambda: self.establecer_modo('crear'))
        self.btn_editar.clicked.connect(lambda: self.establecer_modo('editar'))
        layout_modo.addWidget(self.btn_crear); layout_modo.addWidget(self.btn_editar)
        layout_principal.addLayout(layout_modo)

        self.widget_contenido_formulario = QWidget()
        layout_contenido = QVBoxLayout(self.widget_contenido_formulario)
        
        layout_contenido.addWidget(QLabel("ISBN (Identificador)"))
        self.entrada_isbn = QLineEdit()
        self.entrada_isbn.editingFinished.connect(self.intentar_cargar_edicion)
        layout_contenido.addWidget(self.entrada_isbn)
        
        layout_contenido.addWidget(QLabel("Título"))
        self.entrada_titulo = QLineEdit()
        layout_contenido.addWidget(self.entrada_titulo)
        
        layout_contenido.addWidget(QLabel("Autor Principal"))
        self.combo_autor = QComboBox()
        layout_contenido.addWidget(self.combo_autor)
        
        layout_contenido.addWidget(QLabel("Editorial"))
        self.combo_editorial = QComboBox()
        layout_contenido.addWidget(self.combo_editorial)
        
        layout_contenido.addWidget(QLabel("Categoría"))
        self.combo_categoria = QComboBox()
        layout_contenido.addWidget(self.combo_categoria)
        
        layout_contenido.addWidget(QLabel("Género"))
        self.combo_genero = QComboBox()
        layout_contenido.addWidget(self.combo_genero)
        
        self.cargar_combos() 
        
        layout_contenido.addWidget(QLabel("Stock"))
        self.entrada_stock = QLineEdit()
        self.entrada_stock.setValidator(QIntValidator())
        layout_contenido.addWidget(self.entrada_stock)
        
        self.etiqueta_estado = QLabel("Estado del Libro")
        layout_contenido.addWidget(self.etiqueta_estado)
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["ACTIVA", "INACTIVA", "ELIMINADA"])
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
        
        self.combo_autor.clear(); self.combo_autor.addItem("Seleccione Autor", None)
        for a in self.ctrl_param.obtener_autores(): self.combo_autor.addItem(a['nombre'], a['id'])
        self.combo_editorial.clear(); self.combo_editorial.addItem("Seleccione Editorial", None)
        for e in self.ctrl_param.obtener_editoriales(): self.combo_editorial.addItem(e['nombre'], e['id'])
        self.combo_categoria.clear(); self.combo_categoria.addItem("Seleccione Categoría", None)
        for c in self.ctrl_param.obtener_categorias_libro(): self.combo_categoria.addItem(c['nombre'], c['id'])
        self.combo_genero.clear(); self.combo_genero.addItem("Seleccione Género", None)
        for g in self.ctrl_param.obtener_generos(): self.combo_genero.addItem(g['nombre'], g['id'])

    def establecer_modo(self, modo, inicial=False):
        self.modo = modo
        if modo == 'crear':
            self.btn_crear.setChecked(True)
            self.btn_editar.setChecked(False)
            self.entrada_isbn.setReadOnly(False)
            self.entrada_titulo.setReadOnly(False)
            self.combo_autor.setEnabled(True)
            self.combo_editorial.setEnabled(True)
            self.combo_categoria.setEnabled(True)
            self.combo_genero.setEnabled(True)
            self.entrada_stock.setReadOnly(False)
            self.etiqueta_estado.hide()
            self.combo_estado.hide()
            self.limpiar_formulario()
        else:
            self.btn_crear.setChecked(False)
            self.btn_editar.setChecked(True)
            self.entrada_isbn.setReadOnly(False)
            self.entrada_titulo.setReadOnly(False)
            self.combo_autor.setEnabled(True)
            self.combo_editorial.setEnabled(True)
            self.combo_categoria.setEnabled(True)
            self.combo_genero.setEnabled(True)
            self.entrada_stock.setReadOnly(False)
            self.etiqueta_estado.show()
            self.combo_estado.show()
            self.limpiar_formulario()
            
        if not inicial and self.widget_contenido_formulario:
            self.widget_contenido_formulario.show()

    def limpiar_formulario(self):
        self.entrada_titulo.clear()
        self.entrada_isbn.clear()
        self.entrada_stock.clear()
        if self.combo_autor: self.combo_autor.setCurrentIndex(0)
        if self.combo_editorial: self.combo_editorial.setCurrentIndex(0)
        if self.combo_categoria: self.combo_categoria.setCurrentIndex(0)
        if self.combo_genero: self.combo_genero.setCurrentIndex(0)
        if self.combo_estado: self.combo_estado.setCurrentText('ACTIVA')
        self.datos_libro_actual = None

    def cargar_datos(self):
        datos = self.obtener_todos()
        self.tabla.setRowCount(0)
        for i, d in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(d['titulo'])) 
            self.tabla.setItem(i, 1, QTableWidgetItem(str(d['isbn'])))
            self.tabla.setItem(i, 2, QTableWidgetItem(d['Autor']))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(d['Stock'])))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(d['Cantidad_Disponible'])))

    def filtrar_tabla(self, texto):
        texto = texto.lower()
        for i in range(self.tabla.rowCount()):
            coincidencia = False
            for j in range(self.tabla.columnCount()):
                item = self.tabla.item(i, j)
                if j in [0, 1] and item and texto in item.text().lower():
                    coincidencia = True
                    break
            self.tabla.setRowHidden(i, not coincidencia)

    def intentar_cargar_edicion(self):
        if self.modo != 'editar': return
        isbn = self.entrada_isbn.text().strip()
        if not isbn: 
            self.limpiar_formulario()
            return
            
        libro = self.obtener_por_isbn(isbn)
        if libro:
            self.datos_libro_actual = libro 
            QMessageBox.information(None, "Éxito", "Libro cargado.")
            
            self.entrada_titulo.setText(libro['titulo'])
            estado_bd = libro.get('estado')
            self.combo_estado.setCurrentText(estado_bd if estado_bd != 'INACTIVO' else 'INACTIVA')
            self.entrada_stock.setText(str(libro.get('stock_total') or 0))
            
            if libro.get('primer_id_autor'):
                 indice = self.combo_autor.findData(libro['primer_id_autor'])
                 if indice != -1: self.combo_autor.setCurrentIndex(indice)
            if libro.get('primer_id_editorial'):
                 indice = self.combo_editorial.findData(libro['primer_id_editorial'])
                 if indice != -1: self.combo_editorial.setCurrentIndex(indice)
            if libro.get('primer_id_categoria'):
                 indice = self.combo_categoria.findData(libro['primer_id_categoria'])
                 if indice != -1: self.combo_categoria.setCurrentIndex(indice)
            if libro.get('primer_id_genero'):
                 indice = self.combo_genero.findData(libro['primer_id_genero'])
                 if indice != -1: self.combo_genero.setCurrentIndex(indice)
                 
            self.entrada_isbn.setReadOnly(True) 
        else:
            self.datos_libro_actual = None

    def manejar_guardado(self):
        isbn = self.entrada_isbn.text().strip()
        titulo = self.entrada_titulo.text().strip()
        try:
            stock = int(self.entrada_stock.text() or 0)
            if stock < 0: return
        except: return

        id_autor = self.combo_autor.currentData()
        id_editorial = self.combo_editorial.currentData()
        id_categoria = self.combo_categoria.currentData()
        id_genero = self.combo_genero.currentData()

        if not isbn or not titulo or not id_autor:
            QMessageBox.warning(None, "Error", "Faltan datos obligatorios.")
            return

        existe = self.obtener_por_isbn(isbn)
        
        try:
            if self.modo == 'crear':
                if existe:
                    QMessageBox.warning(None, "Error", "ISBN duplicado")
                    return
                self.guardar_bd(titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, 'ACTIVO', False)
                QMessageBox.information(None, "Éxito", "Libro creado.")
            else: 
                if not existe:
                    QMessageBox.warning(None, "Error", "Libro no encontrado.")
                    return
                
                estado_frontend = self.combo_estado.currentText()
                if estado_frontend == 'ELIMINADA':
                    self.eliminar_todo(isbn) 
                    QMessageBox.information(None, "Info", "Libro y todas sus unidades asociadas eliminadas.")
                else:
                    estado_bd = 'INACTIVO' if estado_frontend == 'INACTIVA' else 'ACTIVO'
                    self.guardar_bd(titulo, isbn, id_autor, id_editorial, id_categoria, id_genero, stock, estado_bd, True)
                    QMessageBox.information(None, "Info", "Actualizado.")
            
            self.cargar_datos()
            self.limpiar_formulario()
            self.libro_guardado.emit()
            
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))