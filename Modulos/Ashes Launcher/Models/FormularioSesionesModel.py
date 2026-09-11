# Models/FormularioSesionesModel.py
import mysql.connector
from mysql.connector import Error

class FormularioSesionesModel:
    def __init__(self, host='localhost', database='onlineashes', user='root', password=''):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def _conectar(self):
        """Establece y retorna la conexión a la base de datos."""
        try:
            conexion = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            return conexion
        except Error as e:
            print(f"Error conectando a la base de datos {self.database}: {e}")
            return None

    def autenticar(self, email, password_ingresada):
        """
        Verifica las credenciales del usuario en la tabla 'usuarios'.
        Retorna un diccionario con el estado del login y los datos requeridos por la vista.
        """
        conexion = self._conectar()
        if not conexion:
            return {"exito": False, "mensaje": "No se pudo conectar al servidor de base de datos."}

        try:
            cursor = conexion.cursor(dictionary=True)
            # Consulta adaptada a los campos de la tabla 'usuarios'
            query = """
                SELECT 
                    id_usuario, 
                    nombre, 
                    email, 
                    clave_drm_maestra, 
                    estado_cuenta, 
                    DATE_FORMAT(fecha_registro, '%d/%m/%Y') AS fecha_registro 
                FROM usuarios 
                WHERE email = %s AND contraseña = %s
            """
            # NOTA: En un entorno de producción, la contraseña debería estar hasheada.
            # Aquí la comparamos de forma directa según la estructura actual de la BD.
            cursor.execute(query, (email, password_ingresada))
            usuario = cursor.fetchone()

            if usuario:
                if usuario['estado_cuenta'] == 'ACTIVA':
                    return {
                        "exito": True,
                        "datos": {
                            "id_usuario": usuario["id_usuario"],
                            "nombre": usuario["nombre"],
                            "email": usuario["email"],
                            "fecha_registro": usuario["fecha_registro"],
                            "clave_drm_maestra": usuario["clave_drm_maestra"]
                        }
                    }
                else:
                    return {"exito": False, "mensaje": "La cuenta se encuentra suspendida o inactiva."}
            else:
                return {"exito": False, "mensaje": "Correo electrónico o contraseña incorrectos."}

        except Error as e:
            print(f"Error ejecutando consulta de autenticación: {e}")
            return {"exito": False, "mensaje": "Error interno al consultar la base de datos."}
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()

    def eliminar_cuenta(self, email):
        """
        Elimina de manera permanente la cuenta del usuario de la base de datos.
        Gracias al 'ON DELETE CASCADE' en la BD, las licencias y recuperaciones asociadas se borrarán.
        """
        conexion = self._conectar()
        if not conexion:
            return False

        try:
            cursor = conexion.cursor()
            query = "DELETE FROM usuarios WHERE email = %s"
            cursor.execute(query, (email,))
            conexion.commit()
            
            # Retorna True si al menos una fila fue afectada
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al eliminar la cuenta: {e}")
            return False
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()