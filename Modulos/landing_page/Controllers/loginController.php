<?php
// Controllers/loginController.php
header("Content-Type: application/json");
require_once __DIR__ . '/../Models/loginModel.php';

$data = json_decode(file_get_contents("php://input"));

if (!empty($data->email) && !empty($data->password)) {

    $model = new InicioSesionModel();
    $usuario = $model->buscarUsuarioPorEmail($data->email);
    
    if ($usuario) {
        $hash = $usuario['contrasena'] ?? $usuario['contraseña'] ?? '';
        
        if (password_verify($data->password, $hash)) {
            
            // Decodificación segura del árbol de permisos JSON
            $permisosRaw = $usuario['permisos'] ?? '';
            $permisos = [];
            
            if (!empty($permisosRaw)) {
                $permisos = is_string($permisosRaw) ? json_decode($permisosRaw, true) : $permisosRaw;
            }
            
            if (!is_array($permisos)) {
                $permisos = [];
            }
            $nodoUsuarios = $permisos['Usuarios'] ?? $permisos['usuarios'] ?? null;
            
            // Intentamos atrapar el nodo de Parámetros tolerando acentos y variaciones de caja
            $nodoParametros = $permisos['Parametros'] ?? $permisos['parametros'] ?? 
                              $permisos['Parámetros'] ?? $permisos['parámetros'] ?? null;
            
            // Validación interna de permisos (Lectura y Escritura obligatorios)
            $usuarios_ok = isset($nodoUsuarios['ver']) && filter_var($nodoUsuarios['ver'], FILTER_VALIDATE_BOOLEAN) && 
                           isset($nodoUsuarios['editar']) && filter_var($nodoUsuarios['editar'], FILTER_VALIDATE_BOOLEAN);
                           
            $parametros_ok = isset($nodoParametros['ver']) && filter_var($nodoParametros['ver'], FILTER_VALIDATE_BOOLEAN) && 
                             isset($nodoParametros['editar']) && filter_var($nodoParametros['editar'], FILTER_VALIDATE_BOOLEAN);
            
            // Validación de estado de cuenta y admisión del rol federado
            $es_admitido = isset($usuario['admitido']) && filter_var($usuario['admitido'], FILTER_VALIDATE_BOOLEAN);
            $es_activa = isset($usuario['estado_cuenta']) && (strtoupper($usuario['estado_cuenta']) === 'ACTIVA');
            
            if ($es_activa && $es_admitido && $usuarios_ok && $parametros_ok) {
                echo json_encode([
                    "status" => "success", 
                    "message" => "Acceso concedido.",
                    "nombre" => $usuario['nombre'] ?? 'Administrador'
                ]);
                exit();
            } else {
                echo json_encode([
                    "status" => "error", 
                    "message" => "Esta cuenta no cumple con las condiciones necesarias."
                ]);
                exit();
            }
        }
    }
    echo json_encode(["status" => "error", "message" => "Cuenta inexistente o credenciales incorrectas."]);

} else {
    echo json_encode(["status" => "error", "message" => "Datos incompletos."]);
}
?>