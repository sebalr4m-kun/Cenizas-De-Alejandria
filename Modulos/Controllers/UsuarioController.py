from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from Modulos.Config import Conexion

class ControladorUsuario:
    def __init__(self):
        self.bd = Conexion().obtener_conexion()
        self.ctrl_param = None
        
        self.widget_vista = None
        self.widget_formulario = None
        self.widget_contenido_formulario = None
        self.tabla = None
        self.modo = 'crear'
        self.entrada_nombre = None
        self.entrada_email = None
        self.combo_tipo_cuenta = None
        self.entrada_contrasena = None
        self.combo_estado_cuenta = None
        self.btn_modo_crear = None
        self.btn_modo_editar = None
        self.entrada_busqueda = None
        self.etiqueta_pass = None
        self.etiqueta_estado = None 

    def obtener_todos(self):
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
            SELECT u.nombre AS Nombre, u.email AS Email, 
                   p.nombre AS 'Tipo Cuenta', u.estado_cuenta AS Estado
            FROM usuarios u 
            JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
            WHERE u.estado_cuenta = 'ACTIVA'
        """
        cursor.execute(consulta)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado

    def obtener_por_email(self, email):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT *, id_tipo_usuario, estado_cuenta FROM usuarios WHERE email = %s", (email,)) 
        resultado = cursor.fetchone()
        cursor.close()
        return resultado

    def _obtener_tipos_usuario_bd(self):
        cursor = self.bd.cursor(dictionary=True)
        consulta = "SELECT id_tipo_usuario, nombre FROM param_tipos_usuario WHERE estado = 'ACTIVO'"
        cursor.execute(consulta)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado

    def guardar_bd(self, nombre, email, id_tipo, estado, contrasena, es_actualizacion):
        cursor = self.bd.cursor()
        try:
            if es_actualizacion:
                consulta = "UPDATE usuarios SET nombre=%s, id_tipo_usuario=%s, estado_cuenta=%s"
                params = [nombre, id_tipo, estado]
                if contrasena is not None:
                    consulta += ", contraseña=%s"
                    params.append(contrasena)
                consulta += " WHERE email=%s"
                params.append(email)
                cursor.execute(consulta, tuple(params))
            else:
                cursor.execute("""
                    INSERT INTO usuarios (nombre, email, id_tipo_usuario, estado_cuenta, contraseña) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (nombre, email, id_tipo, estado, contrasena or ''))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_logico(self, email):
        cursor = self.bd.cursor()
        try:
            cursor.execute("UPDATE usuarios SET estado_cuenta = 'INACTIVA' WHERE email = %s", (email,))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_fisico(self, email):
        cursor = self.bd.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE email = %s", (email,))
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
        
        titulo = QLabel("Gestión de Usuarios")
        titulo.setProperty("isTitle", True)
        layout.addWidget(titulo)
        
        layout_busqueda = QHBoxLayout()
        self.entrada_busqueda = QLineEdit(placeholderText="Filtrar...")
        self.entrada_busqueda.setObjectName("SearchInput")
        self.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        layout_busqueda.addWidget(self.entrada_busqueda)
        layout.addLayout(layout_busqueda)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Email", "Tipo Cuenta", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)
        
        self.cargar_datos()
        return self.widget_vista

    def reiniciar_visibilidad_formulario(self):
        if self.widget_contenido_formulario:
            self.widget_contenido_formulario.hide() 
        self.establecer_modo_crear(inicial=True)

    def obtener_widget_formulario(self, ctrl_param):
        self.ctrl_param = ctrl_param
        if self.widget_formulario:
            return self.widget_formulario
        
        self.widget_formulario = QWidget()
        layout_principal = QVBoxLayout(self.widget_formulario)
        
        layout_principal.addWidget(QLabel("Acciones"))
        layout_modo = QHBoxLayout()
        self.btn_modo_crear = QPushButton("Crear Nuevo")
        self.btn_modo_crear.setCheckable(True)
        self.btn_modo_crear.setChecked(True)
        self.btn_modo_crear.clicked.connect(self.establecer_modo_crear)
        self.btn_modo_editar = QPushButton("Editar Existente")
        self.btn_modo_editar.setCheckable(True)
        self.btn_modo_editar.clicked.connect(self.establecer_modo_editar)
        
        layout_modo.addWidget(self.btn_modo_crear)
        layout_modo.addWidget(self.btn_modo_editar)
        layout_principal.addLayout(layout_modo)

        self.widget_contenido_formulario = QWidget()
        layout_contenido = QVBoxLayout(self.widget_contenido_formulario)

        layout_contenido.addWidget(QLabel("Email (Identificador Único)"))
        self.entrada_email = QLineEdit()
        self.entrada_email.setPlaceholderText("ejemplo@email.com")
        self.entrada_email.editingFinished.connect(self.al_terminar_edicion_email)
        layout_contenido.addWidget(self.entrada_email)

        layout_contenido.addWidget(QLabel("Nombre Completo"))
        self.entrada_nombre = QLineEdit()
        layout_contenido.addWidget(self.entrada_nombre)
        
        layout_contenido.addWidget(QLabel("Tipo de Cuenta"))
        self.combo_tipo_cuenta = QComboBox()
        self.cargar_combos()
        layout_contenido.addWidget(self.combo_tipo_cuenta)
        
        self.etiqueta_pass = QLabel("Contraseña")
        self.entrada_contrasena = QLineEdit()
        self.entrada_contrasena.setEchoMode(QLineEdit.Password)
        self.etiqueta_pass.hide() 
        self.entrada_contrasena.hide() 
        layout_contenido.addWidget(self.etiqueta_pass)
        layout_contenido.addWidget(self.entrada_contrasena)
        
        self.etiqueta_estado = QLabel("Estado")
        self.etiqueta_estado.hide() 
        layout_contenido.addWidget(self.etiqueta_estado)
        
        self.combo_estado_cuenta = QComboBox()
        self.combo_estado_cuenta.addItems(["ACTIVA", "SUSPENDIDA", "ELIMINADA"])
        self.combo_estado_cuenta.hide()
        layout_contenido.addWidget(self.combo_estado_cuenta)
        layout_contenido.addStretch()
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.clicked.connect(self.manejar_guardado)
        layout_contenido.addWidget(self.btn_guardar)
        self.combo_tipo_cuenta.currentTextChanged.connect(self.alternar_contrasena)
        layout_principal.addWidget(self.widget_contenido_formulario)
        layout_principal.addStretch()
        
        self.widget_contenido_formulario.hide() 
        self.establecer_modo_crear(inicial=True) 

        return self.widget_formulario

    def cargar_combos(self):
        try:
            tipos = self._obtener_tipos_usuario_bd() 
        except Exception as e:
            QMessageBox.critical(None, "Error de DB", f"No se pudo cargar Tipos de Usuario: {e}")
            tipos = []
            
        self.combo_tipo_cuenta.clear()
        for t in tipos:
            dato_item = t['id_tipo_usuario']
            self.combo_tipo_cuenta.addItem(t['nombre'], dato_item)
        
        if self.combo_tipo_cuenta.count() > 0:
             self.alternar_contrasena(self.combo_tipo_cuenta.currentText())
        else:
             self.alternar_contrasena("")

    def establecer_modo_crear(self, inicial=False):
        self.modo = 'crear'
        self.btn_modo_crear.setChecked(True)
        self.btn_modo_editar.setChecked(False)
        
        if self.etiqueta_estado: self.etiqueta_estado.hide()
        self.combo_estado_cuenta.hide() 
        
        self.entrada_email.setEnabled(True)
        self.limpiar_formulario()
        
        if self.combo_tipo_cuenta.count() > 0:
            self.alternar_contrasena(self.combo_tipo_cuenta.currentText())
        
        if not inicial and self.widget_contenido_formulario:
            self.widget_contenido_formulario.show()

    def establecer_modo_editar(self):
        self.modo = 'editar'
        self.btn_modo_crear.setChecked(False)
        self.btn_modo_editar.setChecked(True)
        
        if self.etiqueta_estado: self.etiqueta_estado.show()
        self.combo_estado_cuenta.show()
        
        self.entrada_email.setEnabled(True)
        self.limpiar_formulario()
        
        if self.combo_tipo_cuenta.count() > 0:
            self.alternar_contrasena(self.combo_tipo_cuenta.currentText())

        if self.widget_contenido_formulario:
            self.widget_contenido_formulario.show()

    def limpiar_formulario(self):
        self.entrada_nombre.clear()
        self.entrada_email.clear()
        self.entrada_contrasena.clear()
        if self.combo_tipo_cuenta.count() > 0:
            self.combo_tipo_cuenta.setCurrentIndex(0)
        self.combo_estado_cuenta.setCurrentIndex(0)

    def alternar_contrasena(self, texto):
        visible = (texto == "Bibliotecario")
        if self.etiqueta_pass:
             self.etiqueta_pass.setVisible(visible)
        if self.entrada_contrasena:
             self.entrada_contrasena.setVisible(visible)

    def cargar_datos(self):
        datos = self.obtener_todos() 
        self.tabla.setRowCount(0)
        for indice_fila, datos_fila in enumerate(datos):
            self.tabla.insertRow(indice_fila)
            self.tabla.setItem(indice_fila, 0, QTableWidgetItem(datos_fila['Nombre']))
            self.tabla.setItem(indice_fila, 1, QTableWidgetItem(datos_fila['Email']))
            self.tabla.setItem(indice_fila, 2, QTableWidgetItem(datos_fila['Tipo Cuenta']))
            self.tabla.setItem(indice_fila, 3, QTableWidgetItem(datos_fila['Estado']))

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

    def al_terminar_edicion_email(self):
        if self.modo != 'editar': 
            return

        email = self.entrada_email.text().strip()
        if not email: 
            self.entrada_nombre.clear()
            self.entrada_contrasena.clear()
            self.combo_tipo_cuenta.setCurrentIndex(0)
            self.combo_estado_cuenta.setCurrentIndex(0)
            return
        
        usuario = self.obtener_por_email(email)
        
        if usuario:
            self.entrada_nombre.setText(usuario['nombre'])
            indice = self.combo_tipo_cuenta.findData(usuario['id_tipo_usuario'])
            if indice >= 0: self.combo_tipo_cuenta.setCurrentIndex(indice)
            
            if usuario['estado_cuenta'] == 'INACTIVA':
                self.combo_estado_cuenta.setCurrentText('SUSPENDIDA')
            else:
                self.combo_estado_cuenta.setCurrentText(usuario['estado_cuenta'])

            self.entrada_contrasena.clear()
            QMessageBox.information(None, "Carga Exitosa", "Usuario encontrado y datos cargados para edición.")
        else:
            QMessageBox.warning(None, "No encontrado", "Usuario no encontrado para editar. Cambie a modo 'Crear Nuevo' si desea crearlo.")
            self.entrada_nombre.clear()
            self.entrada_contrasena.clear()
            self.combo_tipo_cuenta.setCurrentIndex(0)
            self.combo_estado_cuenta.setCurrentIndex(0)

    def manejar_guardado(self):
        nombre = self.entrada_nombre.text().strip()
        email = self.entrada_email.text().strip()
        id_tipo = self.combo_tipo_cuenta.currentData()
        tipo_str = self.combo_tipo_cuenta.currentText()
        pwd = self.entrada_contrasena.text()

        if not nombre or not email:
            QMessageBox.warning(None, "Error", "Nombre y Email son obligatorios")
            return
        
        existe = self.obtener_por_email(email)

        if self.modo == 'crear':
            if existe:
                QMessageBox.warning(None, "Error", "Ya existe un usuario con este Email.")
                return
            
            if tipo_str == "Bibliotecario" and not pwd.strip():
                QMessageBox.warning(None, "Error", "El Bibliotecario necesita una Contraseña.")
                return

            try:
                self.guardar_bd(nombre, email, id_tipo, "ACTIVA", pwd.strip(), False)
                QMessageBox.information(None, "Éxito", "Usuario creado.")
            except Exception as e:
                QMessageBox.critical(None, "Error de DB", str(e))
        
        else: 
            if not existe:
                QMessageBox.warning(None, "Error", "Usuario no encontrado para editar.")
                return
            
            estado_ui = self.combo_estado_cuenta.currentText()
            
            if tipo_str != "Bibliotecario":
                pwd = None
            elif not pwd.strip():
                pwd = None 
            
            try:
                if estado_ui == "SUSPENDIDA":
                    self.eliminar_logico(email)
                    QMessageBox.information(None, "Info", "Usuario suspendido (INACTIVA).")
                elif estado_ui == "ELIMINADA":
                    self.eliminar_fisico(email)
                    QMessageBox.information(None, "Info", "Usuario eliminado permanentemente.")
                else:
                    self.guardar_bd(nombre, email, id_tipo, "ACTIVA", pwd, True) 
                    QMessageBox.information(None, "Éxito", "Usuario actualizado.")
                    
            except Exception as e:
                QMessageBox.critical(None, "Error de DB", str(e))
        self.cargar_datos()
        self.limpiar_formulario()