-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: bibliotecabd
-- ------------------------------------------------------
-- Server version	5.5.5-10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categorias_catalogo`
--

DROP TABLE IF EXISTS `categorias_catalogo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categorias_catalogo` (
  `id_categoria` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_categoria` varchar(50) NOT NULL,
  `estado` varchar(10) DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categorias_catalogo`
--

LOCK TABLES `categorias_catalogo` WRITE;
/*!40000 ALTER TABLE `categorias_catalogo` DISABLE KEYS */;
/*!40000 ALTER TABLE `categorias_catalogo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `editoriales`
--

DROP TABLE IF EXISTS `editoriales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `editoriales` (
  `id_editorial` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_editorial` varchar(100) NOT NULL,
  `estado` varchar(10) DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_editorial`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `editoriales`
--

LOCK TABLES `editoriales` WRITE;
/*!40000 ALTER TABLE `editoriales` DISABLE KEYS */;
INSERT INTO `editoriales` VALUES (1,'Cangreburguer','ACTIVO'),(2,'Mambo Mambo','ACTIVO');
/*!40000 ALTER TABLE `editoriales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `generos`
--

DROP TABLE IF EXISTS `generos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `generos` (
  `id_genero` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_genero` varchar(50) NOT NULL,
  `estado` varchar(10) DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_genero`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `generos`
--

LOCK TABLES `generos` WRITE;
/*!40000 ALTER TABLE `generos` DISABLE KEYS */;
INSERT INTO `generos` VALUES (1,'LGTB','ACTIVO');
/*!40000 ALTER TABLE `generos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `insumos`
--

DROP TABLE IF EXISTS `insumos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `insumos` (
  `id_insumo` int(11) NOT NULL AUTO_INCREMENT,
  `titulo` varchar(150) NOT NULL,
  `id_tipo_insumo` int(11) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'DISPONIBLE',
  `fecha_adquisicion` date DEFAULT NULL,
  `clave_runa` varchar(50) NOT NULL,
  PRIMARY KEY (`id_insumo`),
  UNIQUE KEY `clave_runa` (`clave_runa`),
  KEY `id_tipo_insumo` (`id_tipo_insumo`),
  CONSTRAINT `insumos_ibfk_1` FOREIGN KEY (`id_tipo_insumo`) REFERENCES `param_tipos_insumo` (`id_tipo_insumo`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `insumos`
--

LOCK TABLES `insumos` WRITE;
/*!40000 ALTER TABLE `insumos` DISABLE KEYS */;
INSERT INTO `insumos` VALUES (2,'Agares',2,'DISPONIBLE','2026-04-30','HCGTP'),(3,'History of 69',3,'DISPONIBLE','2026-05-01','815612'),(4,'Que tu-',3,'DISPONIBLE','2026-05-01','999779'),(5,'Que tu-',3,'DISPONIBLE','2026-05-01','465290'),(6,'OmenClones',3,'DISPONIBLE','2026-05-01','504045'),(7,'EE',3,'DISPONIBLE','2026-05-01','709341');
/*!40000 ALTER TABLE `insumos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `libro_autor`
--

DROP TABLE IF EXISTS `libro_autor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `libro_autor` (
  `id_libro` int(11) NOT NULL,
  `id_autor` int(11) NOT NULL,
  PRIMARY KEY (`id_libro`,`id_autor`),
  KEY `id_autor` (`id_autor`),
  CONSTRAINT `libro_autor_ibfk_1` FOREIGN KEY (`id_libro`) REFERENCES `libros` (`id_libro`) ON DELETE CASCADE,
  CONSTRAINT `libro_autor_ibfk_2` FOREIGN KEY (`id_autor`) REFERENCES `param_autores` (`id_autor`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `libro_autor`
--

LOCK TABLES `libro_autor` WRITE;
/*!40000 ALTER TABLE `libro_autor` DISABLE KEYS */;
INSERT INTO `libro_autor` VALUES (1,1),(2,1),(3,1),(4,1);
/*!40000 ALTER TABLE `libro_autor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `libro_categoria`
--

