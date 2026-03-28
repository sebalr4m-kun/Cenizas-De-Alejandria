import random
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem
from PySide6.QtCore import Qt, QObject
from Modulos.Config import Conexion
from Modulos.Views.UsuarioViews import VistaUsuario, VentanaEmergenciaRecuperacion

class ControladorUsuario(QObject):
    def __init__(self):
        super().__init__()
        self.bd = Conexion().obtener_conexion()
        self.ctrl_param = None
        
        # Instanciamos la Vista
        self.vista = VistaUsuario()
        
        self.modo = 'crear'
        self.pass_actual_bd = ""

        # Conectar Señales de la Vista a la Lógica del Controlador
        self.vista.btn_modo_crear.clicked.connect(self.establecer_modo_crear)
        self.vista.btn_modo_editar.clicked.connect(self.establecer_modo_editar)
        self.vista.btn_guardar.clicked.connect(self.manejar_guardado)
        self.vista.btn_recuperar_pass.clicked.connect(self.proceso_recuperacion_emergencia)
        self.vista.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        self.vista.entrada_email.editingFinished.connect(self.al_terminar_edicion_email)
        self.vista.entrada_pass_actual.textChanged.connect(self.verificar_pass_tiempo_real)
        self.vista.combo_tipo_cuenta.currentTextChanged.connect(self.alternar_contrasena)

    # --- MÉTODOS DE BASE DE DATOS (ABM) ---

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
            cursor.execute("SELECT nombre FROM param_tipos_usuario WHERE id_tipo_usuario = %s", (id_tipo,))
            res_tipo = cursor.fetchone()
            nombre_tipo = res_tipo[0] if res_tipo else ""

            if es_actualizacion:
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
                cursor.execute("""
                    INSERT INTO usuarios (nombre, email, id_tipo_usuario, estado_cuenta, contraseña) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (nombre, email, id_tipo, estado, contrasena or ''))
                target_id_usuario = cursor.lastrowid

            if nombre_tipo == "Bibliotecario":
                indices_num = [random.randint(1, 999) for _ in range(12)]
                indices_txt = ", ".join(map(str, indices_num))
                palabras_recuperacion = []
                for idx in indices_num:
                    cursor.execute("SELECT palabra FROM param_diccionario_seguridad WHERE id_palabra = %s", (idx,))
                    res = cursor.fetchone()
                    palabras_recuperacion.append(res[0] if res else f"Error-ID-{idx}")

                if es_actualizacion:
                    cursor.execute("DELETE FROM seguridad_recuperacion WHERE id_usuario = %s", (target_id_usuario,))

                cursor.execute("""
                    INSERT INTO seguridad_recuperacion (id_usuario, indices_palabras)
                    VALUES (%s, %s)
                """, (target_id_usuario, indices_txt))

                ventana = VentanaEmergenciaRecuperacion(palabras_recuperacion, self.vista)
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

    # --- LÓGICA DE CONTROL ---

    def obtener_widget_vista(self):
        return self.vista.construir_vista_listado()

    def obtener_widget_formulario(self, ctrl_param):
        self.ctrl_param = ctrl_param
        widget = self.vista.construir_vista_formulario()
        self.cargar_combos()
        self.establecer_modo_crear(inicial=True)
        return widget

    def cargar_combos(self):
        try:
            tipos = self._obtener_tipos_usuario_bd() 
        except Exception as e:
            QMessageBox.critical(None, "Error de DB", f"No se pudo cargar Tipos de Usuario: {e}")
            tipos = []
            
        self.vista.combo_tipo_cuenta.clear()
        for t in tipos:
            self.vista.combo_tipo_cuenta.addItem(t['nombre'], t['id_tipo_usuario'])
        
        if self.vista.combo_tipo_cuenta.count() > 0:
            self.alternar_contrasena(self.vista.combo_tipo_cuenta.currentText())

    def establecer_modo_crear(self, inicial=False):
        self.modo = 'crear'
        self.vista.btn_modo_crear.setChecked(True)
        self.vista.btn_modo_editar.setChecked(False)
        self.vista.etiqueta_estado.hide()
        self.vista.combo_estado_cuenta.hide() 
        self.vista.entrada_email.setEnabled(True)
        self.limpiar_formulario()
        self.alternar_contrasena(self.vista.combo_tipo_cuenta.currentText())
        if not inicial:
            self.vista.widget_contenido_formulario.show()

    def establecer_modo_editar(self):
        self.modo = 'editar'
        self.vista.btn_modo_crear.setChecked(False)
        self.vista.btn_modo_editar.setChecked(True)
        self.vista.etiqueta_estado.show()
        self.vista.combo_estado_cuenta.show()
        self.vista.entrada_email.setEnabled(True)
        self.limpiar_formulario()
        self.alternar_contrasena(self.vista.combo_tipo_cuenta.currentText())
        self.vista.widget_contenido_formulario.show()

    def limpiar_formulario(self):
        self.vista.entrada_nombre.clear()
        self.vista.entrada_email.clear()
        self.vista.entrada_pass_actual.clear()
        self.vista.entrada_pass_nueva.clear()
        if self.vista.combo_tipo_cuenta.count() > 0:
            self.vista.combo_tipo_cuenta.setCurrentIndex(0)
        self.vista.combo_estado_cuenta.setCurrentIndex(0)

    def alternar_contrasena(self, texto):
        visible = (texto == "Bibliotecario")
        es_edicion = (self.modo == 'editar')
        self.vista.etiqueta_pass_actual.setVisible(visible)
        self.vista.entrada_pass_actual.setVisible(visible)
        self.vista.btn_recuperar_pass.setVisible(visible and es_edicion)
        self.vista.etiqueta_pass_nueva.setVisible(visible and es_edicion)
        self.vista.entrada_pass_nueva.setVisible(visible and es_edicion)

    def cargar_datos(self):
        datos = self.obtener_todos() 
        self.vista.tabla.setRowCount(0)
        for i, fila in enumerate(datos):
            self.vista.tabla.insertRow(i)
            self.vista.tabla.setItem(i, 0, QTableWidgetItem(fila['Nombre']))
            self.vista.tabla.setItem(i, 1, QTableWidgetItem(fila['Email']))
            self.vista.tabla.setItem(i, 2, QTableWidgetItem(fila['Tipo Cuenta']))
            self.vista.tabla.setItem(i, 3, QTableWidgetItem(fila['Estado']))

    def filtrar_tabla(self, texto):
        texto = texto.lower()
        for i in range(self.vista.tabla.rowCount()):
            coincidencia = any(texto in (self.vista.tabla.item(i, j).text().lower() if self.vista.tabla.item(i, j) else "") for j in range(self.vista.tabla.columnCount()))
            self.vista.tabla.setRowHidden(i, not coincidencia)

    def verificar_pass_tiempo_real(self, texto_ingresado):
        if self.modo == 'editar' and self.vista.combo_tipo_cuenta.currentText() == "Bibliotecario":
            if texto_ingresado == self.pass_actual_bd: 
                self.vista.btn_guardar.setEnabled(True)
                self.vista.btn_guardar.setStyleSheet("background-color: #4CAF50; color: white;")
                self.vista.entrada_pass_actual.setStyleSheet("border: 2px solid green;")
            else:
                self.vista.btn_guardar.setEnabled(False)
                self.vista.btn_guardar.setStyleSheet("background-color: #cccccc;")
                self.vista.entrada_pass_actual.setStyleSheet("border: 2px solid red;")

    def al_terminar_edicion_email(self):
        if self.modo != 'editar': return
        email = self.vista.entrada_email.text().strip()
        if not email: return
        
        usuario = self.obtener_por_email(email)
        if usuario:
            self.vista.entrada_nombre.setText(usuario['nombre'])
            self.pass_actual_bd = usuario['contraseña']
            idx = self.vista.combo_tipo_cuenta.findData(usuario['id_tipo_usuario'])
            if idx >= 0: self.vista.combo_tipo_cuenta.setCurrentIndex(idx)
            
            if self.vista.combo_tipo_cuenta.currentText() == "Bibliotecario":
                self.vista.btn_guardar.setEnabled(False)
                self.vista.btn_guardar.setStyleSheet("background-color: #cccccc;")
            
            self.vista.combo_estado_cuenta.setCurrentText('SUSPENDIDA' if usuario['estado_cuenta'] == 'INACTIVA' else usuario['estado_cuenta'])
            QMessageBox.information(None, "Carga Exitosa", "Datos cargados.")
        else:
            QMessageBox.warning(None, "No encontrado", "Usuario no encontrado.")

    def proceso_recuperacion_emergencia(self):
        from Modulos.PasswordRecover import ValidadorRecuperacion
        dialogo = ValidadorRecuperacion(self.vista)
        if dialogo.exec():
            QMessageBox.information(None, "Éxito", "Identidad confirmada.")
            self.vista.btn_guardar.setEnabled(True)
            self.vista.entrada_pass_nueva.setFocus()
            self.vista.entrada_pass_actual.setText("RECUPERADO_POR_PALABRAS") 
            self.vista.entrada_pass_actual.setEnabled(False)

    def manejar_guardado(self):
        nombre = self.vista.entrada_nombre.text().strip()
        email = self.vista.entrada_email.text().strip()
        id_tipo = self.vista.combo_tipo_cuenta.currentData()
        tipo_str = self.vista.combo_tipo_cuenta.currentText()
        
        nueva_pwd = self.vista.entrada_pass_nueva.text().strip()
        pass_final = nueva_pwd if nueva_pwd else self.pass_actual_bd

        if not nombre or not email:
            QMessageBox.warning(None, "Error", "Nombre y Email son obligatorios")
            return
        
        try:
            if self.modo == 'crear':
                if self.obtener_por_email(email):
                    QMessageBox.warning(None, "Error", "El email ya existe.")
                    return
                pwd_crear = self.vista.entrada_pass_actual.text().strip()
                if tipo_str == "Bibliotecario" and not pwd_crear:
                    QMessageBox.warning(None, "Error", "Requiere contraseña.")
                    return
                self.guardar_bd(nombre, email, id_tipo, "ACTIVA", pwd_crear, False)
            else:
                estado_ui = self.vista.combo_estado_cuenta.currentText()
                if estado_ui == "SUSPENDIDA":
                    self.eliminar_logico(email)
                elif estado_ui == "ELIMINADA":
                    self.eliminar_fisico(email)
                else:
                    self.guardar_bd(nombre, email, id_tipo, "ACTIVA", pass_final, True)
            
            self.cargar_datos()
            self.limpiar_formulario()
            QMessageBox.information(None, "Éxito", "Operación completada.")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))