import sys
import os
import mysql.connector
from mysql.connector import Error
from PySide6.QtWidgets import QApplication, QMessageBox
from Modulos.Controllers.InicioSesionController import ControladorLogin
from Modulos.Views.MainWindow import VentanaPrincipal

# --- CONFIGURACIÓN DE COLORES Y ESTILOS (Vantablack / Alto Contraste) ---
ESTILO_GLOBAL = """
    QWidget { background-color: #FFFFFF; color: #000000; font-family: 'Segoe UI', Arial; }
    QLineEdit, QComboBox, QTableWidget, QDateEdit { 
        background-color: #FFFFFF; 
        color: #000000;
        border: 2px solid #000000; 
        border-radius: 4px; 
        padding: 6px; 
        font-weight: 600;
    }
    QPushButton { 
        background-color: #2C3E50; 
        color: #FFFFFF; 
        border: 2px solid #000000; 
        padding: 10px; 
        border-radius: 5px; 
        font-weight: 900; 
    }
    QPushButton:hover { background-color: #34495E; }
    QLabel { color: #000000; font-weight: 800; }
"""

# --- SCRIPT SQL INTEGRADO PARA RECONSTRUCCIÓN ---
SQL_RECONSTRUCCION = """
-- =============================================================================
-- SISTEMA DE GESTIÓN DE BIBLIOTECA - RECONSTRUCCIÓN INTEGRAL
-- Protocolo: Soberanía de IDs y Referenciación por RUNA
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
    estado VARCHAR(10) DEFAULT 'ACTIVO'
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
    estado VARCHAR(10) DEFAULT 'ACTIVO' -- Soluciona error anterior l.estado
);

-- Unidades Físicas (Insumos)
CREATE TABLE insumos (
    id_insumo INT AUTO_INCREMENT PRIMARY KEY, -- Clave primaria para lógica de código
    titulo VARCHAR(150) NOT NULL,
    id_tipo_insumo INT,
    estado VARCHAR(20) DEFAULT 'DISPONIBLE',
    fecha_adquisicion DATE,
    clave_runa VARCHAR(50) UNIQUE NOT NULL, -- Identificador para búsqueda de usuario
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
-- 4. GESTIÓN DE PRÉSTAMOS (Solución al error p.id_insumo)
-- -----------------------------------------------------------------------------

CREATE TABLE prestamos (
    id_prestamo INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    id_insumo INT, -- Se usa el ID para la relación interna
    fecha_prestamo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_devolucion_esperada DATE,
    estado_prestamo VARCHAR(20) DEFAULT 'ACTIVO',
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_insumo) REFERENCES insumos(id_insumo) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 5. DATOS DE INICIALIZACIÓN
-- -----------------------------------------------------------------------------

-- Tipos base requeridos por la lógica de controladores
INSERT INTO param_tipos_usuario (nombre, estado) VALUES ('Bibliotecario', 'ACTIVO'), ('Lector', 'ACTIVO');
INSERT INTO param_tipos_insumo (id_tipo_insumo, nombre, estado) VALUES (1, 'Papelería', 'ACTIVO'), (2, 'Mobiliario', 'ACTIVO'), (3, 'Libro', 'ACTIVO');

-- -----------------------------------------------------------------------------
-- 6. PROTOCOLO DE RECUPERACIÓN (SISTEMA DE PALABRAS MAESTRAS)
-- -----------------------------------------------------------------------------

-- Diccionario global de 500 palabras
CREATE TABLE param_diccionario_seguridad (
    id_palabra INT PRIMARY KEY AUTO_INCREMENT,
    palabra VARCHAR(50) NOT NULL UNIQUE
);

-- Tabla de claves de recuperación asociadas a usuarios
CREATE TABLE seguridad_recuperacion (
    id_recuperacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT UNIQUE,
    indices_palabras TEXT NOT NULL, -- Guardaremos los 12 números separados por comas
    salt_secreto VARCHAR(64),       -- Para el extra de seguridad que hablamos
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- =============================================================================
-- POBLADO MASIVO DEL DICCIONARIO DE SEGURIDAD (1000 PALABRAS)
-- Protocolo: Seguridad Persistente - Nivel Bibliotecario
-- =============================================================================

-- Diccionario global de 500 palabras
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
('Muro'), ('Foso'), ('Puente'), ('Camino'), ('Bosque'), ('Rio'), ('Valle'), ('Monte'), ('Cielo'), ('Universo'), ('Umbra'), ('Ratio'), ('Magnum'), ('Opus'), ('Primus'), ('Ultima'), ('Dominus'), ('Imperium'), ('Libertas'), ('Veritas'), ('Pax'), ('Bellum'), ('Fatum'), ('Tempus'), ('Spatium'), ('Codex'), ('Lex'), ('Vis'), ('Anima'), ('Corpus'), ('Spiritus'), ('Terra'), ('Aqua'), ('Ignis'), ('Aer'), ('Aether'), ('Chaos'), ('Cosmos'), ('Mundus'), ('Stella'), ('Luna'), ('Sol'), ('Nox'), ('Dies'), ('Vita'), ('Mors'), ('Scientia'), ('Sapientia'), ('Virtus'), ('Honor'), ('Gloria'), ('Fides'), ('Spes'), ('Caritas'), ('Amor'), ('Odium'), ('Metus'), ('Ira'), ('Gaudium'), ('Dolor'), ('Solitudo'), ('Silentium'), ('Clamor'), ('Vox'), ('Verbum'), ('Scriptura'), ('Littera'), ('Numerus'), ('Punctum'), ('Linea'), ('Circulus'), ('Triangulum'), ('Quadratum'), ('Sphaera'), ('Finis'), ('Cyber'), ('Quantum'), ('Entropy'), ('Parity'), ('Legacy'), ('Status'), ('System'), ('Root'), ('Admin'), ('Secure'), ('Void'), ('Null'), ('None'), ('True'), ('False'), ('Link'), ('Flow');
"""

