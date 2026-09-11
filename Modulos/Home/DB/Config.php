<?php
// DB/Config.php
class ConexionBD {
    private string $host = 'localhost';
    private string $db_name = 'bibliotecabd';
    private string $username = 'root';
    private string $password = '';
    private ?PDO $conn = null;

    public function obtenerConexion(): ?PDO {
        if ($this->conn === null) {
            try {
                $this->conn = new PDO(
                    "mysql:host=" . $this->host . ";dbname=" . $this->db_name . ";charset=utf8mb4",
                    $this->username,
                    $this->password
                );
                $this->conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            } catch (PDOException $exception) {
                $this->conn = null;
            }
        }
        return $this->conn;
    }
}
?>