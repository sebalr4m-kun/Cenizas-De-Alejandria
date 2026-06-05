import random
from Modulos.Config import Conexion
from Modulos.Security.PasswordHasher import PasswordHasher

class UsuarioModel:
    def __init__(self):
        self.bd = Conexion().obtener_conexion()

    def obtener_todos(self):
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        try:
            consulta = """
                SELECT u.nombre AS Nombre, u.email AS Email, 
                       p.nombre AS 'Tipo Cuenta', u.estado_cuenta AS Estado
                FROM usuarios u 
                JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                WHERE u.estado_cuenta != 'ELIMINADA'
            """
            cursor.execute(consulta)
            return cursor.fetchall()
        finally:
            cursor.close()

    def obtener_por_email(self, email):
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def _obtener_tipos_usuario_bd(self):
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        try:
            consulta = "SELECT id_tipo_usuario, nombre FROM param_tipos_usuario WHERE estado = 'ACTIVO'"
            cursor.execute(consulta)
            return cursor.fetchall()
        finally:
            cursor.close()

    def es_tipo_admitido(self, id_tipo):
        """
        Verifica dinámicamente si un id_tipo_usuario pertenece a los tipos ADMItidos.
        Útil para que el Controlador gestione las alertas visuales y requerimientos de contraseña.
        """
        self.bd.commit()
        cursor = self.bd.cursor()
        try:
            cursor.execute("SELECT admitido FROM param_tipos_usuario WHERE id_tipo_usuario = %s", (id_tipo,))
            res = cursor.fetchone()
            return bool(res[0]) if res else False
        finally:
            cursor.close()

    def guardar_bd(self, nombre, email, id_tipo, estado, contrasena, es_actualizacion, forzar_palabras=False):
        """Guarda o actualiza registros con hashing dinámico y gestión de llaves maestras basada en admisión."""
        cursor = self.bd.cursor()
        palabras_recuperacion = []
        try:
            hashed = PasswordHasher.hash(contrasena) if contrasena else None

            cursor.execute("SELECT admitido FROM param_tipos_usuario WHERE id_tipo_usuario = %s", (id_tipo,))
            res_admitido = cursor.fetchone()
            es_admitido = bool(res_admitido[0]) if res_admitido else False

            if es_actualizacion:
                consulta = "UPDATE usuarios SET nombre=%s, id_tipo_usuario=%s, estado_cuenta=%s"
                params = [nombre, id_tipo, estado]
                if hashed:
                    consulta += ", contraseña=%s"
                    params.append(hashed)
                consulta += " WHERE email=%s"
                params.append(email)
                cursor.execute(consulta, tuple(params))

                cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
                res_id = cursor.fetchone()
                target_id = res_id[0] if res_id else None
            else:
                cursor.execute("""
                    INSERT INTO usuarios (nombre, email, id_tipo_usuario, estado_cuenta, contraseña)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nombre, email, id_tipo, estado, hashed or ''))
                target_id = cursor.lastrowid

            if es_admitido and target_id and (not es_actualizacion or forzar_palabras):
                indices_num = [random.randint(1, 999) for _ in range(12)]
                indices_txt = ", ".join(map(str, indices_num))
                for idx in indices_num:
                    cursor.execute("SELECT palabra FROM param_diccionario_seguridad WHERE id_palabra = %s", (idx,))
                    res = cursor.fetchone()
                    palabras_recuperacion.append(res[0] if res else f"Error-ID-{idx}")

                cursor.execute("DELETE FROM seguridad_recuperacion WHERE id_usuario = %s", (target_id,))
                cursor.execute("INSERT INTO seguridad_recuperacion (id_usuario, indices_palabras) VALUES (%s, %s)", 
                              (target_id, indices_txt))

            self.bd.commit()
            return palabras_recuperacion
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_logico(self, email):
        cursor = self.bd.cursor()
        try:
            cursor.execute("UPDATE usuarios SET estado_cuenta = 'SUSPENDIDA' WHERE email = %s", (email,))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def eliminar_fisico(self, email):
        cursor = self.bd.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE email = %s", (email,))
            self.bd.commit()
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()