import mysql.connector
from mysql.connector import Error

class Conexion:
    def __init__(self):
        self.host = 'localhost'
        self.base_datos = 'bibliotecabd'
        self.usuario = 'root'
        self.contrasena = ''
        self.conexion = None

    def obtener_conexion(self):
        if self.conexion is None or not self.conexion.is_connected():
            try:
                self.conexion = mysql.connector.connect(
                    host=self.host,
                    database=self.base_datos,
                    user=self.usuario,
                    password=self.contrasena
                )
            except Error as e:
                print(f"Error al conectar a MySQL: {e}")
                self.conexion = None
        return self.conexion

    def cerrar_conexion(self):
        if self.conexion is not None and self.conexion.is_connected():
            self.conexion.close()