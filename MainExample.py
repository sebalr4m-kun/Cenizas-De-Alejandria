import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from Modulos.Controllers.InicioSesionController import ControladorLogin
from Modulos.Views.MainWindow import VentanaPrincipal # Ajustado según tu estructura de archivos


ESTILO_GLOBAL = """
    QWidget { background-color: #E0E0E0; color: #000000; }
    QLineEdit, QComboBox, QTableWidget, QDateEdit { background-color: #FFFFFF; border: 1px solid #999999; border-radius: 4px; padding: 4px; }
    QPushButton { background-color: #B0B0B0; border: 1px solid #777777; padding: 8px; border-radius: 4px; font-weight: bold; }
    QPushButton:hover { background-color: #B9B9B9; }
    QPushButton#ActionButton { background-color: #8da9d8; color: #000000; border: 1px solid #6c8db0; }
    QLabel[isTitle="true"] { font-size: 14pt; font-weight: bold; }
    QHeaderView::section { background-color: #B0B0B0; font-weight: bold; padding: 4px; }
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(ESTILO_GLOBAL)
    
    # Instanciamos el nuevo Controlador de Login
    ctrl_login = ControladorLogin()
    
    # Ejecutamos el flujo de autenticación
    # Nota: El controlador ahora maneja internamente la conexión y validación
    if ctrl_login.ejecutar():
        # Si el login fue aceptado (ya sea por credenciales, invitado o llave)
        rol_final, nombre_usuario = ctrl_login.obtener_resultado()
        
        # Lanzamos la ventana principal con el rol obtenido
        ventana = VentanaPrincipal(rol=rol_final)
        # Opcional: podrías pasar el nombre_usuario si tu MainWindow lo requiere
        ventana.show()
        
        sys.exit(app.exec())
    else:
        # Si el usuario cerró el diálogo o canceló
        sys.exit(0)