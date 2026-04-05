from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from Modulos.Views.UsuarioViews import VistaUsuario, VentanaEmergenciaRecuperacion
from Modulos.Models.UsuarioModel import UsuarioModel
from Modulos.Security.PasswordHasher import PasswordHasher

class ControladorUsuario(QObject):
    datos_actualizados = Signal()

    def __init__(self):
        super().__init__()
        self.model = UsuarioModel()
        self.vista = VistaUsuario()
        self.modo = 'crear'
        self.pass_actual_bd = ""
        self.es_upgrade_a_bibliotecario = False
        self.conectar_senales()

    def conectar_senales(self):
        v = self.vista
        v.btn_modo_crear.clicked.connect(self.establecer_modo_crear)
        v.btn_modo_editar.clicked.connect(self.establecer_modo_editar)
        v.btn_guardar.clicked.connect(self.manejar_guardado)
        v.btn_recuperar_pass.clicked.connect(self.proceso_recuperacion_emergencia)
        v.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        v.entrada_email.editingFinished.connect(self.al_terminar_edicion_email)
        v.entrada_pass_actual.textChanged.connect(self.verificar_pass_tiempo_real)
        v.combo_tipo_cuenta.currentTextChanged.connect(self.alternar_contrasena)

    # ==================== MÉTODOS DE UI ====================
    def obtener_widget_vista(self):
        return self.vista.construir_vista_listado()

    def obtener_widget_formulario(self, ctrl_param=None):
        widget = self.vista.construir_vista_formulario()
        self.cargar_combos()
        self.establecer_modo_crear(inicial=True)
        return widget

    def reiniciar_visibilidad_formulario(self):
        self.establecer_modo_crear(inicial=True)
        self.vista.widget_contenido_formulario.hide()

    def cargar_combos(self):
        try:
            tipos = self.model._obtener_tipos_usuario_bd()
            self.vista.combo_tipo_cuenta.clear()
            for t in tipos:
                self.vista.combo_tipo_cuenta.addItem(t['nombre'], t['id_tipo_usuario'])
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error cargando tipos: {e}")

    def establecer_modo_crear(self, inicial=False):
        self.modo = 'crear'
        self.es_upgrade_a_bibliotecario = False
        self.vista.btn_modo_crear.setChecked(True)
        self.vista.btn_modo_editar.setChecked(False)
        self.vista.etiqueta_estado.hide()
        self.vista.combo_estado_cuenta.hide()
        self.limpiar_formulario()
        self.alternar_contrasena("")
        if not inicial:
            self.vista.widget_contenido_formulario.show()

    def establecer_modo_editar(self):
        self.modo = 'editar'
        self.es_upgrade_a_bibliotecario = False
        self.vista.btn_modo_crear.setChecked(False)
        self.vista.btn_modo_editar.setChecked(True)
        self.vista.etiqueta_estado.show()
        self.vista.combo_estado_cuenta.show()
        self.limpiar_formulario()
        self.alternar_contrasena("")
        self.vista.widget_contenido_formulario.show()

    def limpiar_formulario(self):
        """Reset TOTAL de todos los estados visuales"""
        self.vista.entrada_nombre.clear()
        self.vista.entrada_email.clear()
        self.vista.entrada_pass_actual.clear()
        self.vista.entrada_pass_nueva.clear()
        
        # Reset explícito del botón y estilos
        self.vista.btn_guardar.setEnabled(True)
        self.vista.btn_guardar.setStyleSheet("")
        self.vista.entrada_pass_actual.setStyleSheet("")
        self.vista.entrada_pass_actual.setEnabled(True)
        
        if self.vista.combo_tipo_cuenta.count() > 0:
            self.vista.combo_tipo_cuenta.setCurrentIndex(0)
        self.vista.combo_estado_cuenta.setCurrentIndex(0)
        
        self.pass_actual_bd = ""
        self.es_upgrade_a_bibliotecario = False
        self.restaurar_visibilidad_recovery()

    def restaurar_visibilidad_recovery(self):
        es_biblio = self.vista.combo_tipo_cuenta.currentText() == "Bibliotecario"
        es_edit = self.modo == 'editar'
        mostrar_antiguos = es_biblio and es_edit and not self.es_upgrade_a_bibliotecario
        self.vista.etiqueta_pass_actual.setVisible(mostrar_antiguos)
        self.vista.entrada_pass_actual.setVisible(mostrar_antiguos)
        self.vista.btn_recuperar_pass.setVisible(mostrar_antiguos)

    def alternar_contrasena(self, _=None):
        es_biblio = self.vista.combo_tipo_cuenta.currentText() == "Bibliotecario"
        es_edit = self.modo == 'editar'

        if es_edit and es_biblio and not self.es_upgrade_a_bibliotecario:
            self.es_upgrade_a_bibliotecario = True

        self.vista.etiqueta_pass_nueva.setVisible(es_biblio)
        self.vista.entrada_pass_nueva.setVisible(es_biblio)
        self.restaurar_visibilidad_recovery()

    # ==================== CARGA Y VALIDACIÓN ====================
    def cargar_datos(self):
        datos = self.model.obtener_todos()
        self.vista.tabla.setRowCount(0)
        for i, fila in enumerate(datos):
            self.vista.tabla.insertRow(i)
            self.vista.tabla.setItem(i, 0, QTableWidgetItem(str(fila.get('Nombre', ''))))
            self.vista.tabla.setItem(i, 1, QTableWidgetItem(str(fila.get('Email', ''))))
            self.vista.tabla.setItem(i, 2, QTableWidgetItem(str(fila.get('Tipo Cuenta', ''))))
            self.vista.tabla.setItem(i, 3, QTableWidgetItem(str(fila.get('Estado', ''))))

    def filtrar_tabla(self, texto):
        texto = texto.lower()
        for i in range(self.vista.tabla.rowCount()):
            match = any(texto in str(self.vista.tabla.item(i, j).text()).lower() for j in range(4) if self.vista.tabla.item(i, j))
            self.vista.tabla.setRowHidden(i, not match)

    def verificar_pass_tiempo_real(self, texto=""):
        if self.modo != 'editar' or self.vista.combo_tipo_cuenta.currentText() != "Bibliotecario" or self.es_upgrade_a_bibliotecario:
            self.vista.btn_guardar.setEnabled(True)
            self.vista.entrada_pass_actual.setStyleSheet("")
            return

        if PasswordHasher.verify(texto, self.pass_actual_bd):
            self.vista.btn_guardar.setEnabled(True)
            self.vista.btn_guardar.setStyleSheet("background-color: #4CAF50; color: white;")
            self.vista.entrada_pass_actual.setStyleSheet("border: 2px solid green;")
        else:
            self.vista.btn_guardar.setEnabled(False)
            self.vista.btn_guardar.setStyleSheet("background-color: #cccccc;")
            self.vista.entrada_pass_actual.setStyleSheet("border: 2px solid red;" if texto else "")

    def al_terminar_edicion_email(self):
        if self.modo != 'editar': return
        email = self.vista.entrada_email.text().strip()
        if not email: return

        usuario = self.model.obtener_por_email(email)
        if usuario:
            self.vista.entrada_nombre.setText(usuario['nombre'])
            self.pass_actual_bd = usuario.get('contraseña', '')
            idx = self.vista.combo_tipo_cuenta.findData(usuario.get('id_tipo_usuario'))
            if idx >= 0:
                self.vista.combo_tipo_cuenta.setCurrentIndex(idx)
            self.vista.combo_estado_cuenta.setCurrentText(usuario.get('estado_cuenta', 'ACTIVA'))
            self.vista.entrada_pass_actual.clear()
            self.vista.entrada_pass_actual.setEnabled(True)
            self.es_upgrade_a_bibliotecario = False
            self.restaurar_visibilidad_recovery()
            # Forzar reset del botón después de cargar un nuevo usuario
            self.verificar_pass_tiempo_real("")
        else:
            QMessageBox.warning(None, "No encontrado", "Usuario no registrado.")

    def proceso_recuperacion_emergencia(self):
        from Modulos.PasswordRecover import ValidadorRecuperacion
        dialogo = ValidadorRecuperacion(self.vista)
        if dialogo.exec():
            email = dialogo.entrada_email.text().strip()
            if email:
                self.vista.entrada_email.setText(email)
                self.al_terminar_edicion_email()

            self.es_upgrade_a_bibliotecario = True
            self.vista.etiqueta_pass_actual.hide()
            self.vista.entrada_pass_actual.hide()
            self.vista.btn_recuperar_pass.hide()

            self.vista.entrada_pass_actual.clear()
            self.vista.entrada_pass_actual.setEnabled(True)
            self.vista.entrada_pass_nueva.setFocus()

            QMessageBox.information(self.vista, "Éxito", 
                                  "Identidad confirmada.\nYa puedes ingresar la nueva contraseña.")

    def manejar_guardado(self):
        nombre = self.vista.entrada_nombre.text().strip()
        email = self.vista.entrada_email.text().strip()
        id_tipo = self.vista.combo_tipo_cuenta.currentData()
        tipo_str = self.vista.combo_tipo_cuenta.currentText()
        nueva_pwd = self.vista.entrada_pass_nueva.text().strip()
        pass_actual = self.vista.entrada_pass_actual.text().strip()

        if not nombre or not email:
            QMessageBox.warning(None, "Error", "Nombre y Email son obligatorios")
            return None

        if id_tipo is None:
            QMessageBox.warning(None, "Error", "Seleccione un tipo de cuenta válido.")
            return None

        try:
            if self.modo == 'crear':
                if self.model.obtener_por_email(email):
                    QMessageBox.warning(None, "Error", "El email ya existe.")
                    return None
                if tipo_str == "Bibliotecario" and not nueva_pwd:
                    QMessageBox.warning(None, "Error", "Requiere contraseña.")
                    return None
                pals = self.model.guardar_bd(nombre, email, id_tipo, "ACTIVA", nueva_pwd, False)
                success_msg = "Usuario creado correctamente."
            else:
                # Edición normal o upgrade a Bibliotecario
                estado = self.vista.combo_estado_cuenta.currentText()
                if estado == "SUSPENDIDA":
                    self.model.eliminar_logico(email)
                    pals = []
                    success_msg = "Usuario suspendido correctamente."
                elif estado == "ELIMINADA":
                    self.model.eliminar_fisico(email)
                    pals = []
                    success_msg = "Usuario eliminado correctamente."
                else:
                    pwd_a_usar = nueva_pwd if nueva_pwd or self.es_upgrade_a_bibliotecario else pass_actual
                    pals = self.model.guardar_bd(
                        nombre, email, id_tipo, "ACTIVA", pwd_a_usar, True,
                        forzar_palabras=self.es_upgrade_a_bibliotecario
                    )
                    success_msg = "Usuario actualizado correctamente."

            self.cargar_datos()
            self.limpiar_formulario()
            self.datos_actualizados.emit()

            QMessageBox.information(None, "Éxito", success_msg)

            # VENTANA DE 12 PALABRAS SIEMPRE VISIBLE
            if pals:
                VentanaEmergenciaRecuperacion(pals, None).exec()

            return pals

        except Exception as e:
            QMessageBox.critical(None, "Error Crítico", f"No se pudo guardar: {str(e)}")
            return None