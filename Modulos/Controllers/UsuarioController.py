import re
import json
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QTableWidgetItem, QMessageBox

from Modulos.Models.UsuarioModel import UsuarioModel
from Modulos.Security.PasswordHasher import PasswordHasher
from Modulos.AccountValidator import ValidadorCuenta

class ControladorUsuario(QObject):
    datos_actualizados = Signal()
    solicitar_notificacion = Signal(str, str, str, object)

    def __init__(self):
        super().__init__()
        from Modulos.Views.UsuarioViews import VistaUsuario
        self.model = UsuarioModel()
        self.vista = VistaUsuario()
        
        self.vista.parent_controller = self
        
        self.modo = 'crear'
        self.pass_actual_bd = ""
        
        self.es_upgrade_a_admitido = False
        self._backup_usuario = None
        self.conectar_senales()

    def conectar_senales(self):
        v = self.vista
        self.solicitar_notificacion.connect(v.mostrar_notificacion)
        
        # Corrección obligatoria: Reconexión de botones de cambio de modo usando lambdas seguras
        v.btn_modo_crear.clicked.connect(lambda: self.establecer_modo_crear(inicial=False))
        v.btn_modo_editar.clicked.connect(self.establecer_modo_editar)
        v.btn_guardar.clicked.connect(self.manejar_guardado)
        v.entrada_busqueda.textChanged.connect(self.filtrar_tabla)
        v.entrada_email.editingFinished.connect(self.al_terminar_edicion_email)
        v.entrada_pass_actual.textChanged.connect(self.verificar_pass_tiempo_real)

    # =========================================================================
    # PUENTE DE RETROCOMPATIBILIDAD CON VISTA ACTUAL
    # Evita que UsuarioViews crashee hasta que sea actualizado en el siguiente paso
    # =========================================================================
    @property
    def es_upgrade_a_bibliotecario(self):
        return self.es_upgrade_a_admitido

    @es_upgrade_a_bibliotecario.setter
    def es_upgrade_a_bibliotecario(self, valor):
        self.es_upgrade_a_admitido = valor

    def obtener_widget_vista(self):
        self.cargar_datos()
        return self.vista.widget_listado

    def obtener_widget_formulario(self, ctrl_param=None):
        self.cargar_combos()
        self.establecer_modo_crear(inicial=True)
        return self.vista.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        self.establecer_modo_crear(inicial=True)
        if hasattr(self.vista, 'widget_contenido_formulario'):
            self.vista.widget_contenido_formulario.hide()

    def cargar_combos(self):
        try:
            # Obtención directa de los flags y permisos de la base de datos
            cursor = self.model.bd.cursor(dictionary=True)
            cursor.execute("SELECT id_tipo_usuario, nombre, admitido FROM param_tipos_usuario WHERE estado = 'ACTIVO'")
            tipos = cursor.fetchall()
            cursor.close()

            self.vista.combo_tipo_cuenta.clear()
            for t in tipos:
                # Estética trascendental: Distintivo visual para cuentas con accesos especiales
                icono = "🛡️ " if t.get('admitido') else "👤 "
                nombre_visual = f"{icono}{t['nombre']}"
                self.vista.combo_tipo_cuenta.addItem(nombre_visual, t['id_tipo_usuario'])
        except Exception as e:
            self.solicitar_notificacion.emit('crit', "Error de Carga", f"Fallo al obtener tipos: {e}", None)

    def _obtener_estados_admision(self):
        """Helper robusto guiado puramente por los IDs de la base de datos."""
        id_actual = self.vista.combo_tipo_cuenta.currentData()
        es_admitido = self.model.es_tipo_admitido(id_actual) if id_actual is not None else False
        
        id_orig = getattr(self.vista, 'id_rol_original', None)
        fue_admitido = self.model.es_tipo_admitido(id_orig) if id_orig is not None else False
                
        return es_admitido, fue_admitido, id_actual, id_orig

    def establecer_modo_crear(self, inicial=False):
        self.modo = 'crear'
        self.es_upgrade_a_admitido = False
        self._backup_usuario = None
        self.vista.btn_modo_crear.setChecked(True)
        self.vista.btn_modo_editar.setChecked(False)
        self.vista.etiqueta_estado.hide()
        self.vista.combo_estado_cuenta.hide()
        self.limpiar_formulario()
        if not inicial and hasattr(self.vista, 'widget_contenido_formulario'):
            self.vista.widget_contenido_formulario.show()

    def establecer_modo_editar(self):
        self.modo = 'editar'
        self.es_upgrade_a_admitido = False
        self._backup_usuario = None
        self.vista.btn_modo_crear.setChecked(False)
        self.vista.btn_modo_editar.setChecked(True)
        self.vista.etiqueta_estado.show()
        self.vista.combo_estado_cuenta.show()
        self.limpiar_formulario()
        if hasattr(self.vista, 'widget_contenido_formulario'):
            self.vista.widget_contenido_formulario.show()

    def limpiar_formulario(self):
        self.vista.entrada_nombre.clear()
        self.vista.entrada_email.clear()
        self.vista.entrada_pass_actual.clear()
        self.vista.entrada_pass_nueva.clear()
        
        if hasattr(self.vista, 'entrada_pass_confirmar'):
            self.vista.entrada_pass_confirmar.clear()
            
        self.vista.btn_guardar.setEnabled(True)
        self.vista.btn_guardar.setStyleSheet("")
        self.vista.entrada_pass_actual.setStyleSheet("")
        self.vista.entrada_pass_actual.setEnabled(True)
        
        if self.vista.combo_tipo_cuenta.count() > 0:
            self.vista.combo_tipo_cuenta.setCurrentIndex(0)
        self.vista.combo_estado_cuenta.setCurrentIndex(0)
        
        self.pass_actual_bd = ""
        self.es_upgrade_a_admitido = False
        self._backup_usuario = None
        self.vista._recovery_exitoso = False
        self.vista.ajustar_visibilidad_campos_seguridad()

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
        if self.modo != 'editar':
            self.vista.btn_guardar.setEnabled(True)
            self.vista.entrada_pass_actual.setStyleSheet("")
            return
            
        es_admitido, fue_admitido, _, _ = self._obtener_estados_admision()
        recovery_exitoso = getattr(self.vista, '_recovery_exitoso', False)
        requiere_validacion = False
        
        if fue_admitido and not recovery_exitoso:
            requiere_validacion = True
            
        if not requiere_validacion:
            self.vista.btn_guardar.setEnabled(True)
            self.vista.entrada_pass_actual.setStyleSheet("")
            return
            
        if PasswordHasher.verify(texto, self.pass_actual_bd):
            self.vista.btn_guardar.setEnabled(True)
            self.vista.entrada_pass_actual.setStyleSheet("border: 2px solid #2ecc71;")
        else:
            self.vista.btn_guardar.setEnabled(False)
            self.vista.entrada_pass_actual.setStyleSheet("border: 2px solid #e74c3c;" if texto else "")

    def al_terminar_edicion_email(self):
        if self.modo != 'editar': return
        email = self.vista.entrada_email.text().strip()
        if not email: return
        
        usuario = self.model.obtener_por_email(email)
        if usuario:
            self.vista.entrada_nombre.setText(usuario['nombre'])
            self.pass_actual_bd = usuario.get('contraseña', '')
            
            # Búsqueda infalible mediante el ID (Data), ignorando por completo el texto y sus símbolos
            idx = self.vista.combo_tipo_cuenta.findData(usuario.get('id_tipo_usuario'))
            if idx >= 0:
                self.vista.id_rol_original = usuario.get('id_tipo_usuario')
                self.vista.combo_tipo_cuenta.setCurrentIndex(idx)
                
            self.vista._recovery_exitoso = False
            self.vista.combo_estado_cuenta.setCurrentText(usuario.get('estado_cuenta', 'ACTIVA'))
            self.vista.entrada_pass_actual.clear()
            self.es_upgrade_a_admitido = False
            self.vista.ajustar_visibilidad_campos_seguridad()
            self.verificar_pass_tiempo_real(self.vista.entrada_pass_actual.text())
        else:
            self.solicitar_notificacion.emit('warn', "No encontrado", "Usuario no registrado.", None)

    def validar_identidad_finalizada(self, exito, email=None):
        if exito:
            es_admitido, fue_admitido, _, _ = self._obtener_estados_admision()
            
            if fue_admitido and not es_admitido:
                self.vista._recovery_exitoso = True
                self.vista.ajustar_visibilidad_campos_seguridad()
                self.vista.btn_guardar.setEnabled(True)
            else:
                if email:
                    self.vista.entrada_email.setText(email)
                    self.al_terminar_edicion_email()
                self.es_upgrade_a_admitido = True
                self.vista.ajustar_visibilidad_campos_seguridad()
                self.vista.btn_guardar.setEnabled(True)
                self.solicitar_notificacion.emit('success', "Identidad Confirmada", "Acceso de edición concedido.", None)

    def manejar_guardado(self):
        nombre = self.vista.entrada_nombre.text().strip()
        email = self.vista.entrada_email.text().strip()
        id_tipo = self.vista.combo_tipo_cuenta.currentData()
        nueva_pwd = self.vista.entrada_pass_nueva.text().strip()
        pass_actual = self.vista.entrada_pass_actual.text().strip()

        if not nombre or not email:
            self.solicitar_notificacion.emit('warn', "Datos Faltantes", "Nombre y Email son campos obligatorios.", None)
            return False

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            self.solicitar_notificacion.emit('warn', "Formato Inválido", "El correo ingresado no es válido.", None)
            return False

        if hasattr(self.vista, 'verificar_coincidencia_contrasenas'):
            if not self.vista.verificar_coincidencia_contrasenas():
                return False

        es_admitido, fue_admitido, id_actual, id_orig = self._obtener_estados_admision()

        # ALERTA DINÁMICA DE SEGURIDAD PARA CAMBIO DE ROLES ADMITIDOS
        if self.modo == 'editar' and fue_admitido and id_actual != id_orig:
            cursor = self.model.bd.cursor(dictionary=True)
            cursor.execute("SELECT admitido, permisos FROM param_tipos_usuario WHERE id_tipo_usuario = %s", (id_actual,))
            target_info = cursor.fetchone()
            cursor.close()
            
            permisos_json_str = target_info['permisos'] if target_info and target_info.get('permisos') else "{}"
            
            if not es_admitido:
                resumen_permisos = "⚠️ NO PUEDES VOLVER A INICIAR SESIÓN.\nTu cuenta perderá todo acceso al sistema."
            else:
                try:
                    perms = json.loads(permisos_json_str)
                except Exception:
                    perms = {}
                
                resumen_permisos = "✔️ PUEDES VOLVER A INICIAR SESIÓN.\nEstos serán tus nuevos privilegios:\n"
                for modulo, acciones in perms.items():
                    acts_activas = [k.capitalize() for k, v in acciones.items() if v]
                    if acts_activas:
                        resumen_permisos += f"  • {modulo}: {', '.join(acts_activas)}\n"
                    else:
                        resumen_permisos += f"  • {modulo}: Sin acceso\n"

            mensaje_alerta = (
                f"La cuenta está por ser cambiada a un tipo de usuario con accesos distintos:\n\n"
                f"{resumen_permisos}\n\n"
                "Ten en cuenta que si pierdes acceso a la vista y edición del apartado Usuarios no podrás recuperar tus accesos sin la ayuda de otro usuario con cuenta ADMItida y permisos de administración y vista.\n\n"
                "En caso que sea el único usuario con contraseña, la próxima persona que abra el programa tendrá todos los privilegios hasta que haya una nueva cuenta de tipo ADMItida.\n\n"
                "¿Desea continuar?"
            )
            
            respuesta = QMessageBox.question(None, "Advertencia Crítica de Privilegios", mensaje_alerta, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if respuesta == QMessageBox.No:
                return False

        try:
            pals = []
            hay_senal = ValidadorCuenta.verificar_conexion() if hasattr(ValidadorCuenta, 'verificar_conexion') else False

            if self.modo == 'crear':
                if self.model.obtener_por_email(email):
                    self.solicitar_notificacion.emit('warn', "Conflicto", "Este email ya se encuentra registrado.", None)
                    return False
                
                if es_admitido and not nueva_pwd:
                    self.solicitar_notificacion.emit('warn', "Seguridad", "Las cuentas ADMItidas requieren una contraseña inicial.", None)
                    return False

                pals = self.model.guardar_bd(nombre, email, id_tipo, "ACTIVA", nueva_pwd, False, False)
                
                if es_admitido and hay_senal:
                    self.solicitar_notificacion.emit('validador_cuenta', "Validación Requerida", email, pals)
                    return True

                msg = f"Usuario '{nombre}' creado en modo offline."
            
            else:
                estado = self.vista.combo_estado_cuenta.currentText()
                if estado == "SUSPENDIDA":
                    self.model.eliminar_logico(email)
                    msg = "La cuenta ha sido suspendida."
                elif estado == "ELIMINADA":
                    self.model.eliminar_physico(email) if hasattr(self.model, 'eliminar_physico') else self.model.eliminar_fisico(email)
                    msg = "Registro eliminado permanentemente."
                else:
                    recovery_exitoso = getattr(self.vista, '_recovery_exitoso', False)
                    
                    if fue_admitido and not recovery_exitoso:
                        if not PasswordHasher.verify(pass_actual, self.pass_actual_bd):
                            self.solicitar_notificacion.emit('warn', "Seguridad", "La contraseña actual es incorrecta. No se pueden guardar los cambios.", None)
                            return False

                    if self.es_upgrade_a_admitido:
                        self._backup_usuario = self.model.obtener_por_email(email)

                    pwd_a_usar = nueva_pwd if (nueva_pwd or self.es_upgrade_a_admitido) else pass_actual
                    pals = self.model.guardar_bd(nombre, email, id_tipo, "ACTIVA", pwd_a_usar, True, self.es_upgrade_a_admitido)
                    msg = "Información de perfil actualizada."

                    if self.es_upgrade_a_admitido and hay_senal:
                        self.solicitar_notificacion.emit('validador_cuenta', "Validación Requerida", email, pals)
                        return True

            self.finalizar_operacion(msg, pals)
            return True

        except Exception as e:
            self.solicitar_notificacion.emit('crit', "Error Crítico", str(e), None)
            return False

    def finalizar_operacion(self, mensaje, palabras=None):
        if palabras:
            try:
                self.solicitar_notificacion.emit('emergencia', "Credenciales de Recuperación", "", palabras)
            except Exception as e:
                pals_formateadas = ", ".join(palabras) if isinstance(palabras, list) else str(palabras)
                mensaje += f"\n\n⚠️ [RESPALDO CRÍTICO - PALABRAS MAESTRAS]:\n{pals_formateadas}"
            
        self.solicitar_notificacion.emit('success', "Operación Exitosa", mensaje, None)
        self.cargar_datos()
        self.datos_actualizados.emit()
        self.limpiar_formulario()

    def abortar_creacion(self, email):
        if self.modo == 'editar' and self.es_upgrade_a_admitido and self._backup_usuario:
            old = self._backup_usuario
            cursor = self.model.bd.cursor()
            try:
                cursor.execute(
                    "UPDATE usuarios SET nombre=%s, id_tipo_usuario=%s, estado_cuenta=%s, contraseña=%s WHERE email=%s",
                    (old['nombre'], old['id_tipo_usuario'], old['estado_cuenta'], old['contraseña'], email)
                )
                self.model.bd.commit()
            except Exception as e:
                self.model.bd.rollback()
            finally:
                cursor.close()
            
            self.solicitar_notificacion.emit('crit', "Validación Fallida", "El ascenso a cuenta ADMItida fue abortado por seguridad. Se restauraron los privilegios anteriores.", None)
        else:
            self.model.eliminar_fisico(email)
            self.solicitar_notificacion.emit('crit', "Validación Fallida", "El proceso de creación fue abortado por seguridad.", None)
        
        self.limpiar_formulario()