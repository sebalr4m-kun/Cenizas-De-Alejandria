================================================================================
 DEPENDENCIAS PYTHON - SISTEMA DE GESTIÓN DE BIBLIOTECA (MATEO11-15)
 Autor: Nanam | Fecha: 25 de noviembre de 2025
 Python: 3.13 | Entorno: XAMPP + MySQL
================================================================================

INSTALACIÓN RÁPIDA (una línea):
pip install PySide6 mysql-connector-python pandas openpyxl

--------------------------------------------------------------------------------
1. PySide6
--------------------------------------------------------------------------------
COMANDO:
    pip install PySide6

VERSIÓN RECOMENDADA:
    PySide6>=6.7.0

DESCRIPCIÓN:
    Framework oficial de Qt para Python. Permite crear interfaces gráficas 
    nativas, modernas y multiplataforma (Windows, macOS, Linux).

USO EN EL PROYECTO:
    - MainWindow, LoginDialog, QTableWidget, QPushButton, QComboBox, etc.
    - Todo el frontend: pestañas, formularios, tablas, estilos QSS.
    - Reemplaza a PyQt6 (licencia más restrictiva).

--------------------------------------------------------------------------------
2. mysql-connector-python
--------------------------------------------------------------------------------
COMANDO:
    pip install mysql-connector-python

VERSIÓN RECOMENDADA:
    mysql-connector-python>=8.4.0

DESCRIPCIÓN:
    Conector oficial de MySQL para Python. Permite conexión segura y eficiente
    a bases de datos MySQL/MariaDB sin dependencias externas.

USO EN EL PROYECTO:
    - Clase Conexion en Modulos/Config.py
    - Ejecuta todas las consultas: SELECT, INSERT, UPDATE, DELETE
    - Soporta cursores con diccionario (dictionary=True)
    - Manejo de errores y reconexión automática

--------------------------------------------------------------------------------
3. pandas (requerido para exportar reportes)
--------------------------------------------------------------------------------
COMANDO:
    pip install pandas

DESCRIPCIÓN:
    Librería para manipulación y análisis de datos. Permite crear y exportar
    DataFrames a Excel y CSV de manera sencilla.

USO EN EL PROYECTO:
    - Exportación de datos de todos los apartados a archivos Excel (.xlsx)
    - Generación de reportes multi-hoja con pandas.ExcelWriter

--------------------------------------------------------------------------------
4. openpyxl (requerido para pandas.ExcelWriter)
--------------------------------------------------------------------------------
COMANDO:
    pip install openpyxl

DESCRIPCIÓN:
    Motor para leer y escribir archivos Excel (.xlsx) desde Python.

USO EN EL PROYECTO:
    - Exportación de reportes Excel con pandas

================================================================================
DEPENDENCIAS OPCIONALES
================================================================================

5. python-dotenv (opcional - para variables de entorno)
    pip install python-dotenv
    → Si quieres mover credenciales DB a un archivo .env

================================================================================
VERIFICAR INSTALACIÓN
================================================================================

EJECUTA EN CMD:
    pip list | findstr "PySide6 mysql pandas openpyxl"

SALIDA ESPERADA:
    PySide6                  6.7.3
    mysql-connector-python   8.4.0
    pandas                   2.2.2
    openpyxl                 3.1.2

================================================================================
ARCHIVO requirements.txt (RECOMENDADO)
================================================================================

CREA UN ARCHIVO: requirements.txt
CONTENIDO:
    PySide6>=6.7.0
    mysql-connector-python>=8.4.0
    pandas>=2.2.2
    openpyxl>=3.1.2

LUEGO INSTALA CON:
    pip install -r requirements.txt

================================================================================
NOTAS IMPORTANTES
================================================================================

- NO uses PyQt6 → licencia GPL te obliga a abrir tu código.
- PySide6 es idéntico en API pero con licencia LGPL (más flexible).
- mysql-connector-python es puro Python → no necesitas compiladores.
- pandas y openpyxl son necesarios para exportar a Excel.
- Todas las librerías son compatibles con Python 3.13 (noviembre 2025).

================================================================================
 FUNCIONALIDADES DESTACADAS DEL SISTEMA
================================================================================

- Inicio de sesión seguro para bibliotecarios y modo invitado.
- Gestión completa de usuarios, insumos, libros, préstamos y parámetros.
- Actualización en cascada de títulos y stock de libros en insumos.
- Exportación de todos los datos visibles a un solo archivo Excel multi-hoja.
- Borrado permanente de cualquier unidad por ID usando el formato "ID###".
- Mensaje explicativo sobre la función de borrado en todos los formularios.
- Los campos de ID permiten escribir el carácter "#".
- Los usuarios eliminados no pueden editarse ni verse en la pantalla de usuarios.
- Sincronización automática de vistas tras cualquier operación.
- Consultas SQL optimizadas con JOIN para mostrar información completa.
- Interfaz moderna y responsiva con estilos personalizados.

================================================================================
 SISTEMA DE GESTIÓN DE BIBLIOTECA - MATEO11-15
 CONSULTAS SQL POR MÓDULO
 Autor: Nanam | Fecha: 27 de noviembre de 2025
================================================================================

--------------------------------------------------------------------------------
 MÓDULO: LOGIN (MainExample.py)
--------------------------------------------------------------------------------

1. Verificar si existe al menos un bibliotecario activo
    SELECT COUNT(*) FROM usuarios u
    JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
    WHERE p.nombre = 'Bibliotecario' AND u.estado_cuenta = 'ACTIVA'

2. Validar credenciales de login (por nombre y contraseña)
    SELECT 1 FROM usuarios u
    JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
    WHERE u.nombre = %s AND u.contraseña = %s 
      AND p.nombre = 'Bibliotecario' AND u.estado_cuenta = 'ACTIVA'
    LIMIT 1

================================================================================
 MÓDULO: USUARIOS (UsuarioController.py)
