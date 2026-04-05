import random
from Modulos.Config import Conexion
from Modulos.Security.PasswordHasher import PasswordHasher

class UsuarioModel:
    def __init__(self):
        self.bd = Conexion().obtener_conexion()

    def obtener_todos(self):
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
            SELECT u.nombre AS Nombre, u.email AS Email, 
                   p.nombre AS 'Tipo Cuenta', u.estado_cuenta AS Estado
            FROM usuarios u 
            JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
            WHERE u.estado_cuenta != 'ELIMINADA'
        """
        cursor.execute(consulta)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado

    def obtener_por_email(self, email):
        cursor = self.bd.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        resultado = cursor.fetchone()
        cursor.close()
        return resultado

    def _obtener_tipos_usuario_bd(self):
        cursor = self.bd.cursor(dictionary=True)
        consulta = "SELECT id_tipo_usuario, nombre FROM param_tipos_usuario WHERE estado = 'ACTIVO'"
        cursor.execute(consulta)
        resultado = cursor.fetchall()
        cursor.close()
        return resultado

    def guardar_bd(self, nombre, email, id_tipo, estado, contrasena, es_actualizacion, forzar_palabras=False):
        """Guarda o actualiza con hasheo. Devuelve palabras solo si es Bibliotecario y corresponde."""
        cursor = self.bd.cursor()
        palabras_recuperacion = []
        try:
            hashed = PasswordHasher.hash(contrasena) if contrasena else None

            # Obtener nombre del tipo
            cursor.execute("SELECT nombre FROM param_tipos_usuario WHERE id_tipo_usuario = %s", (id_tipo,))
            res_tipo = cursor.fetchone()
            nombre_tipo = res_tipo[0] if res_tipo else ""

            if es_actualizacion:
                # UPDATE
                consulta = "UPDATE usuarios SET nombre=%s, id_tipo_usuario=%s, estado_cuenta=%s"
                params = [nombre, id_tipo, estado]
                if hashed:
                    consulta += ", contraseña=%s"
                    params.append(hashed)
                consulta += " WHERE email=%s"
                params.append(email)
                cursor.execute(consulta, tuple(params))

                # Obtener id_usuario (una sola vez)
                cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
                res_id = cursor.fetchone()
                target_id = res_id[0] if res_id else None
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO usuarios (nombre, email, id_tipo_usuario, estado_cuenta, contraseña)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nombre, email, id_tipo, estado, hashed or ''))
                target_id = cursor.lastrowid

            # Palabras de recuperación SOLO para Bibliotecario
            if nombre_tipo == "Bibliotecario" and target_id and (not es_actualizacion or forzar_palabras):
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