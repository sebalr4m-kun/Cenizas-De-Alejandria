# Views/ListadoVersionesViews.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QListWidget, QListWidgetItem, QPushButton, QFrame, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

class TarjetaVersion(QWidget):
    def __init__(self, id_version, titulo, version, fecha, precio, estado, adquirible=False):
        super().__init__()
        self.id_version = id_version
        self.estado = estado
        
        self.setStyleSheet("""
            TarjetaVersion {
                background-color: #FFFFFF;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
            }
        """)
        
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Arial", 9, QFont.Bold))
        lbl_titulo.setStyleSheet("color: #111111; border: none;")
        
        lbl_version = QLabel(version)
        lbl_version.setFont(QFont("Arial", 9))
        lbl_version.setStyleSheet("color: #444444; border: none;")
        lbl_version.setAlignment(Qt.AlignCenter)
        
        lbl_fecha = QLabel(fecha)
        lbl_fecha.setFont(QFont("Arial", 9))
        lbl_fecha.setStyleSheet("color: #666666; border: none;")
        lbl_fecha.setAlignment(Qt.AlignCenter)

        lbl_precio = QLabel(precio)
        lbl_precio.setFont(QFont("Arial", 9, QFont.Bold))
        lbl_precio.setStyleSheet("color: #2B7A78; border: none;")
        lbl_precio.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(lbl_titulo, 0, 0)
        layout.addWidget(lbl_version, 0, 1)
        layout.addWidget(lbl_fecha, 0, 2)
        layout.addWidget(lbl_precio, 0, 3)
        
        if adquirible:
            self.btn_comprar = QPushButton("Comprar")
            self.btn_comprar.setCursor(QCursor(Qt.PointingHandCursor))
            self.btn_comprar.setStyleSheet("""
                QPushButton { background-color: #28A745; color: white; font-weight: bold; padding: 4px 8px; border-radius: 3px; border: none; }
                QPushButton:hover { background-color: #218838; }
            """)
            layout.addWidget(self.btn_comprar, 0, 4, Qt.AlignRight)
        else:
            lbl_estado = QLabel(estado.upper())
            lbl_estado.setFont(QFont("Arial", 9, QFont.Bold))
            lbl_estado.setStyleSheet("color: #0066FF; border: none;")
            layout.addWidget(lbl_estado, 0, 4, Qt.AlignRight)

        layout.setColumnStretch(0, 3) 
        layout.setColumnStretch(1, 1) 
        layout.setColumnStretch(2, 2) 
        layout.setColumnStretch(3, 1) 
        layout.setColumnStretch(4, 2) 

