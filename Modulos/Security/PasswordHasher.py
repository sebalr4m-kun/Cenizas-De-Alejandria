import bcrypt

class PasswordHasher:
    """Clase simple y segura para hashear y verificar contraseñas"""

    @staticmethod
    def hash(contrasena: str) -> str:
        """Convierte una contraseña en texto plano a hash"""
        if not contrasena:
            return ""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(contrasena.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify(contrasena_ingresada: str, hash_guardado: str) -> bool:
        """Verifica si la contraseña ingresada coincide con el hash"""
        if not contrasena_ingresada or not hash_guardado:
            return False
        try:
            return bcrypt.checkpw(contrasena_ingresada.encode('utf-8'), hash_guardado.encode('utf-8'))
        except:
            return False