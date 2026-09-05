import json
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem
from Modulos.Models.ParametroModel import ParametroModel
from Modulos.Views.ParametroViews import VistaTablaParametro, FormularioParametro
from Modulos.Auditorias import auditoria_global

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
            self.cargar_datos_tabla()
            
            # Interceptor para asegurar que el doble clic también cargue los permisos RBAC
            self.widget_vista.tabla.itemDoubleClicked.connect(self._interceptar_doble_clic)
        return self.widget_vista

    def obtener_widget_formulario(self):
        """Retorna el formulario y conecta la lógica de negocio, dejando la UI a la Vista."""
        if not self.widget_formulario:
            self.widget_formulario = FormularioParametro(self)
            self.widget_formulario.btn_crear.clicked.connect(self.establecer_crear)
            self.widget_formulario.btn_editar.clicked.connect(self.establecer_editar)
            
            self.widget_formulario.combo_rubro.currentTextChanged.connect(self._reset_id_por_rubro)
            self.widget_formulario.entrada_nombre.editingFinished.connect(self.intentar_cargar_por_nombre)
            self.widget_formulario.btn_guardar.clicked.connect(self.manejar_guardado)
        return self.widget_formulario

    def reiniciar_visibilidad_formulario(self):
        """Reset de seguridad llamado externamente al cambiar de panel."""
        self.establecer_crear()
        if self.widget_formulario:
            self.widget_formulario.limpiar_formulario()

    def _reset_id_por_rubro(self):
        """Evita que se guarden cambios en un ID antiguo si el usuario cambia el rubro a mitad de edición."""
        self.id_actual = None

    def establecer_crear(self):
        """Prepara el controlador y la vista para un nuevo registro."""
        self.modo = 'crear'
        self.id_actual = None
        if self.widget_formulario:
            self.widget_formulario.establecer_modo_ui('crear')

    def establecer_editar(self):
        """Prepara el controlador y la vista para modificar un registro (Usado por el doble click)."""
        self.modo = 'editar'
        if self.widget_formulario:
            self.widget_formulario.establecer_modo_ui('editar')

    def cargar_datos_tabla(self, rubro_filtro=None):
        """Refresco de tabla basándose en los datos actuales de la BD."""
        if not self.widget_vista: return
        
        filtro = rubro_filtro if rubro_filtro and rubro_filtro != "Todos" else "Todos"
        datos = self.model.obtener_todos(filtro)
        self.widget_vista.tabla.setRowCount(0)
        
        for fila, d in enumerate(datos):
            self.widget_vista.tabla.insertRow(fila)
            self.widget_vista.tabla.setItem(fila, 0, QTableWidgetItem(str(d['nombre'])))
            self.widget_vista.tabla.setItem(fila, 1, QTableWidgetItem(str(d['rubro'])))
            self.widget_vista.tabla.setItem(fila, 2, QTableWidgetItem(str(d['estado'])))

    def _interceptar_doble_clic(self, item):
        """Garantiza que al seleccionar de la tabla, se procesen los datos JSON y de Admisión."""
        self.intentar_cargar_por_nombre()

    def intentar_cargar_por_nombre(self):
        """Busca el registro en la BD para habilitar la edición si el usuario lo escribe manualmente."""
        if self.modo != 'editar' or not self.widget_formulario: return
        
        # Extraemos datos limpios usando la nueva API de la vista
        datos_ui = self.widget_formulario.obtener_datos_formulario()
        rubro = datos_ui["rubro"]
        nombre = datos_ui["nombre"]
        
        if not nombre: return

        info = self.model.obtener_info_por_nombre(rubro, nombre)
        if info:
            self.id_actual = info['id']
            # Devolvemos el estado a la vista
            self.widget_formulario.combo_estado.blockSignals(True)
            self.widget_formulario.combo_estado.setCurrentText(info['estado'])
            self.widget_formulario.combo_estado.blockSignals(False)
            
            # Carga del RBAC Dinámico
            if rubro == "Tipo Usuario":
                # 1. Cargar Switch de Admisión
                admitido_val = bool(info.get('admitido', 0))
                self.widget_formulario.switch_admitido.blockSignals(True)
                self.widget_formulario.switch_admitido.setChecked(admitido_val)
                self.widget_formulario.switch_admitido.blockSignals(False)

                # Evaluar visibilidad antes de inyectar sub-módulos
                self.widget_formulario.evaluar_switches_modulos()

                # 2. Extraer y decodificar el JSON de permisos
                permisos_str = info.get('permisos', '{}')
                try:
                    permisos_dict = json.loads(permisos_str) if permisos_str else {}
                except Exception:
                    permisos_dict = {}

                # 3. Mapear de vuelta a los controles de la vista
                for mod_key, controles in self.widget_formulario.permisos.items():
                    # Tolerancia de lectura: busca la clave 'libros' o 'Libros'
                    datos_modulo = permisos_dict.get(mod_key) or permisos_dict.get(mod_key.capitalize()) or {}

                    controles['ver'].blockSignals(True)
                    controles['editar'].blockSignals(True)
                    controles['borrar'].blockSignals(True)

                    controles['ver'].setChecked(datos_modulo.get('ver', False))
                    controles['editar'].setChecked(datos_modulo.get('editar', False) or datos_modulo.get('crear', False))
                    controles['borrar'].setChecked(datos_modulo.get('borrar', False) or datos_modulo.get('eliminar', False))

                    controles['ver'].blockSignals(False)
                    controles['editar'].blockSignals(False)
                    controles['borrar'].blockSignals(False)
                
                # --- SINCRONIZACIÓN FINAL DE LA VISTA ---
                # Despierta la lógica de cascada (para que los botones no queden en gris)
                self.widget_formulario.forzar_evaluacion_cascada()
                
            # Toma la "foto" del estado inicial cargado para el Control de Cambios (Botón Guardar)
            self.widget_formulario.fijar_estado_original()
            
        else:
            self.id_actual = None
            QMessageBox.warning(None, "Aviso", f"No se encontró '{nombre}' en {rubro}.")

    def manejar_guardado(self):
        """Extrae la información RBAC completa y ejecuta el guardado o eliminación."""
        if not self.widget_formulario: return
        
        # 1. Extracción pura y limpia de los datos de la vista
        datos_ui = self.widget_formulario.obtener_datos_formulario()
        rubro = datos_ui["rubro"]
        nombre = datos_ui["nombre"]
        
        if not nombre:
            QMessageBox.warning(None, "Error", "El nombre identificativo es requerido.")
            return

        # Determinamos el estado final dependiendo del modo
        estado_final = datos_ui["estado"] if self.modo == 'editar' else 'ACTIVO'

        # 2. Empaquetado de datos RBAC exclusivos
        admitido = None
        permisos_json = None
        if rubro == "Tipo Usuario":
            admitido = 1 if datos_ui.get("admitido", False) else 0
            permisos_json = json.dumps(datos_ui.get("permisos", {}))

        try:
            if self.modo == 'crear':
                self.model.guardar(rubro, nombre, 'ACTIVO', False, admitido=admitido, permisos=permisos_json)
                auditoria_global.auditar_accion(1, "Parámetros", f"Creación de parámetro '{nombre}' en rubro '{rubro}'")
                QMessageBox.information(None, "Éxito", f"Parámetro de {rubro} creado correctamente.")
            else:
                if self.id_actual is None:
                    QMessageBox.warning(None, "Error", "Debe cargar o seleccionar un registro de la tabla antes de guardar cambios.")
                    return
                
                # Ejecuta el UPDATE, Inactivación o Borrado Físico
                if estado_final in ('INACTIVO', 'INACTIVA'):
                    self.model.inactivar_parametro_y_dependientes(rubro, self.id_actual)
                    auditoria_global.auditar_accion(3, "Parámetros", f"Inactivación de parámetro '{nombre}' en rubro '{rubro}'")
                    QMessageBox.information(None, "Éxito", f"Parámetro inactivado correctamente.")
                elif 'ELIMINAR' in estado_final: # Detecta la opción de borrado físico ignorando si dice "(Peligro)" o no
                    self.model.eliminar_fisicamente(rubro, self.id_actual)
                    auditoria_global.auditar_accion(4, "Parámetros", f"Borrado físico de parámetro '{nombre}' en rubro '{rubro}'")
                    QMessageBox.information(None, "Éxito", f"Parámetro eliminado físicamente de la base de datos.")
                else:
                    self.model.guardar(rubro, nombre, estado_final, True, self.id_actual, admitido=admitido, permisos=permisos_json)
                    auditoria_global.auditar_accion(2, "Parámetros", f"Actualización de parámetro '{nombre}' en rubro '{rubro}'")
                    QMessageBox.information(None, "Éxito", f"Parámetro de {rubro} actualizado correctamente.")

            # Actualizar la tabla local inmediatamente
            self.cargar_datos_tabla()
            
            # Limpiar la UI y regresar al modo crear por seguridad
            self.widget_formulario.limpiar_formulario()
            self.establecer_crear()
            
            # Emitir señal para que otros módulos se actualicen (RBAC Dinámico)
            self.parametro_guardado.emit() 

        except Exception as e:
            QMessageBox.critical(None, "Error de Base de Datos", f"No se pudo completar la operación:\n{str(e)}")