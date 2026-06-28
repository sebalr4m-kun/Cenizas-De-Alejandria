<?php
// Models/loginModel.php
require_once __DIR__ . '/../DB/Config.php'; 

class InicioSesionModel {
    private ?PDO $db;

    public function __construct() {
        $database = new ConexionBD();
        $this->db = $database->obtenerConexion();
    }

    public function buscarUsuarioPorEmail(string $email): ?array {
        if (!$this->db) {
            return null;
        }

        try {
            $query = "SELECT id_usuario, contraseña AS contrasena, estado_cuenta FROM usuarios WHERE email = :email LIMIT 1";
            $stmt = $this->db->prepare($query);
            $stmt->bindParam(":email", $email);
            $stmt->execute();
            
            if ($stmt->rowCount() > 0) {
                $resultado = $stmt->fetch(PDO::FETCH_ASSOC);
                return $resultado ?: null; 
            }
        } catch (PDOException $e) {
        }
        return null;
    }
}
?>