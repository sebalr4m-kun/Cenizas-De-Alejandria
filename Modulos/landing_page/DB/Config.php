<?php
// DB/Config.php
class ConexionBD {
    private $host = "localhost";
    private $nombre_db = "onlineashes";
    private $usuario = "root";
    private $contrasena = "";
    public $conn;

    public function obtenerConexion() {
        $this->conn = null;
        try {
            $this->conn = new PDO("mysql:host=" . $this->host . ";dbname=" . $this->nombre_db, $this->usuario, $this->contrasena);
            $this->conn->exec("set names utf8");
        } catch(PDOException $exception) {
            echo "Error de conexión: " . $exception->getMessage();
        }
        return $this->conn;
    }
}
?>