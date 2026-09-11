# Views/BarraInferior.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor

class BarraInferior(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Panel de Progreso
        progreso_layout = QVBoxLayout()
        
        # Etiquetas de información de descarga
        info_descarga_layout = QHBoxLayout()
        self.lbl_estado = QLabel("Preparando descarga...")
        self.lbl_estado.setStyleSheet("color: #AAA;")
        self.lbl_detalles = QLabel("0 MB / 0 MB (0 KB/s)")
        self.lbl_detalles.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_detalles.setAlignment(Qt.AlignRight)
        
        info_descarga_layout.addWidget(self.lbl_estado)
        info_descarga_layout.addWidget(self.lbl_detalles)
        
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setFixedHeight(8)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.setStyleSheet("""
            QProgressBar { border: none; background-color: #333; border-radius: 4px; }
            QProgressBar::chunk { background-color: #5A9BD5; border-radius: 4px; }
        """)
        self.barra_progreso.setValue(0)
        
        progreso_layout.addLayout(info_descarga_layout)
        progreso_layout.addWidget(self.barra_progreso)
        
        layout.addLayout(progreso_layout)
        layout.addSpacing(20)
        
        # Botón Principal
        self.btn_accion = QPushButton("INSTALAR")
        self.btn_accion.setFixedSize(220, 60)
        self.btn_accion.setFont(QFont("Arial", 16, QFont.Bold))
        self.btn_accion.setCursor(QCursor(Qt.PointingHandCursor))
        self.set_estado_boton(False) # Por defecto
        
        layout.addWidget(self.btn_accion)

    def set_estado_boton(self, esta_instalada):
        if esta_instalada:
            self.btn_accion.setText("EJECUTAR")
            self.btn_accion.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 60, 0, 200);
                    color: white; border: 2px solid #FF5500; border-radius: 2px;
                }
                QPushButton:hover { background-color: rgba(255, 80, 20, 255); }
            """)
        else:
            self.btn_accion.setText("INSTALAR")
            self.btn_accion.setStyleSheet("""
                QPushButton {
                    background-color: rgba(70, 130, 180, 200);
                    color: white; border: 2px solid #5A9BD5; border-radius: 2px;
                }
                QPushButton:hover { background-color: rgba(90, 150, 200, 255); }
            """)