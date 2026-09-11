import json
from Modulos.Config import Conexion

class LoginModel:
    def __init__(self):
        self.conexion = Conexion()

    def verificar_credenciales(self, email, contrasena):
        """
        Verifica el login y retorna un 'Pasaporte de Sesión' completo,
        incluyendo el flag de admisión y el JSON de privilegios decodificado.
        """
        bd = self.conexion.obtener_conexion()
        if not bd:
            return None
            
        bd.commit() # Limpia caché para leer credenciales actualizadas al instante
        cursor = bd.cursor(dictionary=True)
        try:
            consulta = """
                SELECT u.id_usuario, u.nombre, p.nombre AS rol, u.contraseña, p.admitido, p.permisos 
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
                    
                    # Decodificación segura del árbol de permisos RBAC
                    try:
                        permisos_dict = json.loads(usuario['permisos']) if usuario['permisos'] else {}
                    except Exception:
                        permisos_dict = {}

                    # Retornamos el Pasaporte de Sesión
                    return {
                        'id_usuario': usuario['id_usuario'],
                        'nombre': usuario['nombre'],
                        'rol': usuario['rol'],
                        'admitido': bool(usuario['admitido']),
                        'permisos': permisos_dict
                    }
            return None
        except Exception as e:
            print(f"[ERROR LOGIN] Error en verificar_credenciales: {e}")
            return None
        finally:
            cursor.close()

    def _obtener_mod_seguro(self, perms_dict, clave_ideal):
        """
        Buscador tolerante a acentos y variaciones de capitalización para el JSON.
        Previene fallas de lectura si la base de datos guarda 'parámetros' en lugar de 'parametros'.
        """
        # Búsqueda exacta rápida
        if clave_ideal in perms_dict: 
            return perms_dict[clave_ideal]
        if clave_ideal.lower() in perms_dict: 
            return perms_dict[clave_ideal.lower()]
        
        # Búsqueda profunda ignorando acentos
        clave_norm = clave_ideal.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        for k, v in perms_dict.items():
            k_norm = k.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            if k_norm == clave_norm:
                return v
        return {}
        
    def hay_dios_de_la_maquina_activo(self):
        """
        Vigilante de integridad: Devuelve True si existe al menos un usuario ACTIVO que cumpla con:
        1. Su tipo es ADMItido (admitido = 1).
        2. Tiene permisos completos para ver y editar Usuarios.
        3. Tiene permisos completos para ver y editar Parámetros.
        """
        bd = self.conexion.obtener_conexion()
        if not bd:
            return None
            
        bd.commit() # Evita falsos negativos en el arranque del sistema
        cursor = bd.cursor(dictionary=True)
        try:
            consulta = """
                SELECT p.permisos 
                FROM usuarios u
                JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                WHERE u.estado_cuenta = 'ACTIVA' 
                  AND p.admitido = 1
            """
            cursor.execute(consulta)
            candidatos = cursor.fetchall()

            for candidato in candidatos:
                try:
                    perms = json.loads(candidato['permisos']) if candidato['permisos'] else {}
                except Exception:
                    continue

                # Usamos el buscador seguro para garantizar que lea 'parámetros' correctamente
                usuarios_ok = self._obtener_mod_seguro(perms, "Usuarios").get("ver", False) and self._obtener_mod_seguro(perms, "Usuarios").get("editar", False)
                parametros_ok = self._obtener_mod_seguro(perms, "Parametros").get("ver", False) and self._obtener_mod_seguro(perms, "Parametros").get("editar", False)

                if usuarios_ok and parametros_ok:
                    return True # Se encontró un salvaguarda del sistema válido, SE MOSTRARÁ EL LOGIN

            # Ningún candidato pasó las pruebas, se activará el Modo de Rescate
            return False
            
        except Exception as e:
            print(f"[ERROR LOGIN] Error en hay_dios_de_la_maquina_activo: {e}")
            return False
        finally:
            cursor.close()

    def obtener_lista_salvavidas_ddlm(self):
        """
        Rastrea y recopila todos los usuarios que fungen como pilares del sistema.
        Retorna una lista de correos electrónicos de aquellos que evitan que el sistema
        caiga en el modo Dios De La Máquina.
        """
        bd = self.conexion.obtener_conexion()
        if not bd:
            return []
            
        bd.commit() # Fuerza lectura en tiempo real para evitar discrepancias de caché
        cursor = bd.cursor(dictionary=True)
        salvavidas = []
        try:
            consulta = """
                SELECT u.email, p.permisos 
                FROM usuarios u
                JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                WHERE u.estado_cuenta = 'ACTIVA' 
                  AND p.admitido = 1
            """
            cursor.execute(consulta)
            candidatos = cursor.fetchall()

            for candidato in candidatos:
                try:
                    perms = json.loads(candidato['permisos']) if candidato['permisos'] else {}
                except Exception:
                    continue

                usuarios_ok = self._obtener_mod_seguro(perms, "Usuarios").get("ver", False) and self._obtener_mod_seguro(perms, "Usuarios").get("editar", False)
                parametros_ok = self._obtener_mod_seguro(perms, "Parametros").get("ver", False) and self._obtener_mod_seguro(perms, "Parametros").get("editar", False)

                if usuarios_ok and parametros_ok:
                    salvavidas.append(candidato['email'])

            return salvavidas
        except Exception as e:
            print(f"[ERROR DDLM] Error en obtener_lista_salvavidas_ddlm: {e}")
            return []
        finally:
            cursor.close()