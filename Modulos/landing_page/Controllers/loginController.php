<?php
// Controllers/loginController.php
header("Content-Type: application/json");
require_once __DIR__ . '/../Models/loginModel.php';

function obtenerModuloSeguro($perms, $claveIdeal) {
    if (empty($perms) || !is_array($perms)) {
        return [];
    }
    
    // 1. Intento rápido: Coincidencia exacta
    if (isset($perms[$claveIdeal])) {
        return $perms[$claveIdeal];
    }
    
    $claveNorm = strtolower($claveIdeal);
    $claveNorm = str_replace(['á', 'é', 'í', 'ó', 'ú'], ['a', 'e', 'i', 'o', 'u'], $claveNorm);
    
    foreach ($perms as $k => $v) {
        $kNorm = strtolower($k);
        $kNorm = str_replace(['á', 'é', 'í', 'ó', 'ú'], ['a', 'e', 'i', 'o', 'u'], $kNorm);
        
        if ($kNorm === $claveNorm) {
            return $v;
        }
    }
    
    return [];
}

$data = json_decode(file_get_contents("php://input"));

if (!empty($data->email) && !empty($data->password)) {

    $model = new InicioSesionModel();
    $usuario = $model->buscarUsuarioPorEmail($data->email);
    
    if ($usuario) {
        $hash = $usuario['contrasena'] ?? $usuario['contraseña'] ?? '';
        
        if (password_verify($data->password, $hash)) {
            
            $permisosRaw = $usuario['permisos'] ?? '';
            $permisos = [];
            
            if (!empty($permisosRaw)) {
                $permisos = is_string($permisosRaw) ? json_decode($permisosRaw, true) : $permisosRaw;
            }
            
            if (!is_array($permisos)) {
                $permisos = [];
            }
            
            $moduloUsuarios = obtenerModuloSeguro($permisos, "Usuarios");
            $moduloParametros = obtenerModuloSeguro($permisos, "Parametros");
            $usuarios_ok = isset($moduloUsuarios['ver']) && filter_var($moduloUsuarios['ver'], FILTER_VALIDATE_BOOLEAN) && 
                           isset($moduloUsuarios['editar']) && filter_var($moduloUsuarios['editar'], FILTER_VALIDATE_BOOLEAN);
            $parametros_ok = isset($moduloParametros['ver']) && filter_var($moduloParametros['ver'], FILTER_VALIDATE_BOOLEAN) && 
                             isset($moduloParametros['editar']) && filter_var($moduloParametros['editar'], FILTER_VALIDATE_BOOLEAN);
            $es_admitido = isset($usuario['admitido']) && filter_var($usuario['admitido'], FILTER_VALIDATE_BOOLEAN);
            $es_activa = isset($usuario['estado_cuenta']) && (strtoupper($usuario['estado_cuenta']) === 'ACTIVA');
            
            if ($es_activa && $es_admitido && $usuarios_ok && $parametros_ok) {
                echo json_encode([
                    "status" => "success", 
                    "message" => "Acceso concedido.",
                    "nombre" => $usuario['nombre'] ?? 'Administrador',
                    "rol" => $usuario['rol'] ?? 'Sin Rol',
                    "permisos" => $permisos
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