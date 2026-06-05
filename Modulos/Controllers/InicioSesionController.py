from PySide6.QtWidgets import QMessageBox
from Modulos.Models.InicioSesionModel import LoginModel
from Modulos.Views.InicioSesionViews import VistaLogin
from Modulos.PasswordRecover import ValidadorRecuperacion

class ControladorLogin:
    def __init__(self):
        # Asegúrate de que el archivo del modelo ahora se llame InicioSesionModel.py (sin la 's' final)
        self.model = LoginModel()
        self.vista = VistaLogin()

        # Pasaporte de Sesión Unificado en lugar de variables sueltas
        self.pasaporte = None
        self.autenticado = False

        # Conectar señales de la vista
        self.vista.botones.accepted.connect(self.intentar_login)
        self.vista.botones.rejected.connect(self.vista.reject)
        self.vista.boton_invitado.clicked.connect(self.aceptar_invitado)
        self.vista.btn_recuperar.clicked.connect(self.ejecutar_recuperacion)

    def _generar_pasaporte_omnipotente(self, nombre="Administrador (Modo Desarrollo)"):
        """Falsifica un pasaporte con privilegios divinos si el sistema está acéfalo o en rescate."""
        return {
            'id_usuario': 0,
            'nombre': nombre,
            'rol': 'admin',
            'admitido': True,
            'permisos': {
                "Usuarios": {"ver": True, "crear": True, "editar": True, "eliminar": True, "borrar": True},
                "Insumos": {"ver": True, "crear": True, "editar": True, "eliminar": True, "borrar": True},
                "Libros": {"ver": True, "crear": True, "editar": True, "eliminar": True, "borrar": True},
                "Prestamos": {"ver": True, "crear": True, "editar": True, "eliminar": True, "borrar": True},
                "Parametros": {"ver": True, "crear": True, "editar": True, "eliminar": True, "borrar": True}
            }
        }

    def _generar_pasaporte_invitado(self):
        """Genera un pasaporte base sin privilegios."""
        return {
            'id_usuario': None,
            'nombre': 'Invitado',
            'rol': 'invitado',
            'admitido': False,
            'permisos': {}
        }

    def ejecutar(self):
        """Muestra el diálogo y devuelve si se autenticó o no"""
        # === Chequeo automático del Dios de la Máquina ANTES de mostrar el login ===
        if not self.model.hay_dios_de_la_maquina_activo():
            QMessageBox.information(
                None, 
                "Modo de Rescate / Configuración", 
                "No se detectaron usuarios ADMItidos con privilegios de gestión (Dios de la Máquina).\n\nSe ha activado el Modo Administrador con acceso total por seguridad."
            )
            # Designación divina por ausencia de reyes
            self.pasaporte = self._generar_pasaporte_omnipotente()
            self.autenticado = True
            return True  # ← Simula que el login fue exitoso y omite la ventana

        # Si hay guardianes válidos en la BD, mostramos el diálogo normal
        return self.vista.exec()

    def intentar_login(self):
        correo = self.vista.entrada_correo.text().strip()
        password = self.vista.entrada_contrasena.text().strip()

        if not correo or not password:
            QMessageBox.warning(self.vista, "Error", "Por favor, complete todos los campos.")
            return

        # El modelo ahora devuelve el diccionario completo
        pasaporte_validado = self.model.verificar_credenciales(correo, password)

        if pasaporte_validado:
            self.pasaporte = pasaporte_validado
            self.autenticado = True
            self.vista.accept()
        else:
            QMessageBox.critical(self.vista, "Fallo de Inicio", "Correo o contraseña incorrectos.")

    def ejecutar_recuperacion(self):
        validador = ValidadorRecuperacion(self.vista)
        if validador.exec():
            # Si alguien usa las llaves maestras, asume el control total para arreglar su cuenta
            self.pasaporte = self._generar_pasaporte_omnipotente(nombre="Recuperado_Por_Llave")
            self.autenticado = True
            self.vista.accept()

    def aceptar_invitado(self):
        self.pasaporte = self._generar_pasaporte_invitado()
        self.autenticado = True
        self.vista.accept()

    def obtener_resultado(self):
        """Devuelve el pasaporte de sesión completo en lugar de solo strings sueltos"""
        return self.pasaporte