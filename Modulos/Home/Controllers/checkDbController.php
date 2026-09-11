<?php
// Controllers/checkDbController.php
header("Content-Type: application/json");
require_once __DIR__ . '/../DB/Config.php'; 

try {
    $database = new ConexionBD();
    $db = $database->obtenerConexion();

    if ($db !== null) {
        echo json_encode(["status" => "success"]);
    } else {
        echo json_encode(["status" => "error", "message" => "Base de datos apagada."]);
    }
} catch (Exception $e) {
    echo json_encode(["status" => "error", "message" => $e->getMessage()]);
}
?>