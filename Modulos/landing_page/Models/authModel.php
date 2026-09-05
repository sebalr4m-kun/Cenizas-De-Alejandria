<?php
// Models/authModel.php
require_once __DIR__ . '/../DB/Config.php';

class AuthModel {
    private $conn;

    public function __construct() {
        $db = new ConexionBD();
        $this->conn = $db->obtenerConexion();
    }

    public function getUserByEmail($email) {
        $stmt = $this->conn->prepare("SELECT * FROM usuarios WHERE email = :email");
        $stmt->execute(['email' => $email]);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    public function createUser($nombre, $email, $password) {
        $hash = password_hash($password, PASSWORD_DEFAULT);
        $clave_drm = bin2hex(random_bytes(16)); 
        
        $stmt = $this->conn->prepare("INSERT INTO usuarios (nombre, email, contraseña, clave_drm_maestra) VALUES (:nombre, :email, :password, :clave_drm)");
        return $stmt->execute([
            'nombre' => $nombre, 
            'email' => $email, 
            'password' => $hash,
            'clave_drm' => $clave_drm
        ]);
    }

    public function updateUser($email, $nombre, $newPassword = null) {
        if ($newPassword) {
            $hash = password_hash($newPassword, PASSWORD_DEFAULT);
            $stmt = $this->conn->prepare("UPDATE usuarios SET nombre = :nombre, contraseña = :password WHERE email = :email");
            return $stmt->execute(['nombre' => $nombre, 'password' => $hash, 'email' => $email]);
        } else {
            $stmt = $this->conn->prepare("UPDATE usuarios SET nombre = :nombre WHERE email = :email");
            return $stmt->execute(['nombre' => $nombre, 'email' => $email]);
        }
    }

    public function deleteUser($email) {
        $stmt = $this->conn->prepare("DELETE FROM usuarios WHERE email = :email");
        return $stmt->execute(['email' => $email]);
    }

    public function getSecurityWords($limit = 3) {
        // Asumiendo que la columna se llama 'palabra' dentro de 'param_diccionario_seguridad'
        $stmt = $this->conn->prepare("SELECT palabra FROM param_diccionario_seguridad ORDER BY RAND() LIMIT :limit");
        $stmt->bindValue(':limit', (int)$limit, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_COLUMN);
    }
}
?>