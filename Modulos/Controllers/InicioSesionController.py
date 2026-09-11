import sys
from PySide6.QtWidgets import QMessageBox
from Modulos.Models.InicioSesionModel import LoginModel
from Modulos.Views.InicioSesionViews import VistaLogin
from Modulos.PasswordRecover import ValidadorRecuperacion

class ControladorLogin:
    def __init__(self):
        self.model = LoginModel()
        self.vista = VistaLogin()

        self.pasaporte = None
        self.autenticado = False

        self.vista.botones.accepted.connect(self.intentar_login)
        self.vista.botones.rejected.connect(self.vista.reject)
        self.vista.btn_recuperar.clicked.connect(self.ejecutar_recuperacion)

    def _generar_pasaporte_omnipotente(self, nombre="Administrador (Modo Desarrollo)"):
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

    def ejecutar(self):
        estado_ddlm = self.model.hay_dios_de_la_maquina_activo()
        
        if estado_ddlm is None:
            QMessageBox.critical(None, "Error de Conexión", "No se detecta conexión a la base de datos. Encienda MySQL e intente nuevamente.")
            return False
            
        # Validación original del Modo de Rescate
        if not estado_ddlm:
            QMessageBox.information(
                None, 
                "Modo de Rescate / Configuración", 
                "No se detectaron usuarios ADMItidos con privilegios de gestión (Dios de la Máquina).\\n\\nSe ha activado el Modo Administrador con acceso total por seguridad."
            )
            self.pasaporte = self._generar_pasaporte_omnipotente()
            self.autenticado = True
            return True

        return self.vista.exec()

    def intentar_login(self):
        correo = self.vista.entrada_correo.text().strip()
        password = self.vista.entrada_contrasena.text().strip()

        if not correo or not password:
            QMessageBox.warning(self.vista, "Error", "Por favor, complete todos los campos.")
            return

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
            # En lugar de asignar privilegios de "Dios de la Máquina", extraemos el pasaporte
            # real del usuario que el validador ya ha certificado mediante las llaves secretas.
            if hasattr(validador, 'pasaporte') and validador.pasaporte:
                self.pasaporte = validador.pasaporte
                self.autenticado = True
                self.vista.accept()
            else:
                QMessageBox.critical(
                    self.vista, 
                    "Error de Integridad", 
                    "Las llaves fueron correctas, pero el validador no expuso el pasaporte de sesión del usuario. Asegúrate de que ValidadorRecuperacion defina 'self.pasaporte' con los permisos reales al tener éxito."
                )

    def obtener_resultado(self):
        return self.pasaporte