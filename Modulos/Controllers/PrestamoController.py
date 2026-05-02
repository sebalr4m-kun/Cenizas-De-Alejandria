from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate, Signal, QObject
from Modulos.Config import Conexion


class ControladorPrestamo(QObject): 
    datos_actualizados = Signal()   # ← Agregado para que MainWindow pueda llamarlo

    def __init__(self):
        super().__init__()
        self.bd = Conexion().obtener_conexion()
        self.widget_vista = None
        self.widget_formulario = None
        self.tabla = None
        self.modo = 'crear'

    # ==================== BASE DE DATOS ====================

    def obtener_todos(self):
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
            SELECT u.email AS Usuario, i.titulo AS Item, 
                   DATE_FORMAT(p.fecha_prestamo, '%Y-%m-%d') AS 'Fecha Inicio', 
                   p.estado_prestamo AS Estado
            FROM prestamos p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            JOIN insumos i ON p.id_insumo = i.id_insumo
            WHERE p.estado_prestamo != 'ELIMINADA'
            ORDER BY p.fecha_prestamo DESC
        """
        cursor.execute(consulta)
        res = cursor.fetchall()
        cursor.close()
        return res

    def obtener_uno(self, email, item, fecha):
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
            SELECT p.*, u.email, i.titulo, 
                   DATE_FORMAT(p.fecha_devolucion_esperada, '%Y-%m-%d') AS fecha_devolucion_esperada
            FROM prestamos p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            JOIN insumos i ON p.id_insumo = i.id_insumo
            WHERE u.email=%s AND i.titulo=%s AND p.fecha_prestamo=%s
        """
        cursor.execute(consulta, (email, item, fecha))
        res = cursor.fetchone()
        cursor.close()
        return res

    def guardar_bd(self, email, item, fecha, fecha_fin, estado, es_actualizacion):
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE email=%s", (email,))
            fila_uid = cursor.fetchone()
            
            cursor.execute("SELECT id_insumo FROM insumos WHERE titulo=%s AND estado!='ELIMINADA' LIMIT 1", (item,))
            fila_iid = cursor.fetchone()
            
            if not fila_uid or not fila_iid: 
                raise Exception("Usuario o Item no encontrado.")
            
            uid = fila_uid[0]
            iid = fila_iid[0]
            
            if es_actualizacion:
                consulta = """
                    UPDATE prestamos SET estado_prestamo=%s, fecha_devolucion_esperada=%s
                    WHERE id_usuario=%s AND id_insumo=%s AND fecha_prestamo=%s
                """
                cursor.execute(consulta, (estado, fecha_fin, uid, iid, fecha))
            else:
                consulta = """
                    INSERT INTO prestamos (id_usuario, id_insumo, fecha_prestamo, fecha_devolucion_esperada, estado_prestamo)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(consulta, (uid, iid, fecha, fecha_fin, estado))
            self.bd.commit()
        finally:
            cursor.close()

    def eliminar_fisico(self, email, item, fecha):
        cursor = self.bd.cursor()
        try:
            consulta = """
                DELETE p FROM prestamos p
                JOIN usuarios u ON p.id_usuario = u.id_usuario
                JOIN insumos i ON p.id_insumo = i.id_insumo
                WHERE u.email=%s AND i.titulo=%s AND p.fecha_prestamo=%s
            """
            cursor.execute(consulta, (email, item, fecha))
            self.bd.commit()
        finally:
            cursor.close()

    # ==================== WIDGETS Y VISTA ====================

    def obtener_widget_vista(self):
        if self.widget_vista:
            return self.widget_vista

        self.widget_vista = QWidget()
        layout = QVBoxLayout(self.widget_vista)
        layout.addWidget(QLabel("Gestión de Préstamos")) 
        
        self.entrada_busqueda = QLineEdit(placeholderText="Filtrar...")
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.entrada_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Usuario", "Item", "Fecha Inicio", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)
        
        self.cargar_datos()
        return self.widget_vista

    def obtener_widget_formulario(self, ctrl_param): 
        if self.widget_formulario:
            return self.widget_formulario

        self.widget_formulario = QWidget()
        layout = QVBoxLayout(self.widget_formulario)
        
        layout_modo = QHBoxLayout()
        self.btn_crear = QPushButton("Crear Nuevo")
        self.btn_crear.setCheckable(True)
        self.btn_crear.setChecked(True)
        self.btn_editar = QPushButton("Editar Existente")
        self.btn_editar.setCheckable(True)
        self.btn_crear.clicked.connect(self.establecer_crear)
        self.btn_editar.clicked.connect(self.establecer_editar)
        layout_modo.addWidget(self.btn_crear)
        layout_modo.addWidget(self.btn_editar)
        layout.addLayout(layout_modo)
        
        layout.addWidget(QLabel("Email Usuario"))
        self.entrada_email = QLineEdit()
        layout.addWidget(self.entrada_email)
        
        layout.addWidget(QLabel("Nombre Item"))
        self.entrada_item = QLineEdit()
        layout.addWidget(self.entrada_item)
        
        layout.addWidget(QLabel("Fecha Inicio"))
        self.entrada_fecha = QDateEdit(calendarPopup=True)
        self.entrada_fecha.setDate(QDate.currentDate())
        self.entrada_fecha.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.entrada_fecha)
        
        self.entrada_email.editingFinished.connect(self.intentar_cargar_edicion)
        self.entrada_item.editingFinished.connect(self.intentar_cargar_edicion)
        self.entrada_fecha.dateChanged.connect(self.intentar_cargar_edicion) 
        
        layout.addWidget(QLabel("Fecha Devolución Esperada"))
        self.entrada_fecha_fin = QDateEdit(calendarPopup=True)
        self.entrada_fecha_fin.setDate(QDate.currentDate().addDays(7))
        self.entrada_fecha_fin.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.entrada_fecha_fin)
        
        layout.addWidget(QLabel("Estado"))
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["ACTIVO", "DEVUELTO", "VENCIDO", "SUSPENDIDA", "ELIMINADA"])
        self.combo_estado.hide()
        layout.addWidget(self.combo_estado)
        
        layout.addStretch()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.clicked.connect(self.manejar_guardado)
        layout.addWidget(self.btn_guardar)
        
        return self.widget_formulario

    def establecer_crear(self):
        self.modo = 'crear'
        self.btn_crear.setChecked(True)
        self.btn_editar.setChecked(False)
        self.combo_estado.hide()
        self.limpiar_formulario()

    def establecer_editar(self):
        self.modo = 'editar'
        self.btn_crear.setChecked(False)
        self.btn_editar.setChecked(True)
        self.combo_estado.show()
        self.limpiar_formulario()

    def limpiar_formulario(self):
        self.entrada_email.clear()
        self.entrada_item.clear()
        self.entrada_fecha.setDate(QDate.currentDate())
        self.entrada_fecha_fin.setDate(QDate.currentDate().addDays(7)) 
        self.combo_estado.setCurrentIndex(0) 

    def cargar_datos(self):
        datos = self.obtener_todos()
        if self.tabla is None:
            return
        self.tabla.setRowCount(0)
        for i, d in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(d['Usuario']))
            self.tabla.setItem(i, 1, QTableWidgetItem(d['Item']))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(d['Fecha Inicio'])))
            self.tabla.setItem(i, 3, QTableWidgetItem(d['Estado']))

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
        if self.modo != 'editar': 
            return
        
        email = self.entrada_email.text().strip()
        item = self.entrada_item.text().strip()
        fecha = self.entrada_fecha.date().toString("yyyy-MM-dd")
        
        if not email or not item: 
            return
        
        prestamo = self.obtener_uno(email, item, fecha)
        
        if prestamo:
            self.combo_estado.setCurrentText(prestamo.get('estado_prestamo', 'ACTIVO'))
            fecha_fin_str = prestamo.get('fecha_devolucion_esperada')
            if fecha_fin_str:
                self.entrada_fecha_fin.setDate(QDate.fromString(str(fecha_fin_str), "yyyy-MM-dd"))
            QMessageBox.information(None, "Carga Exitosa", "Préstamo encontrado y datos cargados.")
        else:
            self.entrada_fecha_fin.setDate(QDate.currentDate().addDays(7))
            self.combo_estado.setCurrentIndex(0)
            QMessageBox.warning(None, "Aviso", "Préstamo no encontrado.")

    def manejar_guardado(self):
        email = self.entrada_email.text().strip()
        item = self.entrada_item.text().strip()
        fecha = self.entrada_fecha.date().toString("yyyy-MM-dd")
        fin = self.entrada_fecha_fin.date().toString("yyyy-MM-dd")
        
        if not email or not item:
            QMessageBox.warning(None, "Error", "Email de Usuario y Nombre de Ítem son requeridos.")
            return
        
        existe = self.obtener_uno(email, item, fecha)
        
        try:
            if self.modo == 'crear':
                if existe:
                    QMessageBox.warning(None, "Error", "Ya existe este Préstamo.")
                    return
                self.guardar_bd(email, item, fecha, fin, "ACTIVO", False)
                QMessageBox.information(None, "Éxito", "Préstamo creado.")
            else:
                if not existe:
                    QMessageBox.warning(None, "Error", "Préstamo no encontrado para editar.")
                    return
                estado = self.combo_estado.currentText()
                if estado == 'ELIMINADA':
                    self.eliminar_fisico(email, item, fecha)
                    QMessageBox.information(None, "Info", "Préstamo eliminado físicamente.")
                else:
                    self.guardar_bd(email, item, fecha, fin, estado, True)
                    QMessageBox.information(None, "Info", "Préstamo actualizado.")
                    
            # ==================== RECARGA PROFUNDA ====================
            self.cargar_datos()
            self.limpiar_formulario()
            self.datos_actualizados.emit()     # ← Llama a Recuperar_Recargar_Verter_Variables en MainWindow

        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))