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
            $query = "SELECT 
                        u.id_usuario, 
                        u.nombre, 
                        u.contraseña AS contrasena, 
                        u.estado_cuenta,
                        p.nombre AS rol,
                        p.admitido,
                        p.permisos
                      FROM usuarios u
                      INNER JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
                      WHERE u.email = :email 
                      LIMIT 1";
                      
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