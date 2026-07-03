<?php
// Controllers/verificar_sesion.php
header('Content-Type: application/json');

$host = 'localhost';
$db   = 'bibliotecabd';
$user = 'root';
$pass = '';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8", $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);
} catch (PDOException $e) {
    echo json_encode(['error' => 'Error de conexión']);
    exit;
}

function obtenerModuloSeguro($perms, $claveIdeal) {
    if (empty($perms) || !is_array($perms)) {
        return [];
    }
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

$email = isset($_GET['email']) ? trim($_GET['email']) : '';

if (empty($email)) {
    echo json_encode(['activo' => false, 'razon' => 'Sin sesion valida']);
    exit;
}

try {
    $stmt = $pdo->prepare("
        SELECT u.nombre, u.estado_cuenta, p.admitido, p.permisos, p.nombre AS rol 
        FROM usuarios u
        JOIN param_tipos_usuario p ON u.id_tipo_usuario = p.id_tipo_usuario
        WHERE u.email = ?
    ");
    $stmt->execute([$email]);
    $usuario = $stmt->fetch();

    if (!$usuario || strtoupper($usuario['estado_cuenta']) !== 'ACTIVA' || intval($usuario['admitido']) !== 1) {
        echo json_encode(['activo' => false, 'razon' => 'privilegios_perdidos']);
        exit;
    }

    // Decodificar los permisos de forma segura
    $permisos = json_decode($usuario['permisos'], true) ?: [];
    
    $moduloUsuarios = obtenerModuloSeguro($permisos, 'Usuarios');
    $moduloParametros = obtenerModuloSeguro($permisos, 'Parametros');

    $usuarios_ok = isset($moduloUsuarios['ver']) && filter_var($moduloUsuarios['ver'], FILTER_VALIDATE_BOOLEAN) && 
                   isset($moduloUsuarios['editar']) && filter_var($moduloUsuarios['editar'], FILTER_VALIDATE_BOOLEAN);
                   
    $parametros_ok = isset($moduloParametros['ver']) && filter_var($moduloParametros['ver'], FILTER_VALIDATE_BOOLEAN) && 
                     isset($moduloParametros['editar']) && filter_var($moduloParametros['editar'], FILTER_VALIDATE_BOOLEAN);

    if (!$usuarios_ok || !$parametros_ok) {
        echo json_encode(['activo' => false, 'razon' => 'privilegios_perdidos']);
        exit;
    }

    echo json_encode([
        'activo' => true,
        'nombre' => $usuario['nombre'],
        'rol' => $usuario['rol'] ?? 'Sin Rol',
        'permisos' => $permisos
    ]);

} catch (Exception $e) {
    echo json_encode(['error' => 'Error en consulta general']);
}
?>