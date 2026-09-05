import os
from PySide6.QtCore import QObject
from Modulos.Config import Conexion

class AuditoriaModel:
    """Modelo dedicado exclusivamente a la persistencia de datos en la tabla auditorias."""
    def __init__(self):
        self.conexion_obj = Conexion()
        self.bd = self.conexion_obj.obtener_conexion()

    def registrar(self, id_usuario, id_accion, modulo, elemento):
        cursor = self.bd.cursor()
        try:
            consulta = """
                INSERT INTO auditorias (id_usuario, id_accion, modulo, elemento)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(consulta, (id_usuario, id_accion, modulo, elemento))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            print(f"Falla crítica en el sistema de Auditoría: {e}")
        finally:
            cursor.close()

class ControladorAuditoria(QObject):
    """
    Controlador Singleton omnisciente. 
    Mantiene en memoria el usuario actual y expone métodos para auditar operaciones globales.
    """
    _instancia = None

    def __new__(cls, *args, **kwargs):
        if not cls._instancia:
            cls._instancia = super(ControladorAuditoria, cls).__new__(cls)
            cls._instancia.model = AuditoriaModel()
            cls._instancia.id_usuario_actual = None
            cls._instancia.nombre_usuario_actual = "Desconocido"
        return cls._instancia

    def vincular_sesion(self, pasaporte):
        """
        Extrae y retiene el id_usuario validado desde InicioSesionController.
        Debe llamarse inmediatamente después de un login exitoso.
        """
        if pasaporte:
            # Soporta el ID 0 asignado por el generador omnipotente del modo rescate
            self.id_usuario_actual = pasaporte.get('id_usuario')
            self.nombre_usuario_actual = pasaporte.get('nombre', 'Desconocido')
            self.auditar_sesion(f"Inicio de sesión certificado. Usuario: {self.nombre_usuario_actual}")

    def auditar_sesion(self, elemento):
        """id_accion 5: Sesión"""
        self._procesar_auditoria(5, "Seguridad/Login", elemento)

    def auditar_creacion(self, modulo, elemento):
        """id_accion 1: Crear"""
        self._procesar_auditoria(1, modulo, elemento)

    def auditar_modificacion(self, modulo, elemento):
        """id_accion 2: Modificar"""
        self._procesar_auditoria(2, modulo, elemento)

    def auditar_borrado_logico(self, modulo, elemento):
        """id_accion 3: Borrado Lógico"""
        self._procesar_auditoria(3, modulo, elemento)

    def auditar_borrado_fisico(self, modulo, elemento):
        """id_accion 4: Borrado Físico"""
        self._procesar_auditoria(4, modulo, elemento)

    def auditar_accion(self, id_accion, modulo, elemento):
        """Método unificador para compatibilidad directa con las llamadas de los demás módulos."""
        self._procesar_auditoria(id_accion, modulo, elemento)

    def _procesar_auditoria(self, id_accion, modulo, elemento):
        id_usr = self.id_usuario_actual
        
        # Convertir el ID 0 del modo rescate a None para evitar el error de clave foránea
        if id_usr == 0:
            id_usr = None
            
        # Concatenar el nombre de usuario si no está ya presente (evita duplicados en el login)
        if getattr(self, 'nombre_usuario_actual', None) and "Usuario:" not in elemento:
            elemento = f"{elemento} - Usuario: {self.nombre_usuario_actual}"
            
        self.model.registrar(id_usr, id_accion, modulo, elemento)

# Instancia global lista para ser importada en cualquier archivo sin perder el contexto
auditoria_global = ControladorAuditoria()