class ListadoVersiones(QWidget):
    version_seleccionada = Signal(dict)
    solicitud_compra = Signal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # --- SECCIÓN DISPONIBLES ---
        lbl_disp = QLabel("VERSIONES DISPONIBLES")
        lbl_disp.setFont(QFont("Arial", 10, QFont.Bold))
        lbl_disp.setStyleSheet("color: #333333;")
        layout.addWidget(lbl_disp)
        
        # Cabecera siempre visible
        self.cabecera_disp = self._crear_cabecera()
        layout.addWidget(self.cabecera_disp)
        
        self.lista_disponibles = QListWidget()
        self.lista_disponibles.hide() 
        self.lista_disponibles.setStyleSheet("""
            QListWidget { background-color: #EAEAEA; border: 1px solid #CCCCCC; border-radius: 4px; outline: none; padding: 4px; }
            QListWidget::item { margin-bottom: 4px; }
            QListWidget::item:selected { background-color: #D0E4FF; border-radius: 4px; }
        """)
        self.lista_disponibles.itemSelectionChanged.connect(self._emitir_seleccion)
        layout.addWidget(self.lista_disponibles)
        
        self.lbl_sin_disponibles = QLabel("(Sin versiones disponibles encontradas en la máquina)")
        self.lbl_sin_disponibles.setAlignment(Qt.AlignCenter)
        self.lbl_sin_disponibles.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_sin_disponibles.setStyleSheet("color: #777777; font-style: italic; background-color: #EAEAEA; border: 1px solid #CCCCCC; border-radius: 4px;")
        layout.addWidget(self.lbl_sin_disponibles)
        
        # --- SECCIÓN ADQUIRIBLES ---
        lbl_adq = QLabel("VERSIONES ADQUIRIBLES")
        lbl_adq.setFont(QFont("Arial", 10, QFont.Bold))
        lbl_adq.setStyleSheet("color: #333333; padding-top: 6px;")
        layout.addWidget(lbl_adq)

        # Cabecera siempre visible
        self.cabecera_adq = self._crear_cabecera()
        layout.addWidget(self.cabecera_adq)
        
        self.lista_adquiribles = QListWidget()
        self.lista_adquiribles.hide()
        self.lista_adquiribles.setStyleSheet("""
            QListWidget { background-color: #EAEAEA; border: 1px solid #CCCCCC; border-radius: 4px; outline: none; padding: 4px; }
            QListWidget::item { margin-bottom: 4px; }
            QListWidget::item:selected { background-color: transparent; }
        """)
        layout.addWidget(self.lista_adquiribles)
        
        self.lbl_sin_adquiribles = QLabel("(Sin versiones adquiribles encontradas en el servidor)")
        self.lbl_sin_adquiribles.setAlignment(Qt.AlignCenter)
        self.lbl_sin_adquiribles.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_sin_adquiribles.setStyleSheet("color: #777777; font-style: italic; background-color: #EAEAEA; border: 1px solid #CCCCCC; border-radius: 4px;")
        layout.addWidget(self.lbl_sin_adquiribles)

    def _crear_cabecera(self):
        cabecera = QFrame()
        cabecera.setStyleSheet("background-color: #D8D8D8; border-radius: 3px; padding: 2px;")
        grid = QGridLayout(cabecera)
        grid.setContentsMargins(8, 4, 8, 4)

        t_tit = QLabel("TÍTULO")
        t_ver = QLabel("VERSIÓN")
        t_fec = QLabel("FECHA")
        t_pre = QLabel("PRECIO")
        t_est = QLabel("ESTATUS")

        for label in [t_tit, t_ver, t_fec, t_pre, t_est]:
            label.setFont(QFont("Arial", 8, QFont.Bold))
            label.setStyleSheet("color: #444444; border: none;")

        t_ver.setAlignment(Qt.AlignCenter)
        t_fec.setAlignment(Qt.AlignCenter)
        t_pre.setAlignment(Qt.AlignCenter)
        t_est.setAlignment(Qt.AlignRight)

        grid.addWidget(t_tit, 0, 0)
        grid.addWidget(t_ver, 0, 1)
        grid.addWidget(t_fec, 0, 2)
        grid.addWidget(t_pre, 0, 3)
        grid.addWidget(t_est, 0, 4)

        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 2)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 2)

        return cabecera

    def poblar_disponibles(self, versiones_data):
        self.lista_disponibles.clear()
        if not versiones_data:
            self.lista_disponibles.hide()
            self.lbl_sin_disponibles.show()
            return
            
        self.lista_disponibles.show()
        self.lbl_sin_disponibles.hide()
        
        for v in versiones_data:
            item = QListWidgetItem(self.lista_disponibles)
            widget = TarjetaVersion(
                v['id'], v['titulo'], v['version'], v['fecha'], 
                v.get('precio', 'Incluido'), v['estado'], adquirible=False
            )
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, v)
            self.lista_disponibles.addItem(item)
            self.lista_disponibles.setItemWidget(item, widget)

    def poblar_adquiribles(self, versiones_data):
        self.lista_adquiribles.clear()
        if not versiones_data:
            self.lista_adquiribles.hide()
            self.lbl_sin_adquiribles.show()
            return
            
        self.lista_adquiribles.show()
        self.lbl_sin_adquiribles.hide()
        
        for v in versiones_data:
            item = QListWidgetItem(self.lista_adquiribles)
            widget = TarjetaVersion(
                v['id'], v['titulo'], v['version'], v['fecha'], 
                v.get('precio', '$0.00'), v['estado'], adquirible=True
            )
            widget.btn_comprar.clicked.connect(lambda checked=False, id_v=v['id']: self.solicitud_compra.emit(id_v))
            item.setSizeHint(widget.sizeHint())
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.lista_adquiribles.addItem(item)
            self.lista_adquiribles.setItemWidget(item, widget)

    def _emitir_seleccion(self):
        items = self.lista_disponibles.selectedItems()
        if items:
            datos_version = items[0].data(Qt.UserRole)
            self.version_seleccionada.emit(datos_version)