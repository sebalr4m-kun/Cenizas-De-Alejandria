// Controllers/mainController.js
document.addEventListener('DOMContentLoaded', () => {
    const app = document.getElementById('app');

    // =========================================================================
    // 🌐 1. RENDERIZADO ESTRUCTURAL BASE
    // =========================================================================
    app.innerHTML = MainViews.obtenerLandingHTML(PageContent);
    if (typeof LoginDeveloperView !== 'undefined') {
        app.innerHTML += LoginDeveloperView.obtenerDrawerHTML();
        LoginDeveloperView.inicializarComportamiento();
    } else {
        console.error("[ERROR] No se pudo cargar LoginDeveloperView. Verifica el index.php");
    }

    const loginDrawer = document.getElementById('loginDrawer');
    const lanStatusText = document.getElementById('lanStatusText');
    const loginFieldsWrapper = document.getElementById('loginFieldsWrapper');
    const loginForm = document.getElementById('loginForm');

    // =========================================================================
    // 🎛️ 2. CORE: INYECCIÓN Y GESTIÓN DINÁMICA DE LA UI ADMINISTRATIVA
    // =========================================================================
    function activarEntornoAdministrador(nombreAdmin) {
        if (loginDrawer) {
            loginDrawer.classList.remove('open');
            loginDrawer.style.display = 'none';
        }

        document.body.classList.add('admin-mode');

        if (!document.getElementById('adminPanel') && typeof AdminDashboardView !== 'undefined') {
            const adminWrapper = document.createElement('div');
            adminWrapper.innerHTML = AdminDashboardView.obtenerPanelAdminHTML();
            document.body.appendChild(adminWrapper.firstElementChild);
            AdminDashboardView.vincularEventosPanel();
            const panel = document.getElementById('adminPanel');
            if (panel) {
                panel.addEventListener('click', (e) => {
                    const botonCerrar = e.target.closest('button');
                    if (botonCerrar && botonCerrar.textContent.toUpperCase().includes('CERRAR SESIÓN')) {
                        localStorage.clear();
                        window.location.reload();
                    }
                });
            }
        }

        if (typeof iniciarMonitoreoAdmin === 'function') {
            iniciarMonitoreoAdmin();
        }
    }

    // =========================================================================
    // 📡 3. MÓDULO SENSOR: VERIFICACIÓN DE ESTADO INICIAL
    // =========================================================================
    if (localStorage.getItem('nodo_sincronizado') === 'true') {
        const nombrePersistido = localStorage.getItem('usuario_nombre') || 'Administrador';
        activarEntornoAdministrador(nombrePersistido);
    } else {
        fetch('Controllers/checkDbController.php')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (lanStatusText) lanStatusText.innerText = '¡Base de datos encontrada! Inicia tu sesión con una cuenta ADMItida Activa y con acceso a Usuarios y Parámetros!';
                    if (loginFieldsWrapper) loginFieldsWrapper.style.display = 'block';
                } else {
                    if (lanStatusText) lanStatusText.innerText = 'No encontramos tu base de datos, prueba instalar o encender el ejecutable del programa.';
                }
            })
            .catch(error => {
                if (lanStatusText) lanStatusText.innerText = 'No encontramos tu base de datos, prueba instalar o encender el ejecutable del programa.';
                console.error('Error de red al interceptar puerto de datos local:', error);
            });
    }

    // =========================================================================
    // 🔐 4. GESTOR DE ENVÍO DE FORMULARIO (LOGIN)
    // =========================================================================
    if (loginForm) {
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
                    localStorage.setItem('nodo_sincronizado', 'true');
                    localStorage.setItem('usuario_email', email);
                    localStorage.setItem('usuario_nombre', data.nombre);
                    localStorage.setItem('usuario_role', data.rol || 'Sin Rol'); 
                    localStorage.setItem('usuario_rol', data.rol || 'Sin Rol');  
                    localStorage.setItem('usuario_permisos', JSON.stringify(data.permisos || {}));
                    activarEntornoAdministrador(data.nombre);
                    document.dispatchEvent(new CustomEvent('app:notificacion', { 
                        detail: { mensaje: `✅ ¡Sesión iniciada! Bienvenido, ${data.nombre}` } 
                    }));
                } else {
                    mostrarTostada(data.message);
                }
            })
            .catch(error => {
                mostrarTostada('Cuenta inexistente o credenciales incorrectas.');
                console.error('Error crítico en el flujo de autenticación:', error);
            });
        });
    }
});

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

    if (window.toastTimeout) {
        clearTimeout(window.toastTimeout);
    }
    
    window.toastTimeout = setTimeout(() => { 
        toast.classList.remove('show'); 
    }, 4000);
}

document.addEventListener('app:notificacion', (e) => {
    if (typeof mostrarTostada === 'function') {
        mostrarTostada(e.detail.mensaje);
    }
});