# Models/FormularioSesionesModel.py
import mysql.connector
from mysql.connector import Error
import bcrypt

class PasswordHasher:
    """Clase simple y segura para hashear y verificar contraseñas"""
    @staticmethod
    def verify(contrasena_ingresada: str, hash_guardado: str) -> bool:
        if not contrasena_ingresada or not hash_guardado:
            return False
        try:
            return bcrypt.checkpw(contrasena_ingresada.encode('utf-8'), hash_guardado.encode('utf-8'))
        except:
            return False

class Conexion:
    def __init__(self):
        self.host = 'localhost'
        self.base_datos = 'onlineashes'
        self.usuario = 'root'
        self.contrasena = ''
        self.conexion = None

    def obtener_conexion(self):
        try:
            self.conexion = mysql.connector.connect(
                host=self.host,
                database=self.base_datos,
                user=self.usuario,
                password=self.contrasena
            )
            return self.conexion
        except Error as e:
            print(f"[ERROR DE BASE DE DATOS] Fallo al conectar a 'onlineashes': {e}")
            return None

class FormularioSesionesModel:
    def __init__(self):
        self.conexion_db = Conexion()

    def autenticar(self, email, password):
        """
        Verifica las credenciales en 'onlineashes' y devuelve el estado de 
        éxito junto con la clave maestra de DRM para el sistema de seguridad.
        """
        conn = self.conexion_db.obtener_conexion()
        if not conn:
            return False, None

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT contraseña, clave_drm_maestra 
                FROM usuarios 
                WHERE email = %s AND estado_cuenta = 'ACTIVA'
            """
            cursor.execute(query, (email,))
            usuario = cursor.fetchone()

            if usuario:
                hash_guardado = usuario['contraseña']
                
                # Verificación de la contraseña encriptada
                if PasswordHasher.verify(password, hash_guardado):
                    return True, usuario['clave_drm_maestra']
            
            return False, None

        except Error as e:
            print(f"[ERROR DE AUTENTICACIÓN] {e}")
            return False, None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()