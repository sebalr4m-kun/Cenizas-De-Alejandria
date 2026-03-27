from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from Modulos.Config import Conexion


class VentanaEmergenciaRecuperacion(QDialog):
    def __init__(self, palabras, padre=None):
        super().__init__(padre)
        self.setWindowTitle("SISTEMA DE RECUPERACIÓN DE EMERGENCIA")
        self.setFixedSize(480, 500) # Aumentamos un poco el alto por si acaso
        self.setModal(True)
        
        # --- SOLUCIÓN A LA 'X' ---
        # Quitamos el botón de cerrar y la ayuda, dejando solo el título
        self.setWindowFlags(Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        layout = QVBoxLayout(self)

        # Aviso crítico
        aviso = QLabel("⚠️ ATENCIÓN: GUARDE ESTAS PALABRAS EN UN LUGAR SEGURO ⚠️")
        aviso.setStyleSheet("color: #FF4444; font-weight: bold; font-size: 14px;")
        aviso.setWordWrap(True)
        layout.addWidget(aviso)

        # --- SOLUCIÓN AL TEXTO CORTADO ---
        desc = QLabel("Estas 12 palabras son el único método para recuperar su acceso si olvida la contraseña:")
        desc.setWordWrap(True) # Esto asegura que el texto baje de línea si no cabe
        layout.addWidget(desc)

        # Área de texto para copiar y pegar
        self.caja_texto = QTextEdit()
        self.caja_texto.setReadOnly(True)
        self.caja_texto.setText("\n".join([f"{i+1}. {p}" for i, p in enumerate(palabras)]))
        # Estilo para que se vea más profesional
        self.caja_texto.setStyleSheet("font-family: 'Consolas'; font-size: 12px; background-color: #f0f0f0;")
        layout.addWidget(self.caja_texto)

        # Botón con cuenta regresiva
        self.btn_confirmar = QPushButton("Espere 10 segundos...")
        self.btn_confirmar.setEnabled(False)
        self.btn_confirmar.clicked.connect(self.accept)
        layout.addWidget(self.btn_confirmar)

        # Lógica del temporizador
        self.segundos_restantes = 10
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_timer)
        self.timer.start(1000)
        self.pass_actual_bd = None # Para comparar en tiempo real

    def actualizar_timer(self):
        self.segundos_restantes -= 1
        if self.segundos_restantes > 0:
            self.btn_confirmar.setText(f"Espere {self.segundos_restantes} segundos...")
        else:
            self.timer.stop()
            self.btn_confirmar.setText("¡Ya guardé mi código!")
            self.btn_confirmar.setEnabled(True)
            self.btn_confirmar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

    # --- PROTECCIÓN EXTRA ---
    # Evita que se cierre con Alt+F4 o cualquier otro método externo
    def closeEvent(self, event):
        if self.segundos_restantes > 0:
            event.ignore()
        else:
            super().closeEvent(event)

    def actualizar_timer(self):
        self.segundos_restantes -= 1
        if self.segundos_restantes > 0:
            self.btn_confirmar.setText(f"Espere {self.segundos_restantes} segundos...")
        else:
            self.timer.stop()
            self.btn_confirmar.setText("¡Ya guardé mi código!")
            self.btn_confirmar.setEnabled(True)
            self.btn_confirmar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

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
        self.pass_actual_bd = ""

    def proceso_recuperacion_emergencia(self):
        from Modulos.PasswordRecover import ValidadorRecuperacion
        
        dialogo = ValidadorRecuperacion(self.widget_formulario)
        if dialogo.exec():
            # Si las 12 palabras son correctas:
            QMessageBox.information(None, "Éxito", "Identidad confirmada. Ahora puede establecer una nueva contraseña.")
            
            # Forzamos que la pass_actual_bd sea reconocida como 'válida' 
            # o simplemente habilitamos el botón de guardar directamente
            self.btn_guardar.setEnabled(True)
            self.entrada_pass_nueva.setFocus()
            # Opcional: podrías limpiar el campo de pass_actual para que no estorbe
            self.entrada_pass_actual.setText("RECUPERADO_POR_PALABRAS") 
            self.entrada_pass_actual.setEnabled(False)

    def verificar_pass_tiempo_real(self, texto_ingresado):
        # 1. Obtenemos el valor de forma segura. Si no existe, será ""
        pass_bd = getattr(self, 'pass_actual_bd', "")
        
        if self.modo == 'editar' and self.combo_tipo_cuenta.currentText() == "Bibliotecario":
            # 2. USAMOS pass_bd (la variable local segura) en lugar de self.pass_actual_bd
            if texto_ingresado == pass_bd: 
                self.btn_guardar.setEnabled(True)
                self.btn_guardar.setStyleSheet("background-color: #4CAF50; color: white;")
                self.entrada_pass_actual.setStyleSheet("border: 2px solid green;")
            else:
                self.btn_guardar.setEnabled(False)
                self.btn_guardar.setStyleSheet("background-color: #cccccc;")
                self.entrada_pass_actual.setStyleSheet("border: 2px solid red;")

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
            import random
            cursor = self.bd.cursor()
            try:
                # 1. Obtenemos el nombre del tipo AL PRINCIPIO para que esté disponible en ambos casos
                cursor.execute("SELECT nombre FROM param_tipos_usuario WHERE id_tipo_usuario = %s", (id_tipo,))
                res_tipo = cursor.fetchone()
                nombre_tipo = res_tipo[0] if res_tipo else ""

                if es_actualizacion:
                    # Obtenemos el ID del usuario existente mediante su email
                    cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
                    res_id = cursor.fetchone()
                    target_id_usuario = res_id[0] if res_id else None

                    consulta = "UPDATE usuarios SET nombre=%s, id_tipo_usuario=%s, estado_cuenta=%s"
                    params = [nombre, id_tipo, estado]
                    if contrasena is not None:
                        consulta += ", contraseña=%s"
                        params.append(contrasena)
                    consulta += " WHERE email=%s"
                    params.append(email)
                    cursor.execute(consulta, tuple(params))
                else:
                    # Creación normal
                    cursor.execute("""
                        INSERT INTO usuarios (nombre, email, id_tipo_usuario, estado_cuenta, contraseña) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, (nombre, email, id_tipo, estado, contrasena or ''))
                    target_id_usuario = cursor.lastrowid

                # 2. Ahora nombre_tipo y target_id_usuario SIEMPRE existen
                if nombre_tipo == "Bibliotecario":
                    indices_num = [random.randint(1, 999) for _ in range(12)]
                    indices_txt = ", ".join(map(str, indices_num))
                    
                    palabras_recuperacion = []
                    for idx in indices_num:
                        cursor.execute("SELECT palabra FROM param_diccionario_seguridad WHERE id_palabra = %s", (idx,))
                        res = cursor.fetchone()
                        if res:
                            palabras_recuperacion.append(res[0])
                        else:
                            palabras_recuperacion.append(f"Error-ID-{idx}")

                    # Si es edición, podrías querer borrar las palabras viejas antes de insertar nuevas
                    if es_actualizacion:
                        cursor.execute("DELETE FROM seguridad_recuperacion WHERE id_usuario = %s", (target_id_usuario,))

                    cursor.execute("""
                        INSERT INTO seguridad_recuperacion (id_usuario, indices_palabras)
                        VALUES (%s, %s)
                    """, (target_id_usuario, indices_txt))

                    ventana = VentanaEmergenciaRecuperacion(palabras_recuperacion)
                    ventana.exec()

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
        self.widget_formulario = QWidget()
        layout_principal = QVBoxLayout(self.widget_formulario)
        
        # --- SECCIÓN DE MODOS (Crear/Editar) ---
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

        # --- CONTENEDOR DEL FORMULARIO ---
        self.widget_contenido_formulario = QWidget()
        layout_contenido = QVBoxLayout(self.widget_contenido_formulario)

        # Email
        layout_contenido.addWidget(QLabel("Email (Identificador Único)"))
        self.entrada_email = QLineEdit()
        self.entrada_email.setPlaceholderText("ejemplo@email.com")
        self.entrada_email.editingFinished.connect(self.al_terminar_edicion_email)
        layout_contenido.addWidget(self.entrada_email)

        # Nombre
        layout_contenido.addWidget(QLabel("Nombre Completo"))
        self.entrada_nombre = QLineEdit()
        layout_contenido.addWidget(self.entrada_nombre)
        
        # Tipo de Cuenta
        layout_contenido.addWidget(QLabel("Tipo de Cuenta"))
        self.combo_tipo_cuenta = QComboBox()
        layout_contenido.addWidget(self.combo_tipo_cuenta)

        # --- SECCIÓN DE CONTRASEÑA (DEFINICIÓN ÚNICA) ---
        self.etiqueta_pass_actual = QLabel("Contraseña Actual (Requerida para Bibliotecarios)")
        self.entrada_pass_actual = QLineEdit()
        self.entrada_pass_actual.setEchoMode(QLineEdit.Password)
        self.entrada_pass_actual.setPlaceholderText("Escriba su contraseña actual...")
        self.entrada_pass_actual.textChanged.connect(self.verificar_pass_tiempo_real)

        # ... debajo de self.entrada_pass_actual ...
        self.btn_recuperar_pass = QPushButton("¿Olvidó su contraseña?")
        self.btn_recuperar_pass.setStyleSheet("color: #3498db; border: none; background: transparent; text-decoration: underline;")
        self.btn_recuperar_pass.setCursor(Qt.PointingHandCursor)
        self.btn_recuperar_pass.clicked.connect(self.proceso_recuperacion_emergencia)
        
        # Ocultar por defecto, solo se ve en edición y si es Bibliotecario
        self.btn_recuperar_pass.hide() 
        
        layout_contenido.addWidget(self.btn_recuperar_pass)
        
        self.etiqueta_pass_nueva = QLabel("Nueva Contraseña (Opcional)")
        self.entrada_pass_nueva = QLineEdit()
        self.entrada_pass_nueva.setEchoMode(QLineEdit.Password)
        self.entrada_pass_nueva.setPlaceholderText("Dejar vacío para no cambiar")
        
        # Añadimos al layout
        layout_contenido.addWidget(self.etiqueta_pass_actual)
        layout_contenido.addWidget(self.entrada_pass_actual)
        layout_contenido.addWidget(self.etiqueta_pass_nueva)
        layout_contenido.addWidget(self.entrada_pass_nueva)

        # --- ESTADO Y GUARDADO ---
        self.etiqueta_estado = QLabel("Estado")
        self.combo_estado_cuenta = QComboBox()
        self.combo_estado_cuenta.addItems(["ACTIVA", "SUSPENDIDA", "ELIMINADA"])
        
        layout_contenido.addWidget(self.etiqueta_estado)
        layout_contenido.addWidget(self.combo_estado_cuenta)
        
        layout_contenido.addStretch()
        
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setObjectName("ActionButton")
        self.btn_guardar.clicked.connect(self.manejar_guardado)
        layout_contenido.addWidget(self.btn_guardar)

        # --- CONEXIÓN DE SEÑALES Y CARGA FINAL ---
        self.combo_tipo_cuenta.currentTextChanged.connect(self.alternar_contrasena)
        
        # Ahora que todo existe, cargamos los datos
        self.cargar_combos() 
        
        layout_principal.addWidget(self.widget_contenido_formulario)
        layout_principal.addStretch()
        
        # Estado inicial
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
        self.entrada_pass_actual.clear() # Asegúrate de usar los nuevos nombres aquí también
        self.entrada_pass_nueva.clear()
        if self.combo_tipo_cuenta.count() > 0:
            self.combo_tipo_cuenta.setCurrentIndex(0)
        self.combo_estado_cuenta.setCurrentIndex(0)

    def alternar_contrasena(self, texto):
        visible = (texto == "Bibliotecario")
        es_edicion = (self.modo == 'editar')
        
        self.etiqueta_pass_actual.setVisible(visible)
        self.entrada_pass_actual.setVisible(visible)
        
        # El botón de recuperar solo aparece en edición de Bibliotecario
        self.btn_recuperar_pass.setVisible(visible and es_edicion)
        
        self.etiqueta_pass_nueva.setVisible(visible and es_edicion)
        self.entrada_pass_nueva.setVisible(visible and es_edicion)

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
            self.pass_actual_bd = usuario['contraseña'] # <--- GUARDAMOS LA PASS DE LA BD
            indice = self.combo_tipo_cuenta.findData(usuario['id_tipo_usuario'])
            if indice >= 0: self.combo_tipo_cuenta.setCurrentIndex(indice)
            
            # Si es Bibliotecario, bloqueamos el botón hasta que valide
            if self.combo_tipo_cuenta.currentText() == "Bibliotecario":
                self.btn_guardar.setEnabled(False)
                self.btn_guardar.setStyleSheet("background-color: #cccccc;")
            
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
        
        # Lógica de contraseña: Si hay algo en 'nueva', usamos eso. Si no, mantenemos la que ya estaba en la BD.
        nueva_pwd = self.entrada_pass_nueva.text().strip()
        pass_final = nueva_pwd if nueva_pwd else self.pass_actual_bd

        if not nombre or not email:
            QMessageBox.warning(None, "Error", "Nombre y Email son obligatorios")
            return
        
        try:
            if self.modo == 'crear':
                # Validamos que no exista antes de intentar crear
                if self.obtener_por_email(email):
                    QMessageBox.warning(None, "Error", "Ya existe un usuario con este Email.")
                    return
                
                pwd_crear = self.entrada_pass_actual.text().strip()
                if tipo_str == "Bibliotecario" and not pwd_crear:
                    QMessageBox.warning(None, "Error", "El Bibliotecario requiere contraseña.")
                    return
                    
                self.guardar_bd(nombre, email, id_tipo, "ACTIVA", pwd_crear, False)
                QMessageBox.information(None, "Éxito", "Usuario creado.")
            
            else: # MODO EDICIÓN
                estado_ui = self.combo_estado_cuenta.currentText()
                if estado_ui == "SUSPENDIDA":
                    self.eliminar_logico(email)
                elif estado_ui == "ELIMINADA":
                    self.eliminar_fisico(email)
                else:
                    # Guardamos con pass_final (la nueva si escribió algo, o la actual si no)
                    self.guardar_bd(nombre, email, id_tipo, "ACTIVA", pass_final, True)
                QMessageBox.information(None, "Éxito", "Cambios aplicados correctamente.")
            
            self.cargar_datos()
            self.limpiar_formulario()
            
        except Exception as e:
            QMessageBox.critical(None, "Error de Base de Datos", str(e))