def asegurar_integridad_carpetas():
    """Recorre 'Modulos' y crea archivos __init__.py donde falten."""
    ruta_modulos = os.path.join(os.path.dirname(__file__), 'Modulos')
    if not os.path.exists(ruta_modulos):
        return

    for root, dirs, files in os.walk(ruta_modulos):
        if '__init__.py' not in files:
            try:
                with open(os.path.join(root, '__init__.py'), 'w') as f:
                    pass 
                print(f"Estructura reparada: __init__.py creado en {root}")
            except Exception as e:
                print(f"Error reparando estructura: {e}")

def asegurar_base_datos():
    """Verifica la existencia de la BD y la genera si XAMPP está activo."""
    try:
        # Intenta conectar al servidor sin especificar BD primero
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute("SHOW DATABASES LIKE 'bibliotecabd'")
        resultado = cursor.fetchone()
        
        if not resultado:
            print("Base de datos no detectada. Iniciando protocolo de reconstrucción...")
            # Ejecutar el script SQL comando por comando
            for comando in SQL_RECONSTRUCCION.split(';'):
                if comando.strip():
                    cursor.execute(comando)
            conn.commit()
            print("Base de datos 'bibliotecabd' generada exitosamente.")
        
        cursor.close()
        conn.close()
    except Error as e:
        print(f"XAMPP/MySQL no detectado o error de conexión: {e}")

if __name__ == "__main__":
    # 1. Reparación de entorno antes de cargar componentes
    asegurar_integridad_carpetas()
    asegurar_base_datos()

    app = QApplication(sys.argv)
    app.setStyleSheet(ESTILO_GLOBAL)

    # 2. Flujo normal de la aplicación[cite: 6]
    ctrl_login = ControladorLogin()

    if ctrl_login.ejecutar():
        rol_final, nombre_usuario = ctrl_login.obtener_resultado()
        
        try:
            ventana = VentanaPrincipal(rol=rol_final)
            ventana.show()
            sys.exit(app.exec())
        except Exception as e:
            QMessageBox.critical(None, "Error Crítico", f"Fallo al abrir la interfaz principal:\n{str(e)}")
            sys.exit(1)
    else:
        sys.exit(0)