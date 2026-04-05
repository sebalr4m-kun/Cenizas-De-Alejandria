from Modulos.Config import Conexion

class LoginModel:
    def __init__(self):
        self.conexion = Conexion()

    def verificar_credenciales(self, email, contrasena):
        bd = self.conexion.obtener_conexion()
        if not bd:
            return None
            
        cursor = bd.cursor(dictionary=True)
        try:
            consulta = """
                SELECT u.nombre, p.nombre AS rol, u.contraseña 
                FROM usuarios u
                JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                WHERE u.email = %s 
                  AND u.estado_cuenta = 'ACTIVA'
            """
            cursor.execute(consulta, (email,))
            usuario = cursor.fetchone()
            
            if usuario and usuario['contraseña']:
                from Modulos.Security.PasswordHasher import PasswordHasher
                if PasswordHasher.verify(contrasena, usuario['contraseña']):
                    return usuario
            return None
        except Exception as e:
            print(f"Error en LoginModel: {e}")
            return None
        
    def hay_bibliotecario_activo(self):
        """Devuelve True si existe al menos un Bibliotecario ACTIVO"""
        bd = self.conexion.obtener_conexion()
        if not bd:
            return False
            
        cursor = bd.cursor(dictionary=True)
        try:
            consulta = """
                SELECT COUNT(*) as cantidad 
                FROM usuarios u
                JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                WHERE p.nombre = 'Bibliotecario' 
                  AND u.estado_cuenta = 'ACTIVA'
            """
            cursor.execute(consulta)
            resultado = cursor.fetchone()
            return resultado['cantidad'] > 0 if resultado else False
        except Exception:
            return False
        finally:
            cursor.close()