DROP TABLE IF EXISTS `libro_categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `libro_categoria` (
  `id_libro` int(11) NOT NULL,
  `id_categoria` int(11) NOT NULL,
  PRIMARY KEY (`id_libro`,`id_categoria`),
  KEY `id_categoria` (`id_categoria`),
  CONSTRAINT `libro_categoria_ibfk_1` FOREIGN KEY (`id_libro`) REFERENCES `libros` (`id_libro`) ON DELETE CASCADE,
  CONSTRAINT `libro_categoria_ibfk_2` FOREIGN KEY (`id_categoria`) REFERENCES `categorias_catalogo` (`id_categoria`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `libro_categoria`
--

LOCK TABLES `libro_categoria` WRITE;
/*!40000 ALTER TABLE `libro_categoria` DISABLE KEYS */;
/*!40000 ALTER TABLE `libro_categoria` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `libro_editorial`
--

DROP TABLE IF EXISTS `libro_editorial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `libro_editorial` (
  `id_libro` int(11) NOT NULL,
  `id_editorial` int(11) NOT NULL,
  PRIMARY KEY (`id_libro`,`id_editorial`),
  KEY `id_editorial` (`id_editorial`),
  CONSTRAINT `libro_editorial_ibfk_1` FOREIGN KEY (`id_libro`) REFERENCES `libros` (`id_libro`) ON DELETE CASCADE,
  CONSTRAINT `libro_editorial_ibfk_2` FOREIGN KEY (`id_editorial`) REFERENCES `editoriales` (`id_editorial`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `libro_editorial`
--

LOCK TABLES `libro_editorial` WRITE;
/*!40000 ALTER TABLE `libro_editorial` DISABLE KEYS */;
/*!40000 ALTER TABLE `libro_editorial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `libro_genero`
--

DROP TABLE IF EXISTS `libro_genero`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `libro_genero` (
  `id_libro` int(11) NOT NULL,
  `id_genero` int(11) NOT NULL,
  PRIMARY KEY (`id_libro`,`id_genero`),
  KEY `id_genero` (`id_genero`),
  CONSTRAINT `libro_genero_ibfk_1` FOREIGN KEY (`id_libro`) REFERENCES `libros` (`id_libro`) ON DELETE CASCADE,
  CONSTRAINT `libro_genero_ibfk_2` FOREIGN KEY (`id_genero`) REFERENCES `generos` (`id_genero`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `libro_genero`
--

LOCK TABLES `libro_genero` WRITE;
/*!40000 ALTER TABLE `libro_genero` DISABLE KEYS */;
/*!40000 ALTER TABLE `libro_genero` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `libros`
--

DROP TABLE IF EXISTS `libros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `libros` (
  `id_libro` int(11) NOT NULL AUTO_INCREMENT,
  `titulo` varchar(150) NOT NULL,
  `isbn` varchar(20) NOT NULL,
  `estado` varchar(10) DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_libro`),
  UNIQUE KEY `isbn` (`isbn`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `libros`
--

LOCK TABLES `libros` WRITE;
/*!40000 ALTER TABLE `libros` DISABLE KEYS */;
INSERT INTO `libros` VALUES (1,'History of 69','69','ACTIVO'),(2,'Que tu-','12','ACTIVO'),(3,'OmenClones','11','ACTIVO'),(4,'EE','1','ACTIVO');
/*!40000 ALTER TABLE `libros` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `param_autores`
--

DROP TABLE IF EXISTS `param_autores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `param_autores` (
  `id_autor` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_completo` varchar(100) NOT NULL,
  `estado` varchar(10) DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_autor`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `param_autores`
--

LOCK TABLES `param_autores` WRITE;
/*!40000 ALTER TABLE `param_autores` DISABLE KEYS */;
INSERT INTO `param_autores` VALUES (1,'Adriel Segura','ACTIVO');
/*!40000 ALTER TABLE `param_autores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `param_diccionario_seguridad`
--

DROP TABLE IF EXISTS `param_diccionario_seguridad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `param_diccionario_seguridad` (
  `id_palabra` int(11) NOT NULL AUTO_INCREMENT,
  `palabra` varchar(50) NOT NULL,
  PRIMARY KEY (`id_palabra`),
  UNIQUE KEY `palabra` (`palabra`)
) ENGINE=InnoDB AUTO_INCREMENT=1001 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `param_diccionario_seguridad`
--

LOCK TABLES `param_diccionario_seguridad` WRITE;
/*!40000 ALTER TABLE `param_diccionario_seguridad` DISABLE KEYS */;
INSERT INTO `param_diccionario_seguridad` VALUES (485,'Abeja'),(494,'Abeto'),(378,'Abismo'),(516,'Acantilado'),(904,'Aceite'),(785,'Acero'),(414,'Acido'),(139,'Actinio'),(993,'Admin'),(695,'Adn'),(952,'Aer'),(953,'Aether'),(430,'Afrodita'),(408,'Agua'),(453,'Aguila'),(911,'Aguja'),(410,'Aire'),(878,'Ala'),(623,'Alba'),(1,'Alfa'),(715,'Alga'),(151,'Algoritmo'),(381,'Alianza'),(404,'Alma'),(341,'Alquimista'),(63,'Aluminio'),(559,'Amatista'),(575,'Ambar'),(145,'Americio'),(635,'Amor'),(671,'Amperaje'),(348,'Amuleto'),(594,'Analisis'),(792,'Ancla'),(277,'Android'),(29,'Andromeda'),(327,'Angel'),(262,'Angular'),(677,'Angulo'),(363,'Anillo'),(946,'Anima'),(298,'Antena'),(718,'Antidoto'),(45,'Antimateria'),(101,'Antimonio'),(782,'Antorcha'),(437,'Anubis'),(254,'API'),(621,'Apogeo'),(429,'Apolo'),(950,'Aqua'),(483,'Araña'),(273,'Arch'),(518,'Archipielago'),(569,'Arcilla'),(353,'Arco'),(543,'Arcoiris'),(479,'Ardilla'),(680,'Area'),(417,'Arena'),(568,'Arenisca'),(426,'Ares'),(68,'Argon'),(358,'Armadura'),(615,'Armonia'),(696,'Arn'),(528,'Arrecife'),(83,'Arsenico'),(818,'Arte'),(428,'Artemisa'),(221,'Asincrono'),(135,'Astato'),(35,'Asteroide'),(427,'Atenea'),(588,'Atlas'),(689,'Atomo'),(399,'Aura'),(544,'Aurora'),(328,'Avatar'),(591,'Axioma'),(616,'Azar'),(66,'Azufre'),(241,'Backend'),(713,'Bacteria'),(346,'Baculo'),(460,'Ballena'),(354,'Ballesta'),(496,'Bambu'),(337,'Barbaro'),(793,'Barco'),(338,'Bardo'),(106,'Bario'),(897,'Barro'),(564,'Basalto'),(845,'Base'),(280,'Bash'),(318,'Basilisco'),(444,'Bastet'),(939,'Bellum'),(396,'Bendicion'),(54,'Berilio'),(147,'Berkelio'),(2,'Beta'),(152,'Binario'),(133,'Bismuto'),(870,'Bit'),(735,'Boca'),(890,'Bomba'),(222,'Booleano'),(848,'Borde'),(55,'Boro'),(50,'Boson'),(373,'Bosque'),(361,'Botas'),(800,'Brillo'),(85,'Bromo'),(786,'Bronce'),(330,'Brujo'),(585,'Brujula'),(797,'Bruma'),(200,'Buffer'),(455,'Buho'),(894,'Burbuja'),(871,'Byte'),(474,'Caballo'),(884,'Cable'),(201,'Cache'),(98,'Cadmio'),(463,'Calamar'),(70,'Calcio'),(868,'Calculo'),(148,'Californio'),(567,'Caliza'),(658,'Calor'),(675,'Caloria'),(770,'Camino'),(779,'Candado'),(508,'Canela'),(515,'Cañon'),(611,'Caos'),(362,'Capa'),(856,'Cara'),(576,'Carbon'),(56,'Carbono'),(966,'Caritas'),(830,'Carta'),(526,'Cascada'),(359,'Casco'),(370,'Castillo'),(692,'Catalisis'),(491,'Cedro'),(697,'Celula'),(30,'Cenit'),(573,'Ceniza'),(309,'Centauro'),(846,'Centro'),(724,'Cerebro'),(108,'Cerio'),(105,'Cesio'),(347,'Cetro'),(954,'Chaos'),(22,'Chi'),(872,'Chip'),(891,'Chispa'),(178,'Ciber'),(926,'Cielo'),(476,'Ciervo'),(865,'Cifra'),(862,'Cilindro'),(853,'Cima'),(821,'Cine'),(980,'Circulus'),(744,'Ciudad'),(972,'Clamor'),(843,'Clan'),(223,'Clase'),(916,'Clavo'),(332,'Clerigo'),(534,'Clima'),(710,'Clon'),(67,'Cloro'),(77,'Cobalto'),(79,'Cobre'),(458,'Cocodrilo'),(943,'Codex'),(153,'Codigo'),(778,'Cofre'),(364,'Collar'),(801,'Color'),(34,'Cometa'),(154,'Compilador'),(607,'Conciencia'),(269,'Conda'),(478,'Conejo'),(861,'Cono'),(38,'Constelacion'),(520,'Continente'),(465,'Coral'),(725,'Corazon'),(788,'Corona'),(947,'Corpus'),(551,'Corriente'),(39,'Cosmos'),(624,'Crepusculo'),(416,'Cristal'),(74,'Cromo'),(708,'Cromosoma'),(258,'Css'),(553,'Cuarzo'),(860,'Cubo'),(867,'Cuenta'),(791,'Cuerda'),(907,'Cuero'),(701,'Cuerpo'),(456,'Cuervo'),(372,'Cueva'),(653,'Cura'),(146,'Curio'),(985,'Cyber'),(829,'Dado'),(202,'Daemon'),(355,'Daga'),(823,'Danza'),(869,'Dato'),(179,'Datos'),(271,'Debian'),(461,'Delfin'),(4,'Delta'),(435,'Demeter'),(326,'Demonio'),(684,'Densidad'),(155,'Depuracion'),(637,'Deseo'),(376,'Desierto'),(224,'Despliegue'),(799,'Destello'),(389,'Destino'),(290,'Dhcp'),(554,'Diamante'),(678,'Diametro'),(958,'Dies'),(667,'Difraccion'),(388,'Dimension'),(433,'Dionisio'),(826,'Diseño'),(116,'Disprosio'),(247,'Django'),(289,'Dns'),(244,'Docker'),(638,'Dolor'),(934,'Dominus'),(299,'Dragon'),(339,'Druida'),(599,'Dualidad'),(640,'Duda'),(307,'Duende'),(531,'Duna'),(33,'Eclipse'),(661,'Eco'),(149,'Einstenio'),(847,'Eje'),(48,'Electron'),(469,'Elefante'),(325,'Elemental'),(300,'Elfo'),(366,'Elixir'),(301,'Enano'),(156,'Encriptacion'),(401,'Energia'),(880,'Engrane'),(398,'Enigma'),(180,'Enlace'),(225,'Entorno'),(613,'Entropia'),(987,'Entropy'),(693,'Enzima'),(5,'Epsilon'),(614,'Equilibrio'),(118,'Erbio'),(549,'Erupcion'),(767,'Escalera'),(71,'Escandio'),(488,'Escarabajo'),(896,'Escarcha'),(482,'Escorpion'),(350,'Escudo'),(402,'Esencia'),(859,'Esfera'),(316,'Esfinge'),(556,'Esmeralda'),(608,'Espacio'),(349,'Espada'),(705,'Especie'),(321,'Espectro'),(580,'Espejo'),(642,'Esperanza'),(403,'Espiritu'),(323,'Esqueleto'),(746,'Estado'),(100,'Estaño'),(825,'Estatua'),(583,'Este'),(511,'Estepa'),(598,'Estetica'),(37,'Estrella'),(88,'Estroncio'),(527,'Estuario'),(7,'Eta'),(609,'Eternidad'),(203,'Ethernet'),(596,'Etica'),(113,'Europio'),(704,'Evolucion'),(336,'Explorador'),(266,'Express'),(393,'Fabula'),(998,'False'),(887,'Faro'),(940,'Fatum'),(641,'Fe'),(272,'Fedora'),(314,'Fenix'),(150,'Fermio'),(831,'Ficha'),(964,'Fides'),(181,'Fila'),(850,'Final'),(984,'Finis'),(204,'Firewall'),(248,'Flask'),(790,'Flecha'),(1000,'Flow'),(685,'Fluido'),(59,'Fluor'),(854,'Fondo'),(802,'Forma'),(618,'Fortuna'),(529,'Fosa'),(65,'Fosforo'),(574,'Fosil'),(924,'Foso'),(920,'Fragua'),(157,'Framework'),(137,'Francio'),(813,'Frase'),(663,'Frecuencia'),(659,'Frio'),(242,'Frontend'),(284,'Ftp'),(407,'Fuego'),(654,'Fuerza'),(243,'Fullstack'),(226,'Funcion'),(114,'Gadolinio'),(28,'Galaxia'),(81,'Galio'),(3,'Gamma'),(578,'Gas'),(205,'Gateway'),(969,'Gaudium'),(533,'Geiser'),(707,'Gen'),(647,'Genio'),(82,'Germanio'),(182,'Gestor'),(158,'Giga'),(305,'Gigante'),(503,'Girasol'),(227,'Git'),(522,'Glaciar'),(587,'Globo'),(628,'Gloria'),(303,'Gnomo'),(324,'Golem'),(893,'Gota'),(676,'Grado'),(563,'Granito'),(539,'Granizo'),(570,'Grava'),(41,'Gravedad'),(382,'Gremio'),(315,'Grifo'),(345,'Grimorio'),(737,'Grito'),(841,'Grupo'),(360,'Guantelete'),(334,'Guerrero'),(351,'Hacha'),(306,'Hada'),(424,'Hades'),(122,'Hafnio'),(454,'Halcon'),(159,'Hardware'),(206,'Hash'),(331,'Hechicero'),(394,'Hechizo'),(432,'Hefesto'),(497,'Helecho'),(52,'Helio'),(434,'Hera'),(709,'Herencia'),(431,'Hermes'),(711,'Hibrido'),(312,'Hidra'),(51,'Hidrogeno'),(412,'Hielo'),(76,'Hierro'),(727,'Higado'),(183,'Hilo'),(471,'Hipopotamo'),(593,'Hipotesis'),(743,'Hogar'),(117,'Holmio'),(714,'Hongo'),(629,'Honor'),(43,'Horizonte'),(484,'Hormiga'),(921,'Horno'),(440,'Horus'),(228,'Host'),(257,'Html'),(285,'Http'),(286,'Https'),(729,'Hueso'),(796,'Humo'),(546,'Huracan'),(951,'Ignis'),(651,'Ignorancia'),(604,'Ilusion'),(885,'Iman'),(380,'Imperio'),(935,'Imperium'),(656,'Impulso'),(184,'Indice'),(99,'Indio'),(655,'Inercia'),(610,'Infinito'),(851,'Inicio'),(645,'Instinto'),(160,'Interfaz'),(207,'Intranet'),(646,'Intuicion'),(343,'Invocador'),(278,'Ios'),(9,'Iota'),(291,'Ipv4'),(292,'Ipv6'),(633,'Ira'),(127,'Iridio'),(439,'Isis'),(517,'Isla'),(229,'Iteracion'),(120,'Iterbio'),(89,'Itrio'),(561,'Jade'),(161,'Java'),(259,'Javascript'),(185,'Jerarquia'),(472,'Jirafa'),(787,'Joyel'),(230,'Joystick'),(208,'Json'),(828,'Juego'),(834,'Jugada'),(674,'Julios'),(752,'Jupiter'),(625,'Justicia'),(274,'Kali'),(10,'Kappa'),(619,'Karma'),(162,'Kernel'),(186,'Kilobyte'),(313,'Kraken'),(86,'Kripton'),(245,'Kubernetes'),(855,'Lado'),(524,'Lago'),(525,'Laguna'),(11,'Lambda'),(780,'Lampara'),(906,'Lana'),(107,'Lantano'),(352,'Lanza'),(873,'Laser'),(209,'Latencia'),(571,'Lava'),(506,'Lavanda'),(910,'Lazo'),(630,'Lealtad'),(989,'Legacy'),(449,'Leon'),(811,'Letra'),(944,'Lex'),(391,'Leyenda'),(487,'Libelula'),(626,'Libertad'),(936,'Libertas'),(163,'Libreria'),(773,'Libro'),(320,'Licantropo'),(849,'Limite'),(979,'Linea'),(722,'Linfa'),(999,'Link'),(908,'Lino'),(231,'Linux'),(687,'Liquido'),(500,'Lirio'),(53,'Litio'),(976,'Littera'),(892,'Llama'),(777,'Llave'),(760,'Llegada'),(537,'Lluvia'),(451,'Lobo'),(652,'Locura'),(418,'Lodo'),(844,'Logia'),(187,'Logica'),(422,'Loki'),(504,'Loto'),(749,'Luna'),(121,'Lutecio'),(406,'Luz'),(276,'MacOS'),(784,'Madera'),(572,'Magma'),(62,'Magnesio'),(669,'Magnetismo'),(930,'Magnum'),(329,'Mago'),(395,'Maldicion'),(400,'Mana'),(75,'Manganeso'),(586,'Mapa'),(550,'Marea'),(505,'Margarita'),(250,'MariaDB'),(486,'Mariposa'),(565,'Marmol'),(751,'Marte'),(356,'Martillo'),(682,'Masa'),(294,'Mascara'),(44,'Materia'),(188,'Matriz'),(357,'Maza'),(369,'Mazmorra'),(464,'Medusa'),(807,'Melodia'),(164,'Memoria'),(507,'Menta'),(606,'Mente'),(384,'Mercado'),(130,'Mercurio'),(852,'Meta'),(415,'Metal'),(232,'Metodo'),(968,'Metus'),(632,'Miedo'),(902,'Miel'),(397,'Milagro'),(317,'Minotauro'),(601,'Misterio'),(392,'Mito'),(827,'Moda'),(297,'Modem'),(210,'Modulo'),(690,'Molecula'),(92,'Molibdeno'),(922,'Molino'),(253,'Mongo'),(340,'Monje'),(374,'Montaña'),(925,'Monte'),(597,'Moral'),(960,'Mors'),(877,'Motor'),(12,'Mu'),(703,'Muerte'),(748,'Mundo'),(955,'Mundus'),(481,'Murcielago'),(764,'Muro'),(730,'Musculo'),(819,'Museo'),(498,'Musgo'),(822,'Musica'),(706,'Mutacion'),(747,'Nacion'),(31,'Nadir'),(734,'Nariz'),(876,'Nave'),(233,'Navegador'),(27,'Nebulosa'),(110,'Neodimio'),(60,'Neon'),(143,'Neptunio'),(755,'Neptuno'),(723,'Nervio'),(47,'Neutron'),(542,'Niebla'),(538,'Nieve'),(342,'Nigromante'),(447,'Nilo'),(91,'Niobio'),(78,'Niquel'),(57,'Nitrogeno'),(838,'Nivel'),(265,'Node'),(165,'Nodo'),(996,'None'),(581,'Norte'),(957,'Nox'),(267,'Npm'),(13,'Nu'),(189,'Nube'),(698,'Nucleo'),(909,'Nudo'),(211,'Null'),(866,'Numero'),(977,'Numerus'),(532,'Oasis'),(166,'Objeto'),(817,'Obra'),(562,'Obsidiana'),(622,'Ocaso'),(377,'Oceano'),(212,'Octeto'),(420,'Odín'),(636,'Odio'),(967,'Odium'),(584,'Oeste'),(672,'Ohmios'),(733,'Oido'),(732,'Ojo'),(552,'Ola'),(804,'Olor'),(643,'Olvido'),(24,'Omega'),(15,'Omicron'),(664,'Onda'),(560,'Opalo'),(190,'Operador'),(931,'Opus'),(32,'Orbita'),(302,'Orco'),(612,'Orden'),(699,'Organo'),(234,'Origen'),(129,'Oro'),(502,'Orquidea'),(438,'Osiris'),(126,'Osmio'),(452,'Oso'),(58,'Oxigeno'),(814,'Pagina'),(898,'Paja'),(913,'Pala'),(812,'Palabra'),(333,'Paladin'),(96,'Paladio'),(495,'Palmera'),(900,'Pan'),(375,'Pantano'),(776,'Papel'),(191,'Paquete'),(600,'Paradoja'),(716,'Parasito'),(988,'Parity'),(761,'Partida'),(938,'Pax'),(634,'Paz'),(310,'Pegaso'),(741,'Peligro'),(519,'Peninsula'),(367,'Pergamino'),(679,'Perimetro'),(436,'Persefone'),(683,'Peso'),(577,'Petroleo'),(21,'Phi'),(16,'Pi'),(335,'Picaro'),(914,'Pico'),(783,'Piedra'),(731,'Piel'),(833,'Pieza'),(883,'Pila'),(490,'Pino'),(824,'Pintura'),(918,'Pinza'),(268,'Pip'),(213,'Pipeline'),(448,'Piramide'),(881,'Piston'),(566,'Pizarra'),(639,'Placer'),(36,'Planeta'),(858,'Plano'),(688,'Plasma'),(97,'Plata'),(128,'Platino'),(530,'Playa'),(771,'Plaza'),(132,'Plomo'),(774,'Pluma'),(756,'Pluton'),(144,'Plutonio'),(365,'Pocion'),(627,'Poder'),(668,'Polaridad'),(886,'Polo'),(134,'Polonio'),(795,'Polvo'),(387,'Portal'),(425,'Poseidon'),(251,'Postgres'),(69,'Potasio'),(282,'PowerShell'),(923,'Pozo'),(513,'Pradera'),(109,'Praseodimio'),(657,'Presion'),(932,'Primus'),(390,'Profecia'),(111,'Prometio'),(810,'Prosa'),(141,'Protactinio'),(694,'Proteina'),(167,'Protocolo'),(46,'Proton'),(23,'Psi'),(745,'Pueblo'),(768,'Puente'),(762,'Puerta'),(199,'Puerto'),(726,'Pulmon'),(462,'Pulpo'),(26,'Pulsar'),(889,'Pulso'),(978,'Punctum'),(235,'Puntero'),(837,'Punto'),(246,'Python'),(982,'Quadratum'),(986,'Quantum'),(49,'Quark'),(25,'Quasar'),(168,'Query'),(214,'Queue'),(311,'Quimera'),(441,'Ra'),(874,'Radar'),(138,'Radio'),(136,'Radon'),(467,'Rana'),(839,'Rango'),(929,'Ratio'),(480,'Raton'),(411,'Rayo'),(644,'Razon'),(691,'Reaccion'),(261,'React'),(603,'Realidad'),(215,'Recursion'),(169,'Red'),(252,'Redis'),(798,'Reflejo'),(665,'Reflexion'),(666,'Refraccion'),(742,'Refugio'),(836,'Regla'),(379,'Reino'),(368,'Reliquia'),(772,'Reloj'),(125,'Renio'),(236,'Repositorio'),(255,'Rest'),(864,'Resta'),(17,'Rho'),(740,'Riesgo'),(809,'Rima'),(470,'Rinoceronte'),(728,'Riñon'),(523,'Rio'),(806,'Ritmo'),(489,'Roble'),(895,'Rocio'),(95,'Rodio'),(992,'Root'),(499,'Rosa'),(295,'Router'),(555,'Rubi'),(87,'Rubidio'),(879,'Rueda'),(386,'Ruinas'),(344,'Runas'),(589,'Ruta'),(94,'Rutenio'),(192,'Rutina'),(512,'Sabana'),(650,'Sabiduria'),(805,'Sabor'),(816,'Saga'),(903,'Sal'),(468,'Salamandra'),(717,'Salud'),(112,'Samario'),(721,'Sangre'),(649,'Sapiencia'),(962,'Sapientia'),(753,'Saturno'),(493,'Sauce'),(961,'Scientia'),(193,'Script'),(975,'Scriptura'),(842,'Secta'),(492,'Secuoya'),(994,'Secure'),(905,'Seda'),(446,'Sekhmet'),(84,'Selenio'),(509,'Selva'),(888,'Señal'),(590,'Sendero'),(457,'Serpiente'),(170,'Servidor'),(442,'Seth'),(279,'Shell'),(915,'Sierra'),(18,'Sigma'),(739,'Silencio'),(971,'Silentium'),(64,'Silicio'),(237,'Sincronia'),(42,'Singularidad'),(595,'Sintesis'),(308,'Sirena'),(757,'Sistema'),(256,'Soap'),(445,'Sobek'),(198,'Socket'),(61,'Sodio'),(750,'Sol'),(686,'Solido'),(970,'Solitudo'),(405,'Sombra'),(875,'Sonda'),(660,'Sonido'),(942,'Spatium'),(965,'Spes'),(983,'Sphaera'),(948,'Spiritus'),(249,'Sqlite'),(283,'Ssh'),(288,'Ssl'),(216,'Stack'),(990,'Status'),(956,'Stella'),(293,'Subred'),(766,'Suelo'),(605,'Sueño'),(720,'Suero'),(617,'Suerte'),(863,'Suma'),(582,'Sur'),(738,'Susurro'),(264,'Svelte'),(296,'Switch'),(991,'System'),(383,'Taberna'),(832,'Tablero'),(648,'Talento'),(131,'Talio'),(123,'Tantalio'),(19,'Tau'),(820,'Teatro'),(765,'Techo'),(93,'Tecnecio'),(700,'Tejido'),(102,'Telurio'),(385,'Templo'),(941,'Tempus'),(592,'Teoria'),(115,'Terbio'),(194,'Terminal'),(949,'Terra'),(548,'Terremoto'),(803,'Textura'),(8,'Theta'),(421,'Thor'),(443,'Thot'),(217,'Thread'),(459,'Tiburon'),(535,'Tiempo'),(409,'Tierra'),(450,'Tigre'),(912,'Tijera'),(794,'Timon'),(775,'Tinta'),(840,'Tipo'),(72,'Titanio'),(287,'Tls'),(171,'Token'),(815,'Tomo'),(558,'Topacio'),(140,'Torio'),(540,'Tormenta'),(545,'Tornado'),(917,'Tornillo'),(475,'Toro'),(371,'Torre'),(466,'Tortuga'),(238,'Trama'),(981,'Triangulum'),(899,'Trigo'),(304,'Troll'),(789,'Trono'),(997,'True'),(541,'Trueno'),(547,'Tsunami'),(119,'Tulio'),(501,'Tulipan'),(510,'Tundra'),(769,'Tunel'),(835,'Turno'),(260,'Typescript'),(270,'Ubuntu'),(933,'Ultima'),(928,'Umbra'),(239,'Umbral'),(195,'Unidad'),(927,'Universo'),(218,'Uplink'),(20,'Upsilon'),(142,'Uranio'),(754,'Urano'),(172,'Usuario'),(40,'Vacio'),(719,'Vacuna'),(240,'Validacion'),(514,'Valle'),(631,'Valor'),(419,'Valquiria'),(882,'Valvula'),(319,'Vampiro'),(73,'Vanadio'),(173,'Variable'),(673,'Vatios'),(196,'Vector'),(781,'Vela'),(413,'Veneno'),(763,'Ventana'),(974,'Verbum'),(602,'Verdad'),(937,'Veritas'),(808,'Verso'),(857,'Vertice'),(759,'Viaje'),(662,'Vibracion'),(702,'Vida'),(579,'Vidrio'),(536,'Viento'),(901,'Vino'),(219,'Virtual'),(963,'Virtus'),(712,'Virus'),(945,'Vis'),(959,'Vita'),(995,'Void'),(521,'Volcan'),(670,'Voltaje'),(681,'Volumen'),(973,'Vox'),(736,'Voz'),(263,'Vue'),(758,'Vuelo'),(197,'Web'),(174,'Widget'),(220,'Wifi'),(275,'Windows'),(124,'Wolframio'),(104,'Xenon'),(14,'Xi'),(175,'Xml'),(103,'Yodo'),(176,'Yotta'),(919,'Yunque'),(557,'Zafiro'),(473,'Zebra'),(620,'Zenit'),(6,'Zeta'),(423,'Zeus'),(80,'Zinc'),(177,'Zip'),(90,'Zirconio'),(322,'Zombi'),(477,'Zorro'),(281,'Zsh');
/*!40000 ALTER TABLE `param_diccionario_seguridad` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `param_tipos_insumo`
--

DROP TABLE IF EXISTS `param_tipos_insumo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `param_tipos_insumo` (
  `id_tipo_insumo` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `estado` varchar(10) DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_tipo_insumo`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `param_tipos_insumo`
--

LOCK TABLES `param_tipos_insumo` WRITE;
/*!40000 ALTER TABLE `param_tipos_insumo` DISABLE KEYS */;
INSERT INTO `param_tipos_insumo` VALUES (1,'Papelería','ACTIVO'),(2,'Mobiliario','ACTIVO'),(3,'Libro','ACTIVO'),(4,'Regla Telemétrica','INACTIVO');
/*!40000 ALTER TABLE `param_tipos_insumo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `param_tipos_usuario`
--

DROP TABLE IF EXISTS `param_tipos_usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `param_tipos_usuario` (
  `id_tipo_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `estado` varchar(10) DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_tipo_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `param_tipos_usuario`
--

LOCK TABLES `param_tipos_usuario` WRITE;
/*!40000 ALTER TABLE `param_tipos_usuario` DISABLE KEYS */;
INSERT INTO `param_tipos_usuario` VALUES (1,'Bibliotecario','ACTIVO'),(2,'Lector','ACTIVO'),(3,'Conserje','ACTIVO'),(4,'ae','ACTIVO');
/*!40000 ALTER TABLE `param_tipos_usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prestamos`
--

DROP TABLE IF EXISTS `prestamos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prestamos` (
  `id_prestamo` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `id_insumo` int(11) DEFAULT NULL,
  `fecha_prestamo` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_devolucion_esperada` date DEFAULT NULL,
  `estado_prestamo` varchar(20) DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_prestamo`),
  KEY `id_usuario` (`id_usuario`),
  KEY `id_insumo` (`id_insumo`),
  CONSTRAINT `prestamos_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `prestamos_ibfk_2` FOREIGN KEY (`id_insumo`) REFERENCES `insumos` (`id_insumo`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prestamos`
--

LOCK TABLES `prestamos` WRITE;
/*!40000 ALTER TABLE `prestamos` DISABLE KEYS */;
/*!40000 ALTER TABLE `prestamos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seguridad_recuperacion`
--

DROP TABLE IF EXISTS `seguridad_recuperacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seguridad_recuperacion` (
  `id_recuperacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `indices_palabras` text NOT NULL,
  `salt_secreto` varchar(64) DEFAULT NULL,
  `fecha_generacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_recuperacion`),
  UNIQUE KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `seguridad_recuperacion_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seguridad_recuperacion`
--

LOCK TABLES `seguridad_recuperacion` WRITE;
/*!40000 ALTER TABLE `seguridad_recuperacion` DISABLE KEYS */;
INSERT INTO `seguridad_recuperacion` VALUES (1,1,'546, 195, 330, 541, 147, 77, 121, 17, 472, 655, 283, 90',NULL,'2026-04-30 20:55:11'),(3,2,'954, 2, 287, 271, 23, 678, 759, 690, 439, 376, 995, 409',NULL,'2026-05-01 07:25:23'),(34,7,'412, 748, 185, 604, 21, 908, 165, 625, 165, 443, 414, 657',NULL,'2026-05-01 23:31:22'),(36,6,'778, 832, 906, 61, 344, 827, 826, 881, 524, 734, 267, 762',NULL,'2026-05-01 23:47:21'),(37,9,'739, 736, 405, 188, 815, 414, 867, 507, 52, 771, 717, 110',NULL,'2026-05-02 00:08:47'),(38,10,'647, 474, 662, 70, 502, 616, 692, 323, 370, 147, 619, 299',NULL,'2026-05-02 00:18:17'),(44,16,'2, 260, 991, 592, 395, 190, 199, 777, 159, 721, 223, 853',NULL,'2026-05-16 02:37:22'),(45,17,'742, 960, 219, 353, 802, 363, 317, 157, 47, 68, 565, 606',NULL,'2026-05-16 02:58:00'),(46,18,'192, 515, 109, 10, 318, 807, 990, 934, 262, 270, 983, 51',NULL,'2026-05-16 02:58:59'),(47,19,'924, 926, 716, 419, 553, 966, 486, 843, 219, 138, 180, 305',NULL,'2026-05-16 03:05:39'),(48,20,'823, 809, 39, 845, 903, 123, 408, 556, 976, 991, 470, 69',NULL,'2026-05-16 03:13:00');
/*!40000 ALTER TABLE `seguridad_recuperacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `id_tipo_usuario` int(11) DEFAULT NULL,
  `contraseña` varchar(255) DEFAULT NULL,
  `estado_cuenta` varchar(20) DEFAULT 'ACTIVA',
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `email` (`email`),
  KEY `id_tipo_usuario` (`id_tipo_usuario`),
  CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_tipo_usuario`) REFERENCES `param_tipos_usuario` (`id_tipo_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'omen','omen',1,'$2b$12$7zy6jzyMdVe2KN/EdD6aV..HeTeyjKsLUHcWxAChfdEJvRqGx7Kg.','ACTIVA'),(2,'asds','sadasf@g.com',1,'$2b$12$nvnSu5tUqUkPTJ3yMo.oNuXnbIplZmtzGxFk/xLiObH/ZYJXn47h2','ACTIVA'),(3,'ae','Agares@gmail.com',2,'','ACTIVA'),(4,'xd','Xdxdxdxd@gmail.com',3,'','INACTIVA'),(5,'sigma','ae@gmail.com',4,'','ACTIVA'),(6,'Agares Zadkiel','a14nX4rd@gmail.com',1,'$2b$12$xbM0haG9FL/U1i1AJYOpDOnNkBBnvE86qRwcFNgkTey4saRgggr/i','ACTIVA'),(7,'123','123@gmail.com',1,'$2b$12$z37okqwDrkuT70YHDrBFWeOkw/2EQCjIAy2kDtc45T/52xCJp/wJ6','ACTIVA'),(9,'1','1@gmail.com',1,'$2b$12$IWF5R6UVTqYcHP20elOk2u3TmmvGvmTS52foZhsiYupSBGXAdiK4C','ACTIVA'),(10,'fuap','Fuap',1,'$2b$12$YrFFWr9C3mKoww.i9XhVb.7L0bfyanX3XGhIiFNdW5Kx2j.kPTWw2','ACTIVA'),(16,'ae','aea@gmail.com',1,'$2b$12$U1bJux6mO2/P.sIpauLlgOWxtNlxfjNYFWr0zVnaAIBTT82Bl04sO','ACTIVA'),(17,'ae','yippiee@gmail.com',1,'$2b$12$1UH4/1ag5SZNxhE8Xt3YS.RzGnWoqFvbOs8UTVphDIgevQIGTk.6O','ACTIVA'),(18,'zulu','yeey@gmail.com',1,'$2b$12$CrrFJxCqz.0rn9FvM0VE4e4iriWqZa.nbs9mjyFOkgGSnrsemRC0y','ACTIVA'),(19,'omen@gmail.com','omen@gmail.com',1,'$2b$12$GjyxRdDULqiHFZU6dhshe.92fPFt.6fNQ6bDakpjuWrBSE7J2j7Vu','ACTIVA'),(20,'a','ku@gmail.com',1,'$2b$12$h29BzGApKhvLvQxXS0h1MeBaAu5c69nqpJuV.PIEWGfap9DWaEgZa','ACTIVA');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-19 19:58:17
