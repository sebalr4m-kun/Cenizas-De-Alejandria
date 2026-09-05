<?php
// Controllers/authController.php
session_start(); 
header("Content-Type: application/json");
require_once __DIR__ . '/../Models/authModel.php';

// Clases requeridas para PHPMailer
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

// Carga manual de los archivos de PHPMailer
require_once __DIR__ . '/../PHPMailer/src/Exception.php';
require_once __DIR__ . '/../PHPMailer/src/PHPMailer.php';
require_once __DIR__ . '/../PHPMailer/src/SMTP.php';

$data = json_decode(file_get_contents("php://input"));
if (!$data || !isset($data->action)) {
    echo json_encode(["status" => "error", "message" => "Acción no especificada."]);
    exit();
}

$model = new AuthModel();

switch ($data->action) {
    case 'pre_register':
        if ($model->getUserByEmail($data->email)) {
            echo json_encode(["status" => "error", "message" => "El correo ya está registrado."]);
        } else {
            // Generar 3 palabras dinámicas usando el modelo de la base de datos
            $palabrasElegidas = $model->getSecurityWords(3);
            
            if (count($palabrasElegidas) < 3) {
                echo json_encode(["status" => "error", "message" => "Error interno: No hay suficientes palabras en la base de datos."]);
                break;
            }
            
            $_SESSION['registro_pendiente'] = [
                'nombre' => $data->nombre,
                'email' => $data->email,
                'password' => $data->password,
                'words' => $palabrasElegidas
            ];
            
            $palabrasString = implode(" ", $palabrasElegidas);
            
            $mail = new PHPMailer(true);
            try {
                $mail->isSMTP();
                $mail->SMTPDebug = 0;
                $mail->Host       = 'smtp.gmail.com';
                $mail->SMTPAuth   = true;
                $mail->Username   = '414nX4rd@gmail.com'; 
                $mail->Password   = 'lvjzabsitxrxwqmr';   
                $mail->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS;
                $mail->Port       = 465;

                $mail->setFrom('414nX4rd@gmail.com', 'Cenizas de Alejandria');
                $mail->addAddress($data->email, $data->nombre);

                $mail->isHTML(false);
                $mail->Subject = 'Codigo de seguridad para registro';
                $mail->Body    = "Tus 3 palabras de seguridad para crear la cuenta son:\n\n" . $palabrasString . "\n\nIngresalas en el orden correcto para finalizar el registro.";
                $mail->SMTPOptions = array('ssl' => array('verify_peer' => false, 'verify_peer_name' => false, 'allow_self_signed' => true));
                $mail->send();
                
                echo json_encode(["status" => "success", "message" => "Se ha enviado un correo con 3 palabras. Revisa tu bandeja de entrada."]);
            } catch (Exception $e) {
                echo json_encode(["status" => "error", "message" => "Error de envío SMTP: {$mail->ErrorInfo}"]);
            }
        }
        break;

    case 'confirm_register':
        $inputWordsStr = isset($data->words) ? $data->words : '';
        $cleanInput = preg_replace('/[,\\/]/', ' ', $inputWordsStr);
        $inputArray = array_values(array_filter(explode(' ', strtolower(trim($cleanInput)))));
        
        if (isset($_SESSION['registro_pendiente'])) {
            // Normalizar a minúsculas lo que viene de la base de datos
            $expectedArray = array_map('strtolower', $_SESSION['registro_pendiente']['words']);
            
            if ($inputArray === $expectedArray) {
                $datos = $_SESSION['registro_pendiente'];
                
                if ($model->createUser($datos['nombre'], $datos['email'], $datos['password'])) {
                    unset($_SESSION['registro_pendiente']);
                    echo json_encode(["status" => "success", "message" => "Cuenta creada exitosamente. Ya puedes ingresar."]);
                } else {
                    echo json_encode(["status" => "error", "message" => "Error interno al crear la cuenta."]);
                }
            } else {
                echo json_encode(["status" => "error", "message" => "Las palabras no coinciden o no están en el orden correcto."]);
            }
        } else {
            echo json_encode(["status" => "error", "message" => "El tiempo expiró o no hay un registro pendiente activo."]);
        }
        break;
        
    case 'login':
        $user = $model->getUserByEmail($data->email);
        if ($user && password_verify($data->password, $user['contraseña'])) {
            echo json_encode(["status" => "success", "message" => "Acceso concedido.", "nombre" => $user['nombre'], "email" => $user['email']]);
        } else {
            echo json_encode(["status" => "error", "message" => "Cuenta inexistente o credenciales incorrectas."]);
        }
        break;
        
    case 'update':
        $user = $model->getUserByEmail($data->email);
        if ($user && password_verify($data->currentPassword, $user['contraseña'])) {
            $model->updateUser($data->email, $data->nombre, !empty($data->newPassword) ? $data->newPassword : null);
            echo json_encode(["status" => "success", "message" => "Datos actualizados correctamente."]);
        } else {
            echo json_encode(["status" => "error", "message" => "Contraseña actual incorrecta."]);
        }
        break;

    case 'update_bypass':
        $user = $model->getUserByEmail($data->email);
        if ($user) {
            $model->updateUser($data->email, $data->nombre, !empty($data->newPassword) ? $data->newPassword : null);
            echo json_encode(["status" => "success", "message" => "Datos actualizados correctamente mediante omisión temporal."]);
        } else {
            echo json_encode(["status" => "error", "message" => "Usuario no encontrado en la base de datos."]);
        }
        break;
        
    case 'delete':
        $user = $model->getUserByEmail($data->email);
        if ($user && password_verify($data->password, $user['contraseña'])) {
            $model->deleteUser($data->email);
            echo json_encode(["status" => "success", "message" => "Cuenta eliminada de forma permanente."]);
        } else {
            echo json_encode(["status" => "error", "message" => "Contraseña incorrecta."]);
        }
        break;

    case 'recover_login':
        $user = $model->getUserByEmail($data->email);
        if ($user) {
            // Generar 3 palabras dinámicas usando el modelo de la base de datos
            $palabrasElegidas = $model->getSecurityWords(3);
            
            if (count($palabrasElegidas) < 3) {
                echo json_encode(["status" => "error", "message" => "Error interno: No hay suficientes palabras en la base de datos."]);
                break;
            }
            
            $_SESSION['recovery_words_' . $data->email] = $palabrasElegidas;
            $palabrasString = implode(" ", $palabrasElegidas);
            
            $mail = new PHPMailer(true);
            
            try {
                $mail->isSMTP();
                $mail->SMTPDebug = 0; 
                $mail->Host       = 'smtp.gmail.com';
                $mail->SMTPAuth   = true;
                $mail->Username   = '414nX4rd@gmail.com'; 
                $mail->Password   = 'lvjzabsitxrxwqmr';   
                $mail->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS;
                $mail->Port       = 465;

                $mail->setFrom('414nX4rd@gmail.com', 'Cenizas de Alejandria');
                $mail->addAddress($data->email, $user['nombre']);

                $mail->isHTML(false);
                $mail->Subject = 'Codigo de acceso seguro';
                $mail->Body    = "Tus 3 palabras de acceso son:\n\n" . $palabrasString . "\n\nIngresalas en el orden correcto.";
                $mail->SMTPOptions = array('ssl' => array('verify_peer' => false, 'verify_peer_name' => false, 'allow_self_signed' => true));
                $mail->send();
                echo json_encode(["status" => "success", "message" => "Se ha enviado un correo con 3 palabras. Revisa tu bandeja de entrada."]);
            } catch (Exception $e) {
                echo json_encode(["status" => "error", "message" => "Error de envío SMTP: {$mail->ErrorInfo}"]);
            }
        } else {
            echo json_encode(["status" => "success", "message" => "Si el correo es válido, se ha enviado un mensaje con las palabras."]);
        }
        break;

    case 'verify_words':
        $inputWordsStr = $data->words;
        $cleanInput = preg_replace('/[,\\/]/', ' ', $inputWordsStr);
        $inputArray = array_values(array_filter(explode(' ', strtolower(trim($cleanInput)))));
        
        $sessionKey = 'recovery_words_' . $data->email;
        
        if (isset($_SESSION[$sessionKey])) {
            // Normalizar a minúsculas lo que viene de la base de datos
            $expectedArray = array_map('strtolower', $_SESSION[$sessionKey]);
            
            if ($inputArray === $expectedArray) {
                $user = $model->getUserByEmail($data->email);
                if ($user) {
                    unset($_SESSION[$sessionKey]); 
                    echo json_encode(["status" => "success", "message" => "Palabras verificadas. Ingresando...", "nombre" => $user['nombre'], "email" => $user['email']]);
                } else {
                    echo json_encode(["status" => "error", "message" => "Usuario comprometido. Contacta soporte."]);
                }
            } else {
                echo json_encode(["status" => "error", "message" => "Las palabras no coinciden o no están en el orden correcto."]);
            }
        } else {
            echo json_encode(["status" => "error", "message" => "El tiempo expiró o no solicitaste un código recientemente."]);
        }
        break;
}
?>