================================================================================

3. Listar todos los usuarios con tipo y estado
    SELECT u.id_usuario AS ID, u.nombre AS Nombre, u.email AS Email, 
           p.nombre AS 'Tipo Cuenta', u.estado_cuenta AS Estado
    FROM usuarios u 
    JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
    WHERE p.estado = 'ACTIVO' AND u.estado_cuenta != 'ELIMINADA'

4. Guardar/Actualizar usuario
    UPDATE usuarios SET nombre=%s, email=%s, id_tipo_usuario=%s, estado_cuenta=%s 
    WHERE id_usuario=%s

    INSERT INTO usuarios (nombre, email, id_tipo_usuario, estado_cuenta, contraseña) 
    VALUES (%s, %s, %s, %s, %s)

5. Borrado permanente de usuario por ID
    DELETE FROM usuarios WHERE id_usuario=%s

================================================================================
 MÓDULO: INSUMOS (InsumoController.py)
 (Usa 'clave_runa' como identificador único de la unidad física)
================================================================================

6. Listar todos los insumos con categoría y estado (excluye INACTIVA de la vista)
    SELECT i.titulo AS 'Titulo', 
           i.clave_runa AS 'Clave RUNA', 
           COALESCE(t.nombre, 'Sin categoría') AS Categoria,
           i.estado AS Estado, 
           DATE_FORMAT(i.fecha_adquisicion, '%Y-%m-%d') AS Adquisicion,
           i.id_tipo_insumo
    FROM insumos i
    LEFT JOIN param_tipos_insumo t ON i.id_tipo_insumo = t.id_tipo_insumo
    WHERE i.estado != 'INACTIVA' 
    ORDER BY i.titulo

7. Obtener un insumo por Clave RUNA
    SELECT * FROM insumos WHERE clave_runa=%s

8. Guardar/Actualizar insumo (incluye edición de título y metadatos)
    -- Actualizar:
    UPDATE insumos SET estado=%s, titulo=%s, id_tipo_insumo=%s, fecha_adquisicion=%s
    WHERE clave_runa=%s

    -- Insertar (Crear nuevo insumo general):
    INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa)
    VALUES (%s, %s, %s, %s, %s)

9. Borrado permanente de insumo (unidad física) por Clave RUNA
    DELETE FROM insumos WHERE clave_runa=%s

================================================================================
 MÓDULO: LIBROS (LibroController.py)
 (Incluye conteo de stock y eliminación en cascada)
================================================================================

10. Listar libros con autores, editoriales, categorías, géneros, stock y disponibles (Conteos a Nivel de Frontend)
    SELECT l.id_libro AS ID_Libro, l.titulo AS Título, l.isbn AS ISBN,
           GROUP_CONCAT(DISTINCT a.nombre_completo) AS Autor,
           GROUP_CONCAT(DISTINCT e.nombre_editorial) AS Editorial,
           GROUP_CONCAT(DISTINCT c.nombre_categoria) AS Categoría,
           GROUP_CONCAT(DISTINCT g.nombre_genero) AS Género,
           COALESCE(COUNT(i.clave_runa), 0) AS 'Stock Total',
           COALESCE(SUM(CASE WHEN i.estado = 'DISPONIBLE' THEN 1 ELSE 0 END), 0) AS Disponibles
    FROM libros l
    LEFT JOIN libro_autor la ON l.id_libro = la.id_libro
    LEFT JOIN autores a ON la.id_autor = a.id_autor
    LEFT JOIN libro_editorial le ON l.id_libro = le.id_libro
    LEFT JOIN editoriales e ON le.id_editorial = e.id_editorial
    LEFT JOIN libro_categoria lc ON l.id_libro = lc.id_libro
    LEFT JOIN categorias_catalogo c ON lc.id_categoria = c.id_categoria
    LEFT JOIN libro_genero lg ON l.id_libro = lg.id_libro
    LEFT JOIN generos g ON lg.id_genero = g.id_genero
    LEFT JOIN insumos i ON l.titulo = i.titulo AND i.id_tipo_insumo=3
    GROUP BY l.id_libro

11. Guardar/Actualizar libro + relaciones (incluye edición de título)
    -- Actualizar Metadatos del Libro:
    UPDATE libros SET titulo=%s, isbn=%s WHERE id_libro=%s

    -- Actualizar Título en Cascáda (Sincronización Insumos/Libros):
    UPDATE insumos SET titulo=%s WHERE id_tipo_insumo=3 AND titulo=%s

    -- Actualizar Relaciones (Ejemplo con autor, similar para editorial, categoría, género):
    DELETE FROM libro_autor WHERE id_libro=%s
    INSERT INTO libro_autor (id_libro, id_autor) VALUES (%s, %s) -- xN

12. Gestión de Stock de Unidades Físicas (Insumos tipo=3)
    -- Insertar nuevas unidades de libro (stock):
    INSERT INTO insumos (titulo, id_tipo_insumo, estado, fecha_adquisicion, clave_runa)
    VALUES (%s, 3, 'DISPONIBLE', %s, %s)

    -- Eliminar unidades sobrantes (por título, limitando la cantidad a eliminar):
    DELETE FROM insumos WHERE id_tipo_insumo=3 AND titulo=%s AND estado='DISPONIBLE' LIMIT %s

13. Borrado Permanente de Libro (Eliminación en Cascada)
    -- 1. Eliminar unidades físicas asociadas (insumos):
    DELETE FROM insumos WHERE id_tipo_insumo=3 AND titulo=%s
    
    -- 2. Eliminar Metadatos del Libro:
    DELETE FROM libros WHERE id_libro=%s
    
    -- Nota: Las tablas de relación (libro_autor, libro_editorial, etc.) deben tener ON DELETE CASCADE en la FK 'id_libro'.

================================================================================
 MÓDULO: PRÉSTAMOS (PrestamoController.py)
