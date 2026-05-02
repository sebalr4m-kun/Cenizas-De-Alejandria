from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem
from Modulos.Models.ParametroModel import ParametroModel
from Modulos.Views.ParametroViews import VistaTablaParametro, FormularioParametro

class ControladorParametro(QObject):
    # Señal vital para notificar a otros módulos (como Usuarios) que hubo cambios
    parametro_guardado = Signal() 

    def __init__(self):
        super().__init__()
        self.model = ParametroModel()
        self.widget_vista = None
        self.widget_formulario = None
        self.modo = 'crear'
        self.id_actual = None

    def obtener_widget_vista(self):
        """Retorna la vista de tabla y conecta el filtro."""
        if not self.widget_vista:
            self.widget_vista = VistaTablaParametro(self)
            self.widget_vista.combo_filtro.currentTextChanged.connect(self.filtrar_tabla)
            self.cargar_datos_tabla()
        return self.widget_vista

    def obtener_widget_formulario(self):
        """Retorna el formulario y conecta toda la lógica de interacción."""
        if not self.widget_formulario:
            self.widget_formulario = FormularioParametro(self)
            self.widget_formulario.btn_crear.clicked.connect(self.establecer_crear)
            self.widget_formulario.btn_editar.clicked.connect(self.establecer_editar)
            self.widget_formulario.combo_rubro.currentTextChanged.connect(self.limpiar_formulario)
            self.widget_formulario.entrada_nombre.editingFinished.connect(self.intentar_cargar_por_nombre)
            self.widget_formulario.btn_guardar.clicked.connect(self.manejar_guardado)
        return self.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        """Reset de seguridad para la UI."""
        self.establecer_crear()
        if self.widget_formulario:
            self.widget_formulario.widget_contenido.hide()

    def establecer_crear(self):
        self.modo = 'crear'
        self.id_actual = None
        if self.widget_formulario:
            self.widget_formulario.establecer_modo_ui('crear')
        self.limpiar_formulario()

    def establecer_editar(self):
        self.modo = 'editar'
        self.id_actual = None
        if self.widget_formulario:
            self.widget_formulario.establecer_modo_ui('editar')
        self.limpiar_formulario()

    def filtrar_tabla(self, texto):
        """Filtra los resultados basándose en el rubro seleccionado."""
        self.cargar_datos_tabla(texto)

    def cargar_datos_tabla(self, rubro_filtro=None):
        """Refresco de tabla basándose en los datos actuales de la BD[cite: 5]."""
        if not self.widget_vista: return
        
        filtro = rubro_filtro if rubro_filtro and rubro_filtro != "Todos" else "Todos"
        datos = self.model.obtener_todos(filtro)
        self.widget_vista.tabla.setRowCount(0)
        
        for fila, d in enumerate(datos):
            self.widget_vista.tabla.insertRow(fila)
            self.widget_vista.tabla.setItem(fila, 0, QTableWidgetItem(str(d['nombre'])))
            self.widget_vista.tabla.setItem(fila, 1, QTableWidgetItem(str(d['rubro'])))
            self.widget_vista.tabla.setItem(fila, 2, QTableWidgetItem(str(d['estado'])))

    def limpiar_formulario(self):
        if self.widget_formulario:
            self.widget_formulario.entrada_nombre.clear()
            self.widget_formulario.combo_estado.setCurrentIndex(0)

    def intentar_cargar_por_nombre(self):
        """Busca el registro en la BD para habilitar la edición[cite: 5]."""
        if self.modo != 'editar': return
        
        rubro = self.widget_formulario.combo_rubro.currentText()
        nombre = self.widget_formulario.entrada_nombre.text().strip()
        if not nombre: return

        info = self.model.obtener_info_por_nombre(rubro, nombre)
        if info:
            self.id_actual = info['id']
            self.widget_formulario.combo_estado.setCurrentText(info['estado'])
        else:
            self.id_actual = None
            QMessageBox.warning(None, "Aviso", f"No se encontró '{nombre}' en {rubro}.")

    def manejar_guardado(self):
        """Ejecuta el guardado directo y dispara el protocolo de refresco[cite: 5]."""
        f = self.widget_formulario
        rubro = f.combo_rubro.currentText()
        nombre = f.entrada_nombre.text().strip()
        
        if not nombre:
            QMessageBox.warning(None, "Error", "El nombre es requerido.")
            return

        # Determinamos el estado: si es nuevo siempre ACTIVO, si es editar lo que diga el combo[cite: 5].
        estado_final = f.combo_estado.currentText() if self.modo == 'editar' else 'ACTIVO'

        try:
            if self.modo == 'crear':
                # Llamada directa al INSERT del modelo
                self.model.guardar(rubro, nombre, 'ACTIVO', False)
            else:
                if self.id_actual is None:
                    QMessageBox.warning(None, "Error", "Debe cargar un registro antes de editar.")
                    return
                
                # Ejecuta el UPDATE o la inactivación en cascada según el estado[cite: 3, 5]
                if estado_final in ('INACTIVO', 'INACTIVA'):
                    self.model.inactivar_parametro_y_dependientes(rubro, self.id_actual)
                else:
                    self.model.guardar(rubro, nombre, estado_final, True, self.id_actual)

            # Actualizar la tabla local inmediatamente[cite: 5]
            self.cargar_datos_tabla()
            
            # Emitir señal para que otros módulos (Usuarios/Insumos) se actualicen[cite: 5]
            self.parametro_guardado.emit() 

            self.limpiar_formulario()
            QMessageBox.information(None, "Éxito", f"Cambios en {rubro} guardados correctamente.")

        except Exception as e:
            QMessageBox.critical(None, "Error de Base de Datos", f"No se pudo guardar: {str(e)}")