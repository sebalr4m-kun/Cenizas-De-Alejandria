# ==========================================
# Archivo: PrestamoModel_2.py
# ==========================================
from Modulos.Config import Conexion

class PrestamoModel:
    def __init__(self):
        self.conexion_obj = Conexion()
        self.bd = self.conexion_obj.obtener_conexion()

    def obtener_todos(self):
        """Obtiene el listado general de conjuntos de préstamo."""
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
            SELECT 
                p.id_prestamo,
                p.id_usuario,
                u.nombre AS usuario_nombre,
                u.email AS usuario_email,
                DATE_FORMAT(p.fecha_prestamo, '%Y-%m-%d %H:%i') AS fecha_prestamo,
                p.estado_prestamo,
                COUNT(d.id_detalle) AS total_items,
                SUM(CASE WHEN d.estado_item = 'DEVUELTO' THEN 1 ELSE 0 END) AS items_devueltos
            FROM prestamos p
            LEFT JOIN usuarios u ON p.id_usuario = u.id_usuario
            LEFT JOIN detalle_prestamo d ON p.id_prestamo = d.id_prestamo
            GROUP BY p.id_prestamo
            ORDER BY p.id_prestamo DESC
        """
        try:
            cursor.execute(consulta)
            return cursor.fetchall()
        finally:
            cursor.close()

    def obtener_usuarios_elegibles(self):
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        try:
            # FIX APLICADO: La columna correcta según la base de datos es estado_cuenta y su valor 'ACTIVA'
            cursor.execute("SELECT id_usuario, nombre, email FROM usuarios WHERE estado_cuenta = 'ACTIVA' ORDER BY nombre")
            return cursor.fetchall()
        finally:
            cursor.close()

    def obtener_tipos_insumo(self):
        """Categorías registradas en parámetros."""
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_tipo_insumo, nombre FROM param_tipos_insumo WHERE estado = 'ACTIVO' ORDER BY nombre")
            return cursor.fetchall()
        finally:
            cursor.close()

    def obtener_insumos_disponibles(self):
        """Obtiene TODOS los insumos disponibles de una sola vez, extrayendo también su id_tipo_insumo para filtro visual."""
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        try:
            consulta = "SELECT id_insumo, id_tipo_insumo, clave_runa, titulo FROM insumos WHERE estado = 'DISPONIBLE' ORDER BY titulo"
            cursor.execute(consulta)
            return cursor.fetchall()
        finally:
            cursor.close()

    def obtener_detalles_prestamo(self, id_prestamo):
        """Obtiene los libros/insumos asociados a un préstamo específico."""
        self.bd.commit()
        cursor = self.bd.cursor(dictionary=True)
        consulta = """
            SELECT 
                d.id_detalle,
                d.id_insumo,
                i.clave_runa,
                i.titulo,
                d.estado_item,
                DATE_FORMAT(d.fecha_devolucion, '%Y-%m-%d %H:%i') AS fecha_devolucion
            FROM detalle_prestamo d
            INNER JOIN insumos i ON d.id_insumo = i.id_insumo
            WHERE d.id_prestamo = %s
            ORDER BY i.titulo
        """
        try:
            cursor.execute(consulta, (id_prestamo,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def registrar_prestamo_conjunto(self, id_usuario, lista_id_insumos):
        """Crea un nuevo préstamo cabecera e inserta múltiples ítems en el detalle."""
        cursor = self.bd.cursor()
        try:
            cursor.execute("INSERT INTO prestamos (id_usuario, estado_prestamo) VALUES (%s, 'ACTIVO')", (id_usuario,))
            id_prestamo = cursor.lastrowid

            for id_insumo in lista_id_insumos:
                cursor.execute(
                    "INSERT INTO detalle_prestamo (id_prestamo, id_insumo, estado_item) VALUES (%s, %s, 'PRESTADO')",
                    (id_prestamo, id_insumo)
                )

            self.bd.commit()
            return id_prestamo
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()

    def procesar_devolucion_parcial(self, id_prestamo, lista_id_detalles_devueltos):
        """
        Marca ítems seleccionados como DEVUELTO. Si todos los ítems del préstamo 
        se encuentran devueltos, cierra la transacción general.
        """
        cursor = self.bd.cursor()
        try:
            if lista_id_detalles_devueltos:
                formato = ','.join(['%s'] * len(lista_id_detalles_devueltos))
                consulta = f"""
                    UPDATE detalle_prestamo 
                    SET estado_item = 'DEVUELTO', fecha_devolucion = CURRENT_TIMESTAMP 
                    WHERE id_detalle IN ({formato}) AND estado_item = 'PRESTADO'
                """
                cursor.execute(consulta, tuple(lista_id_detalles_devueltos))

            # Verificar si quedan ítems pendientes en este conjunto
            cursor.execute(
                "SELECT COUNT(*) FROM detalle_prestamo WHERE id_prestamo = %s AND estado_item = 'PRESTADO'", 
                (id_prestamo,)
            )
            pendientes = cursor.fetchone()[0]

            if pendientes == 0:
                cursor.execute(
                    "UPDATE prestamos SET estado_prestamo = 'DEVUELTO', fecha_devolucion_real = CURRENT_TIMESTAMP WHERE id_prestamo = %s",
                    (id_prestamo,)
                )

            self.bd.commit()
            return pendientes == 0
        except Exception as e:
            self.bd.rollback()
            raise e
        finally:
            cursor.close()