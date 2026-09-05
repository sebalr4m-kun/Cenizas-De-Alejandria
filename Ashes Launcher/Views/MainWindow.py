# Views/MainWindow.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor
from Views.ListadoVersionesViews import ListadoVersiones
from Views.BarraInferiorViews import BarraInferior
from Views.FormularioSesionesViews import FormularioSesiones

class LauncherMainView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ashes Launcher")
        self.resize(1050, 650)
        self.setStyleSheet("background-color: #FFFFFF; color: #000000; font-family: Arial;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ================= PANEL IZQUIERDO =================
        left_panel = QFrame()
        left_panel.setFixedWidth(320)
        left_panel.setStyleSheet("background-color: #F5F5F7; border-right: 1px solid #E0E0E0;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 30, 20, 20)

        # El título ha sido movido a la derecha. Ahora el panel inicia directo con las versiones.
        self.lista_versiones = ListadoVersiones()
        left_layout.addWidget(self.lista_versiones)

        left_layout.addSpacing(15)

        self.btn_admin_maquinas = QPushButton("Administrar máquinas subordinadas")
        self.btn_admin_maquinas.setFont(QFont("Arial", 10, QFont.Bold))
        self.btn_admin_maquinas.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_admin_maquinas.setStyleSheet("""
            QPushButton {
                background-color: #0066FF;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0052CC;
            }
        """)
        left_layout.addWidget(self.btn_admin_maquinas)

        main_layout.addWidget(left_panel)

        # ================= PANEL DERECHO =================
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #FFFFFF;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 30, 30)

        # Espacio superior elástico
        right_layout.addStretch()

        # Título principal reubicado y centrado
        lbl_titulo = QLabel("CENIZAS DE\nALEJANDRÍA")
        lbl_titulo.setFont(QFont("Impact", 38, QFont.Bold))
        lbl_titulo.setStyleSheet("color: #000000; border: none;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(lbl_titulo)
        
        # Espacio entre el título y el formulario de sesión
        right_layout.addSpacing(25)

        # Formulario de Sesiones
        self.formulario_sesiones = FormularioSesiones()
        right_layout.addWidget(self.formulario_sesiones)
        
        # Espacio inferior elástico
        right_layout.addStretch()

        # Instancia del submódulo de Barra Inferior
        self.barra_inferior = BarraInferior()
        right_layout.addWidget(self.barra_inferior)

        main_layout.addWidget(right_panel)

        self.lista_versiones.version_seleccionada.connect(self.actualizar_boton)

    def actualizar_boton(self, datos_version):
        if datos_version:
            estado_actual = datos_version.get('estado', '').lower()
            esta_instalada = (estado_actual == 'instalada' or estado_actual == 'disponible')
            
            self.barra_inferior.set_estado_boton(esta_instalada)