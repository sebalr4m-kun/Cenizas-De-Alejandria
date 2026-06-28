// Controllers/mainController.js
document.addEventListener('DOMContentLoaded', () => {
    const app = document.getElementById('app');
    
    // 1. Renderizado inicial de la interfaz de marketing consumiendo la Vista delegada
    app.innerHTML = MainViews.obtenerLandingHTML(PageContent);

    // Captura selectiva de nodos del DOM comercial
    const loginDrawer = document.getElementById('loginDrawer');
    const loginTab = document.getElementById('loginTab');
    const closeDrawer = document.getElementById('closeDrawer');
    const lanStatusText = document.getElementById('lanStatusText');
    const loginFieldsWrapper = document.getElementById('loginFieldsWrapper');
    const loginForm = document.getElementById('loginForm');

    // Manejo elemental de apertura/cierre del Drawer lateral
    loginTab.addEventListener('click', () => loginDrawer.classList.toggle('open'));
    closeDrawer.addEventListener('click', () => loginDrawer.classList.remove('open'));

    // =========================================================================
    // 🎛️ CORE: INYECCIÓN Y GESTIÓN DINÁMICA DE LA UI ADMINISTRATIVA
    // =========================================================================
    function activarEntornoAdministrador(nombreAdmin) {
        // Desvanecer y retirar por completo el Drawer de autenticación
        if (loginDrawer) {
            loginDrawer.classList.remove('open');
            loginDrawer.style.display = 'none';
        }
        
        // Empuja suavemente el layout para que la barra fija superior no solape elementos
        document.body.classList.add('admin-mode');

        // Renderizado de la barra superior con el mensaje de bienvenida exacto solicitado
        if (!document.getElementById('topAdminBar')) {
            const bar = document.createElement('div');
            bar.id = 'topAdminBar';
            bar.className = 'top-admin-bar';
            bar.innerHTML = MainViews.obtenerBarraSuperiorHTML(nombreAdmin);
            document.body.appendChild(bar);
        }

        // Renderizado del Panel Deslizante de Administración
        if (!document.getElementById('adminPanel')) {
            const panel = document.createElement('div');
            panel.id = 'adminPanel';
            panel.className = 'admin-panel';
            panel.innerHTML = MainViews.obtenerPanelAdminHTML();
            document.body.appendChild(panel);

            // Control de comportamiento interactivo de la lengüeta deslizante
            const adminTongue = document.getElementById('adminTongue');
            adminTongue.addEventListener('click', () => {
                panel.classList.toggle('open');
                
                // Efecto de acople perfecto: cambia texto e ícono de dirección
                if (panel.classList.contains('open')) {
                    adminTongue.innerHTML = 'Ocultar 🔽';
                } else {
                    adminTongue.innerHTML = 'Administrar 🔼';
                }
            });
        }
    }

    // =========================================================================
    // 📡 MÓDULO SENSOR: VERIFICACIÓN DE ESTADO INICIAL
    // =========================================================================
    if (localStorage.getItem('nodo_sincronizado') === 'true') {
        const nombrePersistido = localStorage.getItem('usuario_nombre') || 'Administrador';
        activarEntornoAdministrador(nombrePersistido);
    } else {
        // Ejecución del rastreo en tiempo real del motor local
        fetch('Controllers/checkDbController.php')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    lanStatusText.innerText = '¡Base de datos encontrada! Inicia tu sesión con una cuenta ADMItida Activa y con acceso a Usuarios y Parámetros!';
                    loginFieldsWrapper.style.display = 'block'; // Mostrar inputs de credenciales
                } else {
                    lanStatusText.innerText = 'No encontramos tu base de datos, prueba instalar o encender el ejecutable del programa.';
                }
            })
            .catch(error => {
                lanStatusText.innerText = 'No encontramos tu base de datos, prueba instalar o encender el ejecutable del programa.';
                console.error('Error de red al interceptar puerto de datos local:', error);
            });
    }

    // =========================================================================
    // 🔐 GESTOR DE ENVÍO DE FORMULARIO (LOGIN CONTROLADO POR PHP/PYTHON)
    // =========================================================================
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        
        if (!email || !password) {
            mostrarTostada('Por favor, completa todos los campos.');
            return;
        }
        
        fetch('Controllers/loginController.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, password: password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Escritura de pasaporte de persistencia en almacenamiento local
                localStorage.setItem('nodo_sincronizado', 'true');
                localStorage.setItem('usuario_email', email);
                localStorage.setItem('usuario_nombre', data.nombre);
                
                // Mutación estética inmediata del ecosistema web
                activarEntornoAdministrador(data.nombre);
            } else {
                // Alerta nativa controlada (Captura errores de credenciales o permisos faltantes)
                mostrarTostada(data.message);
            }
        })
        .catch(error => {
            mostrarTostada('Cuenta inexistente o credenciales incorrectas.');
        });
    });
});

/**
 * Utilidad global para el despliegue de notificaciones emergentes
 */
function mostrarTostada(mensaje) {
    let toast = document.getElementById('toastError');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toastError';
        toast.className = 'toast-error';
        document.body.appendChild(toast);
    }
    toast.innerText = mensaje;
    toast.classList.add('show');
    
    setTimeout(() => { 
        toast.classList.remove('show'); 
    }, 4000);
}