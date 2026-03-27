import random
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from Modulos.Config import Conexion

class ValidadorRecuperacion(QDialog):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.setWindowTitle("VALIDACIÓN DE IDENTIDAD - BIBLIOTECARIO")
        self.setFixedSize(400, 350)
        self.setModal(True)
        self.bd = Conexion().obtener_conexion()
        
        # Variables de control
        self.id_usuario_local = None
        self.palabras_correctas = {} # Guardará {posicion: palabra}
        
        self.init_ui()

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)

        # --- FASE 1: IDENTIFICACIÓN ---
        self.etiqueta_instruccion = QLabel("Introduzca su correo electrónico para iniciar el desafío:")
        self.etiqueta_instruccion.setWordWrap(True)
        self.layout_principal.addWidget(self.etiqueta_instruccion)

        self.entrada_email = QLineEdit()
        self.entrada_email.setPlaceholderText("correo@ejemplo.com")
        self.layout_principal.addWidget(self.entrada_email)

        self.btn_verificar_mail = QPushButton("Verificar Identidad")
        self.btn_verificar_mail.clicked.connect(self.preparar_desafio)
        self.layout_principal.addWidget(self.btn_verificar_mail)

        # --- FASE 2: EL DESAFÍO (Oculto al inicio) ---
        self.contenedor_desafio = QVBoxLayout()
        self.inputs_desafio = {} # Para guardar los QLineEdit de las palabras

        self.layout_principal.addLayout(self.contenedor_desafio)

        self.btn_validar_desafio = QPushButton("Confirmar Palabras")
        self.btn_validar_desafio.clicked.connect(self.verificar_respuestas)
        self.btn_validar_desafio.hide()
        self.btn_validar_desafio.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.layout_principal.addWidget(self.btn_validar_desafio)

    def preparar_desafio(self):
        email = self.entrada_email.text().strip()
        if not email: return

        cursor = self.bd.cursor(dictionary=True)
        try:
            # 1. Buscar si el usuario existe y es bibliotecario
            query_user = """
                SELECT u.id_usuario FROM usuarios u
                JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                WHERE u.email = %s AND p.nombre = 'Bibliotecario'
            """
            cursor.execute(query_user, (email,))
            usuario = cursor.fetchone()

            if not usuario:
                QMessageBox.warning(self, "Error", "Correo no reconocido o no tiene privilegios de Bibliotecario.")
                return

            self.id_usuario_local = usuario['id_usuario']

            # 2. Obtener los 12 índices
            cursor.execute("SELECT indices_palabras FROM seguridad_recuperacion WHERE id_usuario = %s", (self.id_usuario_local,))
            resultado = cursor.fetchone()
            
            if not resultado:
                QMessageBox.critical(self, "Error Crítico", "No se encontraron llaves de recuperación para este usuario.")
                return

            indices = [int(i.strip()) for i in resultado['indices_palabras'].split(",")]

            # 3. Elegir 3 posiciones únicas (0 a 11)
            posiciones_elegidas = random.sample(range(12), 3)
            posiciones_elegidas.sort()

            # 4. Traducir esas 3 posiciones a palabras reales
            for pos in posiciones_elegidas:
                id_palabra_bd = indices[pos]
                cursor.execute("SELECT palabra FROM param_diccionario_seguridad WHERE id_palabra = %s", (id_palabra_bd,))
                palabra = cursor.fetchone()['palabra']
                self.palabras_correctas[pos + 1] = palabra # Guardamos posición humana (1-12)

            # 5. Cambiar la interfaz al modo desafío
            self.mostrar_interfaz_desafio()

        except Exception as e:
            QMessageBox.critical(self, "Error de DB", str(e))
        finally:
            cursor.close()

    def mostrar_interfaz_desafio(self):
        # Limpiar y ocultar mail
        self.entrada_email.hide()
        self.btn_verificar_mail.hide()
        self.etiqueta_instruccion.setText("Desafío de seguridad: Ingrese las palabras solicitadas de su lista de recuperación.")

        # Crear los campos para las 3 palabras
        for pos in self.palabras_correctas.keys():
            lbl = QLabel(f"Palabra número {pos}:")
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.Password) # Privacidad al escribir
            self.contenedor_desafio.addWidget(lbl)
            self.contenedor_desafio.addWidget(edit)
            self.inputs_desafio[pos] = edit

        self.btn_validar_desafio.show()

    def verificar_respuestas(self):
        aciertos = 0
        for pos, palabra_real in self.palabras_correctas.items():
            if self.inputs_desafio[pos].text().strip().lower() == palabra_real.lower():
                aciertos += 1
        
        if aciertos == 3:
            QMessageBox.information(self, "Éxito", "Identidad confirmada. Acceso concedido.")
            self.accept() # Esto devuelve QDialog.Accepted (True)
        else:
            QMessageBox.warning(self, "Fallo de Seguridad", "Las palabras no coinciden. El proceso se cancelará.")
            self.reject() # Esto devuelve QDialog.Rejected (False)

# --- BLOQUE DE EJECUCIÓN INDEPENDIENTE ---
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # Ajuste de contraste: Forzamos el color del texto a negro (#000000)
    app.setStyleSheet("""
        QWidget { 
            background-color: #E0E0E0; 
            color: #000000; 
            font-family: 'Segoe UI'; 
        }
        QLabel { 
            color: #000000; 
        }
        QPushButton { 
            background-color: #8da9d8; 
            color: #000000; 
            padding: 8px; 
            border-radius: 4px; 
            font-weight: bold; 
        }
        QLineEdit { 
            background-color: white; 
            color: #000000; 
            border: 1px solid #999999; 
            padding: 5px; 
        }
    """)

    ventana_prueba = ValidadorRecuperacion()
    if ventana_prueba.exec():
        print("Resultado: ÉXITO")
    else:
        print("Resultado: FALLO")
    
    sys.exit()