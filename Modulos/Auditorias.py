import os
from PySide6.QtCore import QObject
from Modulos.Config import Conexion

class AuditoriaModel:
    """Modelo dedicado exclusivamente a la persistencia de datos en la tabla auditorias."""
    def __init__(self):
        self.conexion_obj = Conexion()

    def registrar(self, id_usuario, id_accion, modulo, elemento):
        """Registra el evento garantizando siempre una conexión activa a la BD."""
        try:
            bd = self.conexion_obj.obtener_conexion()
            if not bd:
                print("[ERROR AUDITORÍA] No se pudo obtener conexión con la base de datos.")
                return

            bd.commit() # Sincronización previa limpia
            cursor = bd.cursor()
            consulta = """
                INSERT INTO auditorias (id_usuario, id_accion, modulo, elemento)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(consulta, (id_usuario, id_accion, modulo, elemento))
            bd.commit()
            cursor.close()
        except Exception as e:
            print(f"Falla crítica en el sistema de Auditoría: {e}")

    def eliminar_rastro(self, modulo, subcadena_elemento):
        """Elimina silenciosamente el último registro de auditoría de una operación abortada."""
        try:
            bd = self.conexion_obj.obtener_conexion()
            if not bd:
                return
            
            bd.commit()
            cursor = bd.cursor()
            
            # Buscar el último registro específico para evitar borrar historiales legítimos pasados
            consulta_sel = "SELECT id_auditoria FROM auditorias WHERE modulo = %s AND elemento LIKE %s ORDER BY id_auditoria DESC LIMIT 1"
            cursor.execute(consulta_sel, (modulo, f"%{subcadena_elemento}%"))
            resultado = cursor.fetchone()
            
            if resultado:
                id_auditoria = resultado[0]
                cursor.execute("DELETE FROM auditorias WHERE id_auditoria = %s", (id_auditoria,))
                bd.commit()
                
            cursor.close()
        except Exception as e:
            print(f"Falla al eliminar rastro de auditoría abortada: {e}")


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
        
    def eliminar_rastro_operacion(self, modulo, elemento):
        """Llama al modelo para borrar la huella de una acción cancelada o fallida."""
        self.model.eliminar_rastro(modulo, elemento)

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