================================================================================

14. Listar préstamos activos y históricos
    SELECT p.id_prestamo AS ID_Préstamo,
           CONCAT(i.titulo, ' (RUNA: ', i.clave_runa, ')') AS 'Nombre Item/RUNA',
           CONCAT(u.nombre, ' (ID: ', p.id_usuario, ')') AS 'Nombre Usuario/ID',
           p.estado_prestamo AS Estado,
           CONCAT(DATE_FORMAT(p.fecha_prestamo, '%d/%m'), ' - ', 
                   IFNULL(DATE_FORMAT(p.fecha_devolucion_esperada, '%d/%m'), '')) AS Fechas
    FROM prestamos p
    JOIN usuarios u ON p.id_usuario = u.id_usuario
    JOIN insumos i ON p.clave_runa_insumo = i.clave_runa -- Asume cambio en tabla prestamos para usar RUNA
    
15. Registrar/Actualizar préstamo
    UPDATE prestamos SET id_usuario=%s, clave_runa_insumo=%s, fecha_devolucion_esperada=%s 
    WHERE id_prestamo=%s

    INSERT INTO prestamos (id_usuario, clave_runa_insumo, fecha_devolucion_esperada)
    VALUES (%s, %s, %s)

16. Borrado permanente de préstamo por ID
    DELETE FROM prestamos WHERE id_prestamo=%s

================================================================================
 MÓDULO: PARÁMETROS (ParametroController.py)
================================================================================

17. Listar todos los parámetros editables
    SELECT id_tipo_usuario AS ID, nombre AS Nombre, 'Tipo Usuario' AS Rubro, estado AS Estado FROM param_tipos_usuario
    UNION SELECT id_tipo_insumo, nombre, 'Tipo Insumo', estado FROM param_tipos_insumo
    UNION SELECT id_autor, nombre_completo, 'Autor', estado FROM param_autores
    UNION SELECT id_editorial, nombre_editorial, 'Editorial', estado FROM editoriales
    UNION SELECT id_categoria, nombre_categoria, 'Categoría (Libro)', estado FROM categorias_catalogo
    UNION SELECT id_genero, nombre_genero, 'Género', estado FROM generos
    ORDER BY Rubro, Nombre

18. Combo: Tipos de usuario activos
    SELECT id_tipo_usuario AS id, nombre FROM param_tipos_usuario WHERE estado = 'ACTIVO'

19. Combo: Tipos de insumo activos
    SELECT id_tipo_insumo AS id, nombre FROM param_tipos_insumo WHERE estado = 'ACTIVO'

20. Combo: Autores activos
    SELECT id_autor AS id, nombre_completo AS nombre FROM param_autores WHERE estado = 'ACTIVO'

21. Combo: Editoriales activas
    SELECT id_editorial AS id, nombre_editorial AS nombre FROM editoriales WHERE estado = 'ACTIVO'

22. Combo: Categorías activas
    SELECT id_categoria AS id, nombre_categoria AS nombre FROM categorias_catalogo WHERE estado = 'ACTIVO'

23. Combo: Géneros activos
    SELECT id_genero AS id, nombre_genero AS nombre FROM generos WHERE estado = 'ACTIVO'

24. Guardar parámetro genérico (ejemplo: autor)
    UPDATE param_autores SET nombre_completo=%s, estado=%s WHERE id_autor=%s
    INSERT INTO param_autores (nombre_completo, estado) VALUES (%s, %s)

25. Borrado permanente de parámetro por ID (ejemplo: autor)
    DELETE FROM param_autores WHERE id_autor=%s

================================================================================
 RESUMEN DE TABLAS CLAVE USADAS EN SELECT
================================================================================

-- Usuarios
SELECT * FROM usuarios;
SELECT * FROM param_tipos_usuario;

-- Libros e insumos
SELECT * FROM libros;
SELECT * FROM insumos;

-- Catálogo completo
SELECT * FROM libro_autor;
SELECT * FROM libro_editorial;
SELECT * FROM libro_categoria;
SELECT * FROM libro_genero;

-- Préstamos
SELECT * FROM prestamos;

-- Parámetros
SELECT * FROM param_autores;
SELECT * FROM editoriales;
SELECT * FROM categorias_catalogo;
SELECT * FROM generos;

================================================================================
 MENSAJE DE BORRADO PERMANENTE POR CLAVE
================================================================================

En todos los formularios de edición, aparece el mensaje:
    Función de borrado: CLAVE###

