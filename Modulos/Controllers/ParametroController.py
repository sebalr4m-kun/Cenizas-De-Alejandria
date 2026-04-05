from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem
from Modulos.Models.ParametroModel import ParametroModel
from Modulos.Views.ParametroViews import VistaTablaParametro, FormularioParametro

class ControladorParametro(QObject):
    parametro_guardado = Signal()

    def __init__(self):
        super().__init__()
        self.model = ParametroModel()
        self.widget_vista = None
        self.widget_formulario = None
        self.modo = 'crear'
        self.id_actual = None

    def obtener_widget_vista(self):
        if not self.widget_vista:
            self.widget_vista = VistaTablaParametro(self)
            self.widget_vista.combo_filtro.currentTextChanged.connect(self.filtrar_tabla)
            self.cargar_datos_tabla()
        return self.widget_vista

    def obtener_widget_formulario(self):
        if not self.widget_formulario:
            self.widget_formulario = FormularioParametro(self)
            self.widget_formulario.btn_crear.clicked.connect(self.establecer_crear)
            self.widget_formulario.btn_editar.clicked.connect(self.establecer_editar)
            self.widget_formulario.combo_rubro.currentTextChanged.connect(self.limpiar_formulario)
            self.widget_formulario.entrada_nombre.editingFinished.connect(self.intentar_cargar_por_nombre)
            self.widget_formulario.btn_guardar.clicked.connect(self.manejar_guardado)
        return self.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        """Llamado por MainWindow al cambiar de página"""
        self.establecer_crear()                    # vuelve a modo crear
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
        self.cargar_datos_tabla(texto)

    def cargar_datos_tabla(self, rubro_filtro="Todos"):
        if not self.widget_vista: return
        datos = self.model.obtener_todos(rubro_filtro)
        self.widget_vista.tabla.setRowCount(0)
        for fila, d in enumerate(datos):
            self.widget_vista.tabla.insertRow(fila)
            self.widget_vista.tabla.setItem(fila, 0, QTableWidgetItem(d['nombre']))
            self.widget_vista.tabla.setItem(fila, 1, QTableWidgetItem(d['rubro']))
            self.widget_vista.tabla.setItem(fila, 2, QTableWidgetItem(d['estado']))

    def limpiar_formulario(self):
        if self.widget_formulario:
            self.widget_formulario.entrada_nombre.clear()
            self.widget_formulario.combo_estado.setCurrentIndex(0)

    def intentar_cargar_por_nombre(self):
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
            QMessageBox.warning(None, "Aviso", "No encontrado.")

    def manejar_guardado(self):
        f = self.widget_formulario
        rubro = f.combo_rubro.currentText()
        nombre = f.entrada_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(None, "Error", "Nombre requerido.")
            return

        estado_ui = f.combo_estado.currentText() if self.modo == 'editar' else 'ACTIVO'

        try:
            if self.modo == 'crear':
                self.model.guardar(rubro, nombre, 'ACTIVO', False)
            else:
                if self.id_actual is None:
                    QMessageBox.warning(None, "Error", "Debe cargar un registro primero.")
                    return
                if estado_ui == 'ELIMINADA':
                    self.model.eliminar(rubro, self.id_actual)
                else:
                    self.model.guardar(rubro, nombre, estado_ui, True, self.id_actual)

            self.cargar_datos_tabla()
            self.limpiar_formulario()
            self.parametro_guardado.emit()

            QMessageBox.information(None, "Éxito", f"Operación de {rubro} realizada correctamente.")

        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))