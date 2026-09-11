# ==========================================
# Archivo: PrestamoController.py
# ==========================================
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import QMessageBox, QListWidgetItem

from Modulos.Models.PrestamoModel import PrestamoModel
from Modulos.Auditorias import auditoria_global
from Modulos.Views.PrestamoViews import VistaTablaPrestamo, FormularioPrestamo

class ControladorPrestamo(QObject):
    datos_actualizados = Signal() 

    def __init__(self):
        super().__init__()
        self.model = PrestamoModel()
        self.ctrl_param = None
        
        self.widget_vista = None
        self.widget_formulario = None
        self._esta_cargando = False
        self.prestamo_seleccionado = None

    def obtener_widget_vista(self):
        if not self.widget_vista:
            self.widget_vista = VistaTablaPrestamo(self)
            self.widget_vista.tabla.itemSelectionChanged.connect(self.al_seleccionar_prestamo)
            self.cargar_datos_tabla()
        return self.widget_vista

    def obtener_widget_formulario(self, ctrl_param):
        self.ctrl_param = ctrl_param
        if not self.widget_formulario:
            self.widget_formulario = FormularioPrestamo(self)
            
            self.widget_formulario.btn_guardar.clicked.connect(self.manejar_guardado)
            self.widget_formulario.btn_devolver.clicked.connect(self.manejar_devolucion)
            
            if hasattr(self.ctrl_param, 'parametro_guardado'):
                self.ctrl_param.parametro_guardado.connect(self.cargar_combos)

            self.cargar_combos()
        return self.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        if self.widget_formulario:
            self.widget_formulario.limpiar_interfaz()
            self.prestamo_seleccionado = None

    def cargar_datos_tabla(self):
        if self._esta_cargando: return
        try:
            self._esta_cargando = True
            if self.widget_vista:
                datos = self.model.obtener_todos()
                self.widget_vista.actualizar_tabla(datos)
        finally:
            self._esta_cargando = False

    def cargar_combos(self):
        if not self.widget_formulario: return
        try:
            # 1. Cargar Usuarios
            self.widget_formulario.lista_usuarios.clear()
            usuarios = self.model.obtener_usuarios_elegibles()
            for u in usuarios:
                texto = f"{u['nombre']} ({u['email']})"
                item = QListWidgetItem(texto)
                item.setData(Qt.UserRole, u['id_usuario'])
                self.widget_formulario.lista_usuarios.addItem(item)

            # 2. Cargar Categorías (Tipos de insumo)
            self.widget_formulario.combo_tipo_insumo.blockSignals(True)
            self.widget_formulario.combo_tipo_insumo.clear()
            self.widget_formulario.combo_tipo_insumo.addItem("Todas las categorías", None)
            
            categorias = self.model.obtener_tipos_insumo()
            for cat in categorias:
                self.widget_formulario.combo_tipo_insumo.addItem(cat['nombre'], cat['id_tipo_insumo'])
            self.widget_formulario.combo_tipo_insumo.blockSignals(False)

            # 3. Cargar Lista de Insumos Disponibles (Se hace UNA SOLA VEZ)
            self.widget_formulario.lista_insumos.clear()
            insumos = self.model.obtener_insumos_disponibles()
            
            for i in insumos:
                texto = f"[{i['clave_runa']}] {i['titulo']}"
                item = QListWidgetItem(texto)
                item.setData(Qt.UserRole, i['id_insumo'])
                item.setData(Qt.UserRole + 1, i['id_tipo_insumo']) # Metadato para el filtro dinámico visual
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.widget_formulario.lista_insumos.addItem(item)

            # Forzar un filtrado inicial
            self.al_cambiar_categoria()

        except Exception as e:
            print(f"Error al cargar desplegables y listas en Préstamos: {e}")

    def al_cambiar_categoria(self):
        """Invoca el mecanismo de filtrado visual de la vista sin eliminar ni recrear elementos de la lista."""
        if not self.widget_formulario: return
        self.widget_formulario.filtrar_lista_insumos()

    def al_seleccionar_prestamo(self):
        """Carga en el panel de devolución los libros correspondientes al préstamo activo."""
        if not self.widget_formulario or not self.widget_vista: return
        filas = self.widget_vista.tabla.selectedItems()
        if not filas:
            self.prestamo_seleccionado = None
            return

        self.prestamo_seleccionado = self.widget_vista.tabla.item(filas[0].row(), 0).data(Qt.UserRole)
        
        if self.widget_formulario.modo == 'editar' and self.prestamo_seleccionado:
            id_p = self.prestamo_seleccionado['id_prestamo']
            usuario = self.prestamo_seleccionado['usuario_nombre']
            
            self.widget_formulario.label_prestamo_info.setText(
                f"Préstamo #{id_p} - Usuario: {usuario}"
            )
            
            # Cargar ítems pertenecientes a este préstamo
            detalles = self.model.obtener_detalles_prestamo(id_p)
            self.widget_formulario.lista_devolucion.clear()
            
            for d in detalles:
                estado_txt = f"[{d['estado_item']}]"
                texto = f"{estado_txt} [{d['clave_runa']}] {d['titulo']}"
                item = QListWidgetItem(texto)
                item.setData(Qt.UserRole, d['id_detalle'])
                
                if d['estado_item'] == 'DEVUELTO':
                    item.setFlags(Qt.NoItemFlags) # Deshabilitado si ya fue devuelto
                    item.setCheckState(Qt.Checked)
                else:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    
                self.widget_formulario.lista_devolucion.addItem(item)

    def manejar_guardado(self):
        """Procesa el registro de un préstamo con 1 o más insumos elegidos."""
        item_user = self.widget_formulario.lista_usuarios.currentItem()
        if not item_user:
            QMessageBox.warning(None, "Validación", "Debe seleccionar un usuario solicitante.")
            return

        id_usuario = item_user.data(Qt.UserRole)
        
        # Recolectar ítems marcados con checkbox
        insumos_seleccionados = []
        for i in range(self.widget_formulario.lista_insumos.count()):
            item = self.widget_formulario.lista_insumos.item(i)
            if item.checkState() == Qt.Checked:
                insumos_seleccionados.append(item.data(Qt.UserRole))

        if not insumos_seleccionados:
            QMessageBox.warning(None, "Validación", "Debe marcar al menos un ítem para realizar el préstamo.")
            return

        try:
            id_prestamo = self.model.registrar_prestamo_conjunto(id_usuario, insumos_seleccionados)
            auditoria_global.auditar_accion(
                1, "Préstamos", f"Registrado préstamo #{id_prestamo} con {len(insumos_seleccionados)} ítems."
            )
            QMessageBox.information(None, "Éxito", f"Préstamo #{id_prestamo} registrado correctamente.")
            self.finalizar_transaccion()
        except Exception as e:
            QMessageBox.critical(None, "Error de Transacción", f"No se pudo registrar el préstamo:\n{e}")

    def manejar_devolucion(self):
        """Registra la devolución de los ítems seleccionados en la lista."""
        if not self.prestamo_seleccionado:
            QMessageBox.warning(None, "Selección", "Debe seleccionar un préstamo de la tabla superior.")
            return

        id_p = self.prestamo_seleccionado['id_prestamo']
        detalles_a_devolver = []

        for i in range(self.widget_formulario.lista_devolucion.count()):
            item = self.widget_formulario.lista_devolucion.item(i)
            # Solo consideramos ítems activos marcados por el operador
            if item.flags() & Qt.ItemIsEnabled and item.checkState() == Qt.Checked:
                detalles_a_devolver.append(item.data(Qt.UserRole))

        if not detalles_a_devolver:
            QMessageBox.warning(None, "Atención", "Marque la casilla de al menos un ítem devuelto.")
            return

        try:
            todo_devuelto = self.model.procesar_devolucion_parcial(id_p, detalles_a_devolver)
            auditoria_global.auditar_accion(
                2, "Préstamos", f"Devolución parcial/total registrada en préstamo #{id_p}."
            )
            
            if todo_devuelto:
                QMessageBox.information(None, "Préstamo Completado", "Todos los ítems han sido devueltos. El préstamo queda CERRADO.")
            else:
                QMessageBox.information(None, "Devolución Parcial", "Devolución registrada. El préstamo permanece ACTIVO por ítems pendientes.")
            
            self.finalizar_transaccion()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Fallo al registrar la devolución:\n{e}")

    def finalizar_transaccion(self):
        self.cargar_datos_tabla()
        self.cargar_combos()
        self.reiniciar_visibilidad_formulario()
        self.datos_actualizados.emit()