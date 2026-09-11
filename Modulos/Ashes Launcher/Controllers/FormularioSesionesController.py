# Controllers/FormularioSesionesController.py
from PySide6.QtCore import QObject, Signal
from Views.FormularioSesionesViews import FormularioSesiones
# Importaremos el modelo cuando esté listo:
# from Models.FormularioSesionesModel import FormularioSesionesModel

class FormularioSesionesController(QObject):
    # Señales para notificar al resto del Launcher (ej. ListadoVersionesController)
    sesion_iniciada = Signal(dict) # Transmite datos del usuario y su clave_privada_usuario
    sesion_cerrada = Signal()

    def __init__(self, view: FormularioSesiones, model=None):
        super().__init__()
        self.view = view
        self.model = model # Aquí se inyectará FormularioSesionesModel
        
        # Almacenamiento temporal en la memoria RAM de la sesión activa
        self.usuario_actual = None
        self.clave_privada_usuario = None # Hash DRM para verificar ejecutables
        
        # Conectar eventos de la Vista
        self._conectar_senales_view()

    def _conectar_senales_view(self):
        # Conexión del botón de login
        self.view.btn_login.clicked.connect(self.procesar_inicio_sesion)
        
        # Conexión de botones de la vista activa
        self.view.btn_logout.clicked.connect(self.procesar_cierre_sesion)
        self.view.btn_borrar.clicked.connect(self.procesar_borrado_cuenta)

    def procesar_inicio_sesion(self):
        email = self.view.input_email.text().strip()
        password = self.view.input_pass.text().strip()
        
        if not email or not password:
            # Aquí podrías mostrar un aviso visual en la interfaz si lo deseas
            return
            
        # --- SIMULACIÓN DE VALIDACIÓN CON EL MODELO ---
        # Cuando FormularioSesionesModel esté conectado, la llamada será:
        # resultado = self.model.autenticar(email, password)
        
        # Estructura de respuesta esperada desde el Modelo:
        exito = True # Cambiar según respuesta del Modelo
        
        if exito:
            self.usuario_actual = email
            # El modelo debe generar/retornar el hash único de la cuenta
            self.clave_privada_usuario = f"HASH_DRM_KEY_{email.upper()}_9921"
            
            # Actualizar la interfaz gráfica
            self.view.cambiar_a_sesion_activa(self.usuario_actual)
            
            # Emitir señal global para que el ListadoVersionesController sepa qué claves filtrar
            self.sesion_iniciada.emit({
                "email": self.usuario_actual,
                "clave_privada": self.clave_privada_usuario
            })
        else:
            self.view.input_pass.clear()

    def procesar_cierre_sesion(self):
        # Limpieza estricta de seguridad en memoria RAM
        self.usuario_actual = None
        self.clave_privada_usuario = None
        
        # Regresar la vista al estado de login
        self.view.cambiar_a_login()
        
        # Notificar al Launcher que la sesión terminó para ocultar versiones no autorizadas
        self.sesion_cerrada.emit()

    def procesar_borrado_cuenta(self):
        if self.usuario_actual and self.model:
            # self.model.eliminar_cuenta(self.usuario_actual)
            self.procesar_cierre_sesion()

    def obtener_clave_activa(self):
        """Método de consulta para verificar si hay un usuario autenticado y su clave DRM."""
        return self.clave_privada_usuario