import re
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QTableWidgetItem

from Modulos.Models.UsuarioModel import UsuarioModel
from Modulos.Security.PasswordHasher import PasswordHasher
from Modulos.AccountValidator import ValidadorCuenta

class ControladorUsuario(QObject):
    # Señal para actualizar la tabla en el Main
    datos_actualizados = Signal()
    # Señal Maestra para notificaciones: (tipo, titulo, mensaje, datos_extra)
    # tipos: 'info', 'warn', 'crit', 'success', 'validador', 'emergencia'
    solicitar_notificacion = Signal(str, str, str, object)

    def __init__(self):
        super().__init__()
        # Importación diferida para evitar ciclos
        from Modulos.Views.UsuarioViews import VistaUsuario
        self.model = UsuarioModel()
        self.vista = VistaUsuario()
        
        # VÍNCULO DE CONTROL: Permite que la vista regrese datos al controlador
        self.vista.parent_controller = self
        
        self.modo = 'crear'
        self.pass_actual_bd = ""
        self.es_upgrade_a_bibliotecario = False
        self.conectar_senales()

    def conectar_senales(self):
        v = self.vista
        
        # --- CONEXIÓN CRÍTICA FALTANTE ---
        # Conecta la señal maestra del controlador al manejador visual de la vista
        self.solicitar_notificacion.connect(v.mostrar_notificacion)
        
        # Conexiones de botones y eventos
        v.btn_modo_crear.clicked.connect(self.establecer_modo_crear)
        v.btn_modo_editar.clicked.connect(self.establecer_modo_editar)
        v.btn_guardar.clicked.connect(self.manejar_guardado)
        v.btn_recuperar_pass.clicked.connect(self.proceso_recuperacion_emergencia)
        v.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        v.entrada_email.editingFinished.connect(self.al_terminar_edicion_email)
        v.entrada_pass_actual.textChanged.connect(self.verificar_pass_tiempo_real)
        v.combo_tipo_cuenta.currentTextChanged.connect(self.alternar_contrasena)

    # ==================== MÉTODOS DE UI (LÓGICA) ====================
    def obtener_widget_vista(self):
        """Devuelve el widget de listado ya existente en la vista."""
        return self.vista.widget_listado

    def obtener_widget_formulario(self, ctrl_param=None):
        """Prepara y devuelve el widget de formulario existente."""
        self.cargar_combos()
        self.establecer_modo_crear(inicial=True)
        return self.vista.widget_formulario

    def reiniciar_visibilidad_formulario(self):
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
            self.solicitar_notificacion.emit('crit', "Error de Carga", f"Fallo al obtener tipos: {e}", None)

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
            self.vista.entrada_pass_actual.setStyleSheet("border: 2px solid green;")
        else:
            self.vista.btn_guardar.setEnabled(False)
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
            if idx >= 0: self.vista.combo_tipo_cuenta.setCurrentIndex(idx)
            self.vista.combo_estado_cuenta.setCurrentText(usuario.get('estado_cuenta', 'ACTIVA'))
            self.vista.entrada_pass_actual.clear()
            self.es_upgrade_a_bibliotecario = False
            self.restaurar_visibilidad_recovery()
        else:
            self.solicitar_notificacion.emit('warn', "No encontrado", "Usuario no registrado.", None)

    def proceso_recuperacion_emergencia(self):
        self.solicitar_notificacion.emit('recovery_trigger', "", "", None)

    def validar_identidad_finalizada(self, exito, email=None):
        if exito:
            if email:
                self.vista.entrada_email.setText(email)
                self.al_terminar_edicion_email()
            self.es_upgrade_a_bibliotecario = True
            self.restaurar_visibilidad_recovery()
            self.vista.btn_guardar.setEnabled(True)
            self.solicitar_notificacion.emit('success', "Éxito", "Identidad confirmada.", None)

    # ==================== LÓGICA DE GUARDADO ====================
    def manejar_guardado(self):
        nombre = self.vista.entrada_nombre.text().strip()
        email = self.vista.entrada_email.text().strip()
        id_tipo = self.vista.combo_tipo_cuenta.currentData()
        tipo_str = self.vista.combo_tipo_cuenta.currentText()
        nueva_pwd = self.vista.entrada_pass_nueva.text().strip()
        pass_actual = self.vista.entrada_pass_actual.text().strip()

        # Validaciones básicas que ahora SÍ dispararán alertas
        if not nombre or not email:
            self.solicitar_notificacion.emit('warn', "Campos Incompletos", "Nombre y Email obligatorios.", None)
            return

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            self.solicitar_notificacion.emit('warn', "Email Inválido", "Formato de correo no reconocido.", None)
            return

        try:
            pals = []
            if self.modo == 'crear':
                if self.model.obtener_por_email(email):
                    self.solicitar_notificacion.emit('warn', "Duplicado", "El email ya existe.", None)
                    return
                
                if tipo_str == "Bibliotecario" and not nueva_pwd:
                    self.solicitar_notificacion.emit('warn', "Seguridad", "Se requiere contraseña para Bibliotecarios.", None)
                    return

                hay_senal = ValidadorCuenta.verificar_conexion()
                pals = self.model.guardar_bd(nombre, email, id_tipo, "ACTIVA", nueva_pwd, False)
                
                if tipo_str == "Bibliotecario" and hay_senal:
                    # Lanza el diálogo de validación en la vista
                    self.solicitar_notificacion.emit('validador_cuenta', "Validación Requerida", email, pals)
                    return

                msg = f"Usuario '{nombre}' creado." + (" (Auto-validado)" if not hay_senal else "")
            
            else: # Modo Editar
                estado = self.vista.combo_estado_cuenta.currentText()
                if estado == "SUSPENDIDA":
                    self.model.eliminar_logico(email)
                    msg = "Usuario suspendido."
                elif estado == "ELIMINADA":
                    self.model.eliminar_fisico(email)
                    msg = "Usuario eliminado físicamente."
                else:
                    pwd_a_usar = nueva_pwd if (nueva_pwd or self.es_upgrade_a_bibliotecario) else pass_actual
                    pals = self.model.guardar_bd(nombre, email, id_tipo, "ACTIVA", pwd_a_usar, True, self.es_upgrade_a_bibliotecario)
                    msg = "Datos actualizados."

            self.finalizar_operacion(msg, pals)

        except Exception as e:
            self.solicitar_notificacion.emit('crit', "Error BD", str(e), None)

    def finalizar_operacion(self, mensaje, palabras=None):
        self.solicitar_notificacion.emit('success', "Operación Exitosa", mensaje, None)
        if palabras:
            self.solicitar_notificacion.emit('emergencia', "Palabras Maestras", "", palabras)
        
        self.cargar_datos()
        self.datos_actualizados.emit()
        self.limpiar_formulario()

    def abortar_creacion(self, email):
        self.model.eliminar_fisico(email)
        self.solicitar_notificacion.emit('crit', "Abortado", "Cuenta no validada. Se ha eliminado el registro.", None)