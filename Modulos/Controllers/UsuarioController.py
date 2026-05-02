import re
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
        """Protocolo para limpiar la interfaz desde el exterior (Main)"""
        self.establecer_modo_crear(inicial=True)
        if hasattr(self.vista, 'widget_contenido_formulario'):
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
        if not inicial and hasattr(self.vista, 'widget_contenido_formulario'):
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
        if hasattr(self.vista, 'widget_contenido_formulario'):
            self.vista.widget_contenido_formulario.show()

    def limpiar_formulario(self):
        """Limpia los campos internos del formulario[cite: 1]"""
        self.vista.entrada_nombre.clear()
        self.vista.entrada_email.clear()
        self.vista.entrada_pass_actual.clear()
        self.vista.entrada_pass_nueva.clear()
        
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
            match = any(texto in str(self.vista.tabla.item(i, j).text()).lower() 
                       for j in range(4) if self.vista.tabla.item(i, j))
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
        if self.modo != 'editar': 
            return
        email = self.vista.entrada_email.text().strip()
        if not email: 
            return

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
            self.vista.entrada_pass_nueva.setFocus()
            self.vista.btn_guardar.setEnabled(True)
            QMessageBox.information(self.vista, "Éxito", "Identidad confirmada.")

    # ==================== LÓGICA DE GUARDADO CRÍTICA ====================
    def manejar_guardado(self):
        """Ejecuta validaciones totales y guarda en BD[cite: 2]"""
        nombre = self.vista.entrada_nombre.text().strip()
        email = self.vista.entrada_email.text().strip()
        id_tipo = self.vista.combo_tipo_cuenta.currentData()
        tipo_str = self.vista.combo_tipo_cuenta.currentText()
        nueva_pwd = self.vista.entrada_pass_nueva.text().strip()
        pass_actual = self.vista.entrada_pass_actual.text().strip()

        # 1. Validación de campos obligatorios[cite: 2]
        if not nombre or not email:
            QMessageBox.warning(self.vista, "Campos Incompletos", "Nombre y Email son obligatorios.")
            return None

        # 2. Validación de Email mediante REGEX[cite: 2]
        # No permite espacios, comas, ni formatos sin @ o dominio
        patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(patron_email, email):
            QMessageBox.warning(self.vista, "Formato de Email Inválido", 
                "El correo electrónico no es válido.\nAsegúrese de usar el formato usuario@dominio.com sin espacios ni caracteres especiales.")
            return None

        if id_tipo is None:
            QMessageBox.warning(self.vista, "Error", "Seleccione un tipo de cuenta válido.")
            return None

        try:
            pals = []
            if self.modo == 'crear':
                # Verificar duplicados[cite: 2]
                if self.model.obtener_por_email(email):
                    QMessageBox.warning(self.vista, "Usuario Duplicado", "El email ya se encuentra registrado.")
                    return None
                
                # Forzar contraseña si es Bibliotecario[cite: 2]
                if tipo_str == "Bibliotecario" and not nueva_pwd:
                    QMessageBox.warning(self.vista, "Seguridad Requerida", "Los Bibliotecarios requieren una contraseña para ser creados.")
                    return None
                
                pals = self.model.guardar_bd(nombre, email, id_tipo, "ACTIVA", nueva_pwd, False)
                success_msg = f"Usuario '{nombre}' creado correctamente."
            
            else: # Modo Editar
                estado = self.vista.combo_estado_cuenta.currentText()
                if estado == "SUSPENDIDA":
                    self.model.eliminar_logico(email)
                    success_msg = "Usuario suspendido correctamente."
                elif estado == "ELIMINADA":
                    self.model.eliminar_fisico(email)
                    success_msg = "Usuario eliminado físicamente del sistema."
                else:
                    # Si no hay nueva pwd y no es recovery, se usa la actual validada[cite: 2]
                    pwd_a_usar = nueva_pwd if (nueva_pwd or self.es_upgrade_a_bibliotecario) else pass_actual
                    pals = self.model.guardar_bd(
                        nombre, email, id_tipo, "ACTIVA", pwd_a_usar, True,
                        forzar_palabras=self.es_upgrade_a_bibliotecario
                    )
                    success_msg = "Datos del usuario actualizados con éxito."

            # --- SECUENCIA DE ÉXITO ---
            QMessageBox.information(self.vista, "Operación Exitosa", success_msg)
            
            # Lanzar ventana de recuperación SI existen palabras[cite: 1, 2]
            if pals:
                dialogo_pals = VentanaEmergenciaRecuperacion(pals, self.vista)
                dialogo_pals.exec()

            # Notificar éxito al Main para limpieza[cite: 3]
            self.cargar_datos()
            self.datos_actualizados.emit()
            return True 

        except Exception as e:
            QMessageBox.critical(self.vista, "Error en Base de Datos", f"No se pudo guardar la información: {str(e)}")
            return None