Para eliminar una unidad o registro, inserta el ID (o Clave RUNA) seguido de tres signos de numeral (###).
Ejemplo: Para un usuario, 123###. Para un insumo, ABCDZ###.

================================================================================
 FIN DEL DOCUMENTO
================================================================================

El sistema utiliza la función export_to_excel para capturar y guardar la información que se muestra en las listas de la pantalla, como usuarios, insumos y libros. El proceso comienza con la recolección de todos los datos visibles de las tablas de la interfaz. Luego, esta información se somete a una organización, donde se convierte en un formato de tabla digital conocido como DataFrame de pandas. Finalmente, para su guardado, se crea un único archivo Excel con múltiples pestañas, de modo que cada lista de datos se almacena en una hoja separada. Este archivo se ubica en la carpeta 'Exportaciones' e incluye la fecha y hora para facilitar su identificación.


-- =============================================================================
-- SISTEMA DE GESTIÓN DE BIBLIOTECA - RECONSTRUCCIÓN INTEGRAL
-- Protocolo: Soberanía de IDs y Referenciación por RUNA
-- Optimización: Soporte RBAC Modular Integrado (Ejemplo de Inicialización Completo)
-- =============================================================================

DROP DATABASE IF EXISTS bibliotecabd;
CREATE DATABASE bibliotecabd;
USE bibliotecabd;

-- -----------------------------------------------------------------------------
-- 1. TABLAS DE PARÁMETROS (Catálogos y Rubros)
-- -----------------------------------------------------------------------------

CREATE TABLE param_tipos_usuario (
    id_tipo_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    estado VARCHAR(10) DEFAULT 'ACTIVO',
    admitido TINYINT(1) DEFAULT 0, -- Switch maestro de acceso para el login
    permisos TEXT                  -- Contenedor JSON serializado para los checkboxes modulares
);

CREATE TABLE param_tipos_insumo (
    id_tipo_insumo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    estado VARCHAR(10) DEFAULT 'ACTIVO'
);

CREATE TABLE param_autores (
    id_autor INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL,
    estado VARCHAR(10) DEFAULT 'ACTIVO'
);

CREATE TABLE editoriales (
    id_editorial INT AUTO_INCREMENT PRIMARY KEY,
    nombre_editorial VARCHAR(100) NOT NULL,
    estado VARCHAR(10) DEFAULT 'ACTIVO'
);

CREATE TABLE categorias_catalogo (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre_categoria VARCHAR(50) NOT NULL,
    estado VARCHAR(10) DEFAULT 'ACTIVO'
);

CREATE TABLE generos (
    id_genero INT AUTO_INCREMENT PRIMARY KEY,
    nombre_genero VARCHAR(50) NOT NULL,
    estado VARCHAR(10) DEFAULT 'ACTIVO'
);

-- -----------------------------------------------------------------------------
-- 2. ENTIDADES PRINCIPALES
-- -----------------------------------------------------------------------------

-- Usuarios del sistema
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    id_tipo_usuario INT,
    contraseña VARCHAR(255),
    estado_cuenta VARCHAR(20) DEFAULT 'ACTIVA',
    FOREIGN KEY (id_tipo_usuario) REFERENCES param_tipos_usuario(id_tipo_usuario)
);

-- Metadatos de Libros
CREATE TABLE libros (
    id_libro INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    estado VARCHAR(10) DEFAULT 'ACTIVO'
);

-- Unidades Físicas (Insumos)
CREATE TABLE insumos (
    id_insumo INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    id_tipo_insumo INT,
    estado VARCHAR(20) DEFAULT 'DISPONIBLE',
    fecha_adquisicion DATE,
    clave_runa VARCHAR(50) UNIQUE NOT NULL,
    FOREIGN KEY (id_tipo_insumo) REFERENCES param_tipos_insumo(id_tipo_insumo)
);

-- -----------------------------------------------------------------------------
-- 3. RELACIONES MUCHOS A MUCHOS (Libros Metadatos)
-- -----------------------------------------------------------------------------

CREATE TABLE libro_autor (
    id_libro INT,
    id_autor INT,
    PRIMARY KEY (id_libro, id_autor),
    FOREIGN KEY (id_libro) REFERENCES libros(id_libro) ON DELETE CASCADE,
    FOREIGN KEY (id_autor) REFERENCES param_autores(id_autor) ON DELETE CASCADE
);

CREATE TABLE libro_editorial (
    id_libro INT,
    id_editorial INT,
    PRIMARY KEY (id_libro, id_editorial),
    FOREIGN KEY (id_libro) REFERENCES libros(id_libro) ON DELETE CASCADE,
    FOREIGN KEY (id_editorial) REFERENCES editoriales(id_editorial) ON DELETE CASCADE
);

CREATE TABLE libro_categoria (
    id_libro INT,
    id_categoria INT,
    PRIMARY KEY (id_libro, id_categoria),
    FOREIGN KEY (id_libro) REFERENCES libros(id_libro) ON DELETE CASCADE,
    FOREIGN KEY (id_categoria) REFERENCES categorias_catalogo(id_categoria) ON DELETE CASCADE
);

CREATE TABLE libro_genero (
    id_libro INT,
    id_genero INT,
    PRIMARY KEY (id_libro, id_genero),
    FOREIGN KEY (id_libro) REFERENCES libros(id_libro) ON DELETE CASCADE,
    FOREIGN KEY (id_genero) REFERENCES generos(id_genero) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 4. GESTIÓN DE PRÉSTAMOS
-- -----------------------------------------------------------------------------

CREATE TABLE prestamos (
    id_prestamo INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    id_insumo INT,
    fecha_prestamo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_devolucion_esperada DATE,
    estado_prestamo VARCHAR(20) DEFAULT 'ACTIVO',
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_insumo) REFERENCES insumos(id_insumo) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 5. DATOS DE INICIALIZACIÓN
-- -----------------------------------------------------------------------------

-- Tipos base requeridos con el mapeo completo de permisos serializados para el controlador
INSERT INTO param_tipos_usuario (nombre, estado, admitido, permisos) VALUES 
('Bibliotecario', 'ACTIVO', 1, '{"Usuarios": {"ver": true, "crear": true, "editar": true, "eliminar": true}, "Insumos": {"ver": true, "crear": true, "editar": true, "eliminar": true}, "Libros": {"ver": true, "crear": true, "editar": true, "eliminar": true}, "Prestamos": {"ver": true, "crear": true, "editar": true, "eliminar": true}, "Parametros": {"ver": true, "crear": true, "editar": true, "eliminar": true}}'), 
('Lector', 'ACTIVO', 1, '{"Usuarios": {"ver": false, "crear": false, "editar": false, "eliminar": false}, "Insumos": {"ver": true, "crear": false, "editar": false, "eliminar": false}, "Libros": {"ver": true, "crear": false, "editar": false, "eliminar": false}, "Prestamos": {"ver": true, "crear": true, "editar": false, "eliminar": false}, "Parametros": {"ver": false, "crear": false, "editar": false, "eliminar": false}}');

INSERT INTO param_tipos_insumo (id_tipo_insumo, nombre, estado) VALUES (1, 'Papelería', 'ACTIVO'), (2, 'Mobiliario', 'ACTIVO'), (3, 'Libro', 'ACTIVO');

-- -----------------------------------------------------------------------------
-- 6. PROTOCOLO DE RECUPERACIÓN (SISTEMA DE PALABRAS MAESTRAS)
-- -----------------------------------------------------------------------------

CREATE TABLE param_diccionario_seguridad (
    id_palabra INT PRIMARY KEY AUTO_INCREMENT,
    palabra VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE seguridad_recuperacion (
    id_recuperacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT UNIQUE,
    indices_palabras TEXT NOT NULL,
    salt_secreto VARCHAR(64),
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- =============================================================================
-- POBLADO MASIVO DEL DICCIONARIO DE SEGURIDAD (1000 PALABRAS)
-- Protocolo: Seguridad Persistente - Nivel Bibliotecario
-- =============================================================================

DROP TABLE IF EXISTS param_diccionario_seguridad;

CREATE TABLE param_diccionario_seguridad (
    id_palabra INT PRIMARY KEY AUTO_INCREMENT,
    palabra VARCHAR(50) NOT NULL UNIQUE
);

INSERT IGNORE INTO param_diccionario_seguridad (palabra) VALUES
('Alfa'), ('Beta'), ('Gamma'), ('Delta'), ('Epsilon'), ('Zeta'), ('Eta'), ('Theta'), ('Iota'), ('Kappa'),
('Lambda'), ('Mu'), ('Nu'), ('Xi'), ('Omicron'), ('Pi'), ('Rho'), ('Sigma'), ('Tau'), ('Upsilon'),
('Phi'), ('Chi'), ('Psi'), ('Omega'), ('Quasar'), ('Pulsar'), ('Nebulosa'), ('Galaxia'), ('Andromeda'), ('Cenit'),
('Nadir'), ('Orbita'), ('Eclipse'), ('Cometa'), ('Asteroide'), ('Planeta'), ('Estrella'), ('Constelacion'), ('Cosmos'), ('Vacio'),
('Gravedad'), ('Singularidad'), ('Horizonte'), ('Materia'), ('Antimateria'), ('Proton'), ('Neutron'), ('Electron'), ('Quark'), ('Boson'),
('Hidrogeno'), ('Helio'), ('Litio'), ('Berilio'), ('Boro'), ('Carbono'), ('Nitrogeno'), ('Oxigeno'), ('Fluor'), ('Neon'),
('Sodio'), ('Magnesio'), ('Aluminio'), ('Silicio'), ('Fosforo'), ('Azufre'), ('Cloro'), ('Argon'), ('Potasio'), ('Calcio'),
('Escandio'), ('Titanio'), ('Vanadio'), ('Cromo'), ('Manganeso'), ('Hierro'), ('Cobalto'), ('Niquel'), ('Cobre'), ('Zinc'),
('Galio'), ('Germanio'), ('Arsenico'), ('Selenio'), ('Bromo'), ('Kripton'), ('Rubidio'), ('Estroncio'), ('Itrio'), ('Zirconio'),
('Niobio'), ('Molibdeno'), ('Tecnecio'), ('Rutenio'), ('Rodio'), ('Paladio'), ('Plata'), ('Cadmio'), ('Indio'), ('Estaño'),
('Antimonio'), ('Telurio'), ('Yodo'), ('Xenon'), ('Cesio'), ('Bario'), ('Lantano'), ('Cerio'), ('Praseodimio'), ('Neodimio'),
('Prometio'), ('Samario'), ('Europio'), ('Gadolinio'), ('Terbio'), ('Disprosio'), ('Holmio'), ('Erbio'), ('Tulio'), ('Iterbio'),
('Lutecio'), ('Hafnio'), ('Tantalio'), ('Wolframio'), ('Renio'), ('Osmio'), ('Iridio'), ('Platino'), ('Oro'), ('Mercurio'),
('Talio'), ('Plomo'), ('Bismuto'), ('Polonio'), ('Astato'), ('Radon'), ('Francio'), ('Radio'), ('Actinio'), ('Torio'),
('Protactinio'), ('Uranio'), ('Neptunio'), ('Plutonio'), ('Americio'), ('Curio'), ('Berkelio'), ('Californio'), ('Einstenio'), ('Fermio'),
('Algoritmo'), ('Binario'), ('Codigo'), ('Compilador'), ('Depuracion'), ('Encriptacion'), ('Framework'), ('Giga'), ('Hardware'), ('Interfaz'),
('Java'), ('Kernel'), ('Libreria'), ('Memoria'), ('Nodo'), ('Objeto'), ('Protocolo'), ('Query'), ('Red'), ('Servidor'),
('Token'), ('Usuario'), ('Variable'), ('Widget'), ('Xml'), ('Yotta'), ('Zip'), ('Ciber'), ('Datos'), ('Enlace'),
('Fila'), ('Gestor'), ('Hilo'), ('Indice'), ('Jerarquia'), ('Kilobyte'), ('Logica'), ('Matriz'), ('Nube'), ('Operador'),
('Paquete'), ('Rutina'), ('Script'), ('Terminal'), ('Unidad'), ('Vector'), ('Web'), ('Socket'), ('Puerto'), ('Buffer'),
('Cache'), ('Daemon'), ('Ethernet'), ('Firewall'), ('Gateway'), ('Hash'), ('Intranet'), ('Json'), ('Latencia'), ('Modulo'),
('Null'), ('Octeto'), ('Pipeline'), ('Queue'), ('Recursion'), ('Stack'), ('Thread'), ('Uplink'), ('Virtual'), ('Wifi'),
('Asincrono'), ('Booleano'), ('Clase'), ('Despliegue'), ('Entorno'), ('Funcion'), ('Git'), ('Host'), ('Iteracion'), ('Joystick'),
('Linux'), ('Metodo'), ('Navegador'), ('Origen'), ('Puntero'), ('Repositorio'), ('Sincronia'), ('Trama'), ('Umbral'), ('Validacion'),
('Backend'), ('Frontend'), ('Fullstack'), ('Docker'), ('Kubernetes'), ('Python'), ('Django'), ('Flask'), ('Sqlite'), ('MariaDB'),
('Postgres'), ('Redis'), ('Mongo'), ('API'), ('Rest'), ('Soap'), ('Html'), ('Css'), ('Javascript'), ('Typescript'),
('React'), ('Angular'), ('Vue'), ('Svelte'), ('Node'), ('Express'), ('Npm'), ('Pip'), ('Conda'), ('Linux'),
('Ubuntu'), ('Debian'), ('Fedora'), ('Arch'), ('Kali'), ('Windows'), ('MacOS'), ('Android'), ('Ios'), ('Kernel'),
('Shell'), ('Bash'), ('Zsh'), ('PowerShell'), ('Ssh'), ('Ftp'), ('Http'), ('Https'), ('Tls'), ('Ssl'),
('Dns'), ('Dhcp'), ('Ipv4'), ('Ipv6'), ('Subred'), ('Mascara'), ('Router'), ('Switch'), ('Modem'), ('Antena'),
('Dragon'), ('Elfo'), ('Enano'), ('Orco'), ('Gnomo'), ('Troll'), ('Gigante'), ('Hada'), ('Duende'), ('Sirena'),
('Centauro'), ('Pegaso'), ('Quimera'), ('Hidra'), ('Kraken'), ('Fenix'), ('Grifo'), ('Esfinge'), ('Minotauro'), ('Basilisco'),
('Vampiro'), ('Licantropo'), ('Espectro'), ('Zombi'), ('Esqueleto'), ('Golem'), ('Elemental'), ('Demonio'), ('Angel'), ('Avatar'),
('Mago'), ('Brujo'), ('Hechicero'), ('Clerigo'), ('Paladin'), ('Guerrero'), ('Picaro'), ('Explorador'), ('Barbaro'), ('Bardo'),
('Druida'), ('Monje'), ('Alquimista'), ('Nigromante'), ('Invocador'), ('Runas'), ('Grimorio'), ('Baculo'), ('Cetro'), ('Amuleto'),
('Espada'), ('Escudo'), ('Hacha'), ('Lanza'), ('Arco'), ('Ballesta'), ('Daga'), ('Martillo'), ('Maza'), ('Armadura'),
('Casco'), ('Guantelete'), ('Botas'), ('Capa'), ('Anillo'), ('Collar'), ('Pocion'), ('Elixir'), ('Pergamino'), ('Reliquia'),
('Mazmorra'), ('Castillo'), ('Torre'), ('Cueva'), ('Bosque'), ('Montaña'), ('Pantano'), ('Desierto'), ('Oceano'), ('Abismo'),
('Reino'), ('Imperio'), ('Alianza'), ('Gremio'), ('Taberna'), ('Mercado'), ('Templo'), ('Ruinas'), ('Portal'), ('Dimension'),
('Destino'), ('Profecia'), ('Leyenda'), ('Mito'), ('Fabula'), ('Hechizo'), ('Maldicion'), ('Bendicion'), ('Milagro'), ('Enigma'),
('Aura'), ('Mana'), ('Energia'), ('Esencia'), ('Espiritu'), ('Alma'), ('Sombra'), ('Luz'), ('Fuego'), ('Agua'),
('Tierra'), ('Aire'), ('Rayo'), ('Hielo'), ('Veneno'), ('Acido'), ('Metal'), ('Cristal'), ('Arena'), ('Lodo'),
('Valquiria'), ('Odín'), ('Thor'), ('Loki'), ('Zeus'), ('Hades'), ('Poseidon'), ('Ares'), ('Atenea'), ('Artemisa'),
('Apolo'), ('Afrodita'), ('Hermes'), ('Hefesto'), ('Dionisio'), ('Hera'), ('Demeter'), ('Persefone'), ('Anubis'), ('Osiris'),
('Isis'), ('Horus'), ('Ra'), ('Seth'), ('Thot'), ('Bastet'), ('Sobek'), ('Sekhmet'), ('Nilo'), ('Piramide'),
('Leon'), ('Tigre'), ('Lobo'), ('Oso'), ('Aguila'), ('Halcon'), ('Buho'), ('Cuervo'), ('Serpiente'), ('Cocodrilo'),
('Tiburon'), ('Ballena'), ('Delfin'), ('Pulpo'), ('Calamar'), ('Medusa'), ('Coral'), ('Tortuga'), ('Rana'), ('Salamandra'),
('Elefante'), ('Rinoceronte'), ('Hipopotamo'), ('Jirafa'), ('Zebra'), ('Caballo'), ('Toro'), ('Ciervo'), ('Zorro'), ('Conejo'),
('Ardilla'), ('Raton'), ('Murcielago'), ('Escorpion'), ('Araña'), ('Hormiga'), ('Abeja'), ('Mariposa'), ('Libelula'), ('Escarabajo'),
('Roble'), ('Pino'), ('Cedro'), ('Secuoya'), ('Sauce'), ('Abeto'), ('Palmera'), ('Bambu'), ('Helecho'), ('Musgo'),
('Rosa'), ('Lirio'), ('Tulipan'), ('Orquidea'), ('Girasol'), ('Loto'), ('Margarita'), ('Lavanda'), ('Menta'), ('Canela'),
('Selva'), ('Bosque'), ('Tundra'), ('Estepa'), ('Sabana'), ('Pradera'), ('Valle'), ('Cañon'), ('Acantilado'), ('Cueva'),
('Isla'), ('Archipielago'), ('Peninsula'), ('Continente'), ('Montaña'), ('Volcan'), ('Glaciar'), ('Rio'), ('Lago'), ('Laguna'),
('Cascada'), ('Delta'), ('Estuario'), ('Arrecife'), ('Abismo'), ('Fosa'), ('Playa'), ('Duna'), ('Oasis'), ('Geiser'),
('Clima'), ('Tiempo'), ('Viento'), ('Lluvia'), ('Nieve'), ('Granizo'), ('Tormenta'), ('Rayo'), ('Trueno'), ('Niebla'),
('Arcoiris'), ('Aurora'), ('Tornado'), ('Huracan'), ('Tsunami'), ('Terremoto'), ('Erupcion'), ('Marea'), ('Corriente'), ('Ola'),
('Cuarzo'), ('Diamante'), ('Rubi'), ('Esmeralda'), ('Zafiro'), ('Topacio'), ('Amatista'), ('Opalo'), ('Jade'), ('Obsidiana'),
('Granito'), ('Basalto'), ('Marmol'), ('Pizarra'), ('Caliza'), ('Arenisca'), ('Arcilla'), ('Arena'), ('Grava'), ('Lava'),
('Magma'), ('Ceniza'), ('Fosil'), ('Ambar'), ('Carbon'), ('Petroleo'), ('Gas'), ('Cristal'), ('Vidrio'), ('Espejo'),
('Norte'), ('Sur'), ('Este'), ('Oeste'), ('Brujula'), ('Mapa'), ('Globo'), ('Atlas'), ('Ruta'), ('Sendero'),
('Axioma'), ('Teoria'), ('Hipotesis'), ('Metodo'), ('Analisis'), ('Sintesis'), ('Logica'), ('Etica'), ('Moral'), ('Estetica'),
('Dualidad'), ('Paradoja'), ('Enigma'), ('Misterio'), ('Verdad'), ('Realidad'), ('Ilusion'), ('Sueño'), ('Mente'), ('Conciencia'),
('Tiempo'), ('Espacio'), ('Eternidad'), ('Infinito'), ('Caos'), ('Orden'), ('Entropia'), ('Equilibrio'), ('Armonia'), ('Destino'),
('Azar'), ('Suerte'), ('Fortuna'), ('Karma'), ('Zenit'), ('Nadir'), ('Apogeo'), ('Ocaso'), ('Alba'), ('Crepusculo'),
('Justicia'), ('Libertad'), ('Poder'), ('Gloria'), ('Honor'), ('Lealtad'), ('Valor'), ('Miedo'), ('Ira'), ('Paz'),
('Amor'), ('Odio'), ('Deseo'), ('Dolor'), ('Placer'), ('Duda'), ('Fe'), ('Esperanza'), ('Olvido'), ('Memoria'),
('Razon'), ('Instinto'), ('Intuicion'), ('Genio'), ('Talento'), ('Sapiencia'), ('Sabiduria'), ('Ignorancia'), ('Locura'), ('Cura'),
('Energia'), ('Fuerza'), ('Inercia'), ('Impulso'), ('Presion'), ('Calor'), ('Frio'), ('Luz'), ('Sonido'), ('Eco'),
('Vibracion'), ('Frecuencia'), ('Onda'), ('Espectro'), ('Reflexion'), ('Refraccion'), ('Difraccion'), ('Polaridad'), ('Magnetismo'), ('Voltaje'),
('Amperaje'), ('Ohmios'), ('Vatios'), ('Julios'), ('Caloria'), ('Grado'), ('Angulo'), ('Radio'), ('Diametro'), ('Perimetro'),
('Area'), ('Volumen'), ('Masa'), ('Peso'), ('Densidad'), ('Presion'), ('Fluido'), ('Gas'), ('Solido'), ('Liquido'),
('Plasma'), ('Atomo'), ('Molecula'), ('Enlace'), ('Reaccion'), ('Catalisis'), ('Enzima'), ('Proteina'), ('Adn'), ('Arn'),
('Celula'), ('Nucleo'), ('Organo'), ('Tejido'), ('Cuerpo'), ('Vida'), ('Muerte'), ('Evolucion'), ('Especie'), ('Mutacion'),
('Gen'), ('Cromosoma'), ('Herencia'), ('Clon'), ('Hibrido'), ('Virus'), ('Bacteria'), ('Hongo'), ('Alga'), ('Parasito'),
('Salud'), ('Veneno'), ('Antidoto'), ('Vacuna'), ('Suero'), ('Sangre'), ('Linfa'), ('Nervio'), ('Cerebro'), ('Corazon'),
('Pulmon'), ('Higado'), ('Riñon'), ('Hueso'), ('Musculo'), ('Piel'), ('Ojo'), ('Oido'), ('Nariz'), ('Boca'),
('Voz'), ('Grito'), ('Susurro'), ('Silencio'), ('Riesgo'), ('Peligro'), ('Refugio'), ('Hogar'), ('Ciudad'), ('Pueblo'),
('Estado'), ('Nacion'), ('Mundo'), ('Tierra'), ('Luna'), ('Sol'), ('Marte'), ('Jupiter'), ('Saturno'), ('Urano'),
('Neptuno'), ('Pluton'), ('Sistema'), ('Orbita'), ('Vuelo'), ('Viaje'), ('Ruta'), ('Destino'), ('Llegada'), ('Partida'),
('Puerta'), ('Ventana'), ('Muro'), ('Techo'), ('Suelo'), ('Escalera'), ('Puente'), ('Tunel'), ('Camino'), ('Plaza'),
('Reloj'), ('Brujula'), ('Mapa'), ('Libro'), ('Pluma'), ('Tinta'), ('Papel'), ('Llave'), ('Cofre'), ('Candado'),
('Espejo'), ('Lampara'), ('Vela'), ('Antorcha'), ('Fuego'), ('Hielo'), ('Viento'), ('Piedra'), ('Madera'), ('Hierro'),
('Acero'), ('Bronce'), ('Plata'), ('Oro'), ('Joyel'), ('Corona'), ('Trono'), ('Cetro'), ('Escudo'), ('Espada'),
('Daga'), ('Arco'), ('Flecha'), ('Cuerda'), ('Red'), ('Ancla'), ('Barco'), ('Vela'), ('Timon'), ('Puerto'),
('Arena'), ('Polvo'), ('Ceniza'), ('Humo'), ('Nube'), ('Bruma'), ('Sombra'), ('Reflejo'), ('Destello'), ('Brillo'),
('Color'), ('Forma'), ('Textura'), ('Olor'), ('Sabor'), ('Sonido'), ('Ritmo'), ('Melodia'), ('Armonia'), ('Verso'),
('Rima'), ('Prosa'), ('Letra'), ('Palabra'), ('Frase'), ('Libro'), ('Pagina'), ('Tomo'), ('Saga'), ('Obra'),
('Arte'), ('Museo'), ('Teatro'), ('Cine'), ('Musica'), ('Danza'), ('Pintura'), ('Estatua'), ('Diseño'), ('Moda'),
('Juego'), ('Azar'), ('Dado'), ('Carta'), ('Ficha'), ('Tablero'), ('Pieza'), ('Jugada'), ('Turno'), ('Regla'),
('Punto'), ('Nivel'), ('Rango'), ('Clase'), ('Tipo'), ('Grupo'), ('Secta'), ('Orden'), ('Clan'), ('Logia'),
('Base'), ('Centro'), ('Eje'), ('Borde'), ('Limite'), ('Final'), ('Inicio'), ('Origen'), ('Meta'), ('Cima'),
('Fondo'), ('Lado'), ('Cara'), ('Angulo'), ('Vertice'), ('Plano'), ('Esfera'), ('Cubo'), ('Cono'), ('Cilindro'),
('Suma'), ('Resta'), ('Cifra'), ('Numero'), ('Cuenta'), ('Calculo'), ('Dato'), ('Bit'), ('Byte'), ('Chip'),
('Laser'), ('Radar'), ('Sonda'), ('Nave'), ('Motor'), ('Ala'), ('Rueda'), ('Engrane'), ('Piston'), ('Valvula'),
('Pila'), ('Cable'), ('Iman'), ('Polo'), ('Onda'), ('Faro'), ('Señal'), ('Pulso'), ('Frecuencia'), ('Ritmo'),
('Bomba'), ('Chispa'), ('Llama'), ('Gota'), ('Burbuja'), ('Rocio'), ('Escarcha'), ('Barro'), ('Polvo'), ('Paja'),
('Trigo'), ('Pan'), ('Vino'), ('Miel'), ('Sal'), ('Aceite'), ('Seda'), ('Lana'), ('Cuero'), ('Lino'),
('Nudo'), ('Lazo'), ('Hilo'), ('Aguja'), ('Tijera'), ('Pala'), ('Pico'), ('Sierra'), ('Clavo'), ('Tornillo'),
('Llave'), ('Martillo'), ('Pinza'), ('Yunque'), ('Fragua'), ('Horno'), ('Molino'), ('Rueda'), ('Pozo'), ('Torre'),
('Muro'), ('Foso'), ('Puente'), ('Camino'), ('Bosque'), ('Rio'), ('Valle'), ('Monte'), ('Cielo'), ('Universo'), 
('Umbra'), ('Ratio'), ('Magnum'), ('Opus'), ('Primus'), ('Ultima'), ('Dominus'), ('Imperium'), ('Libertas'), ('Veritas'), 
('Pax'), ('Bellum'), ('Fatum'), ('Tempus'), ('Spatium'), ('Codex'), ('Lex'), ('Vis'), ('Anima'), ('Corpus'), 
('Spiritus'), ('Terra'), ('Aqua'), ('Ignis'), ('Aer'), ('Aether'), ('Chaos'), ('Cosmos'), ('Mundus'), ('Stella'), 
('Luna'), ('Sol'), ('Nox'), ('Dies'), ('Vita'), ('Mors'), ('Scientia'), ('Sapientia'), ('Virtus'), ('Honor'), 
('Gloria'), ('Fides'), ('Spes'), ('Caritas'), ('Amor'), ('Odium'), ('Metus'), ('Ira'), ('Gaudium'), ('Dolor'), 
('Solitudo'), ('Silentium'), ('Clamor'), ('Vox'), ('Verbum'), ('Scriptura'), ('Littera'), ('Numerus'), ('Punctum'), 
('Linea'), ('Circulus'), ('Triangulum'), ('Quadratum'), ('Sphaera'), ('Finis'), ('Cyber'), ('Quantum'), ('Entropy'), 
('Parity'), ('Legacy'), ('Status'), ('System'), ('Root'), ('Admin'), ('Secure'), ('Void'), ('Null'), ('None'), 
('True'), ('False'), ('Link'), ('Flow');

-- Confirmación de carga
SELECT COUNT(*) FROM param_diccionario_seguridad;

-- -----------------------------------------------------------------------------
-- 7. MÓDULO DE AUDITORÍAS (Trazabilidad)
-- -----------------------------------------------------------------------------

CREATE TABLE param_acciones (
    id_accion INT AUTO_INCREMENT PRIMARY KEY,
    nombre_accion VARCHAR(50) NOT NULL,
    descripcion VARCHAR(150)
);

INSERT INTO param_acciones (id_accion, nombre_accion, descripcion) VALUES
(1, 'Crear', 'Inserción de nuevos registros'),
(2, 'Modificar', 'Actualización de registros existentes'),
(3, 'Borrado Lógico', 'Desactivación de registros sin eliminación física'),
(4, 'Borrado Físico', 'Eliminación permanente de registros'),
(5, 'Sesión', 'Inicio y cierre de sesión de usuarios');

CREATE TABLE auditorias (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    id_accion INT,
    modulo VARCHAR(50) NOT NULL,
    elemento TEXT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_accion) REFERENCES param_acciones(id_accion) ON DELETE RESTRICT
);