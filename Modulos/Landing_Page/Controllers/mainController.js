// Controllers/mainController.js
document.addEventListener('DOMContentLoaded', () => {
    const app = document.getElementById('app');

    // Renderiza la Landing
    app.innerHTML = MainViews.obtenerLandingHTML(PageContent);

    // Inyecta el drawer lateral
    app.insertAdjacentHTML('beforeend', LoginDeveloperView.obtenerDrawerHTML());

    // Inyecta el Dashboard de Administración
    let currentUserEmail = localStorage.getItem('user_email') || null;
    let currentUserName = localStorage.getItem('user_nombre') || 'Administrador';
    
    app.insertAdjacentHTML('beforeend', AdminDashboardViews.obtenerDashboardHTML(currentUserName));

    // Variables de estado para las nuevas lógicas de recuperación
    let isDashboardRecovery = false;

    // Sistema de Notificaciones Toast
    function showToast(message) {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = 'toast blue-toast';
        toast.innerHTML = `<span class="toast-icon">ℹ</span><span>${message}</span>`;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('hide');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // Procesador seguro de respuestas HTTP / JSON
    async function handleResponse(res) {
        const text = await res.text();
        try {
            return JSON.parse(text);
        } catch (e) {
            console.error("Respuesta del servidor no es un JSON válido:", text);
            throw new Error(`Error en servidor (${res.status}). Revisa la consola para más detalle.`);
        }
    }

    // Actualiza el texto de la lengüeta y aplica la clase según la sesión
    function checkAuthState() {
        const tabBtn = document.getElementById('btnNavIngresar');
        if (currentUserEmail) {
            if (tabBtn) {
                tabBtn.innerText = 'ADMINISTRAR';
                tabBtn.classList.add('admin-mode');
            }
            const updateNombre = document.getElementById('updateNombre');
            if (updateNombre) updateNombre.value = localStorage.getItem('user_nombre') || '';
        } else {
            if (tabBtn) {
                tabBtn.innerText = 'INGRESAR';
                tabBtn.classList.remove('admin-mode');
            }
        }
    }
    checkAuthState();

    // ==========================================
    // SISTEMA EMERGENTE DE PALABRAS DE RECUPERACIÓN (LOGIN)
    // ==========================================
    function showRecoveryModal(email) {
        const overlay = document.createElement('div');
        overlay.id = 'recoveryModalOverlay';
        overlay.style = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:9999; display:flex; justify-content:center; align-items:center; backdrop-filter: blur(5px);';
        
        overlay.innerHTML = `
            <div style="background:var(--bg-panel, #1e1e1e); padding: 25px; border-radius: 8px; width: 320px; text-align: center; border: 1px solid var(--color-acento, #00d2ff); box-shadow: 0 4px 15px rgba(0, 210, 255, 0.2);">
                <h3 style="color:white; margin-top:0; font-family: monospace;">Verificación de Seguridad</h3>
                <p style="color:#aaa; font-size:0.85rem; margin-bottom: 20px;">Ingresa las 3 palabras enviadas a tu correo. Sepáralas con espacios, comas o diagonales.</p>
                <input type="text" id="recoveryWordsInput" placeholder="palabra1, palabra2, palabra3" style="width:90%; padding:10px; margin-bottom:15px; background:#111; color:white; border:1px solid #444; border-radius:4px; outline: none; font-family: monospace;">
                <button id="verifyRecoveryBtn" style="background:var(--color-acento, #00d2ff); color:black; border:none; padding:10px; border-radius:4px; cursor:pointer; font-weight:bold; width:95%; margin-bottom: 10px; transition: 0.3s;">Autenticar</button>
                <button id="closeRecoveryBtn" style="background:transparent; color:#888; border:none; cursor:pointer; font-size:0.85rem; width:100%; padding: 5px;">Cancelar</button>
            </div>
        `;
        document.body.appendChild(overlay);

        document.getElementById('verifyRecoveryBtn').addEventListener('click', () => {
            const words = document.getElementById('recoveryWordsInput').value;
            if (!words) {
                showToast("Debes ingresar las palabras.");
                return;
            }
            
            fetch('Controllers/authController.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'verify_words', email: email, words: words })
            })
            .then(handleResponse)
            .then(data => {
                if (data.status === 'success') {
                    document.body.removeChild(overlay);
                    showToast(data.message);
                    localStorage.setItem('user_email', data.email);
                    localStorage.setItem('user_nombre', data.nombre);
                    currentUserEmail = data.email;
                    checkAuthState();
                    document.getElementById('loginDrawer').classList.remove('open');
                    document.getElementById('adminDashboardOverlay').classList.add('open');
                } else {
                    showToast(data.message);
                }
            })
            .catch(err => showToast(err.message || "Error al conectar con el servidor."));
        });

        document.getElementById('closeRecoveryBtn').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
    }

    // ==========================================
    // SISTEMA EMERGENTE DE CONFIRMACIÓN DE REGISTRO
    // ==========================================
    function showRegistrationModal(email) {
        const overlay = document.createElement('div');
        overlay.id = 'registrationModalOverlay';
        overlay.style = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:9999; display:flex; justify-content:center; align-items:center; backdrop-filter: blur(5px);';
        
        overlay.innerHTML = `
            <div style="background:var(--bg-panel, #1e1e1e); padding: 25px; border-radius: 8px; width: 320px; text-align: center; border: 1px solid var(--color-acento, #00d2ff); box-shadow: 0 4px 15px rgba(0, 210, 255, 0.2);">
                <h3 style="color:white; margin-top:0; font-family: monospace;">Confirmar Registro</h3>
                <p style="color:#aaa; font-size:0.85rem; margin-bottom: 20px;">Se han enviado 3 palabras de seguridad a <b>${email}</b>. Ingrésalas para activar tu cuenta.</p>
                <input type="text" id="regWordsInput" placeholder="palabra1, palabra2, palabra3" style="width:90%; padding:10px; margin-bottom:15px; background:#111; color:white; border:1px solid #444; border-radius:4px; outline: none; font-family: monospace;">
                <button id="verifyRegBtn" style="background:var(--color-acento, #00d2ff); color:black; border:none; padding:10px; border-radius:4px; cursor:pointer; font-weight:bold; width:95%; margin-bottom: 10px; transition: 0.3s;">Crear Cuenta</button>
                <button id="closeRegBtn" style="background:transparent; color:#888; border:none; cursor:pointer; font-size:0.85rem; width:100%; padding: 5px;">Cancelar</button>
            </div>
        `;
        document.body.appendChild(overlay);

        document.getElementById('verifyRegBtn').addEventListener('click', () => {
            const words = document.getElementById('regWordsInput').value;
            if (!words) {
                showToast("Debes ingresar las palabras.");
                return;
            }
            
            fetch('Controllers/authController.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'confirm_register', words: words })
            })
            .then(handleResponse)
            .then(data => {
                showToast(data.message);
                if (data.status === 'success') {
                    document.body.removeChild(overlay);
                    
                    let correosRegistrados = JSON.parse(localStorage.getItem('correos_registrados')) || [];
                    if (!correosRegistrados.includes(email)) {
                        correosRegistrados.push(email);
                        localStorage.setItem('correos_registrados', JSON.stringify(correosRegistrados));
                    }
                    
                    const authForm = document.getElementById('authForm');
                    if (authForm) authForm.reset();
                    
                    const loginRadio = document.querySelector('input[name="authMode"][value="login"]');
                    if (loginRadio) {
                        loginRadio.checked = true;
                        loginRadio.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            })
            .catch(err => showToast(err.message || "Error al confirmar registro."));
        });

        document.getElementById('closeRegBtn').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
    }

    // ==========================================
    // SISTEMA EMERGENTE DE RECUPERACIÓN EN DASHBOARD
    // ==========================================
    function showDashboardRecoveryModal(email) {
        const overlay = document.createElement('div');
        overlay.id = 'dashboardRecoveryOverlay';
        overlay.style = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:9999; display:flex; justify-content:center; align-items:center; backdrop-filter: blur(5px);';
        
        overlay.innerHTML = `
            <div style="background:var(--bg-panel, #1e1e1e); padding: 25px; border-radius: 8px; width: 320px; text-align: center; border: 1px solid var(--color-acento, #00d2ff); box-shadow: 0 4px 15px rgba(0, 210, 255, 0.2);">
                <h3 style="color:white; margin-top:0; font-family: monospace;">Validación de Identidad</h3>
                <p style="color:#aaa; font-size:0.85rem; margin-bottom: 20px;">Ingresa las 3 palabras enviadas a tu correo para autorizar los cambios.</p>
                <input type="text" id="dashWordsInput" placeholder="palabra1, palabra2, palabra3" style="width:90%; padding:10px; margin-bottom:15px; background:#111; color:white; border:1px solid #444; border-radius:4px; outline: none; font-family: monospace;">
                <button id="verifyDashBtn" style="background:var(--color-acento, #00d2ff); color:black; border:none; padding:10px; border-radius:4px; cursor:pointer; font-weight:bold; width:95%; margin-bottom: 10px; transition: 0.3s;">Autorizar</button>
                <button id="closeDashBtn" style="background:transparent; color:#888; border:none; cursor:pointer; font-size:0.85rem; width:100%; padding: 5px;">Cancelar</button>
            </div>
        `;
        document.body.appendChild(overlay);

        document.getElementById('verifyDashBtn').addEventListener('click', () => {
            const words = document.getElementById('dashWordsInput').value;
            if (!words) {
                showToast("Debes ingresar las palabras.");
                return;
            }
            
            fetch('Controllers/authController.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'verify_words', email: email, words: words })
            })
            .then(handleResponse)
            .then(data => {
                if (data.status === 'success') {
                    document.body.removeChild(overlay);
                    isDashboardRecovery = true;
                    
                    const currentPasswordField = document.getElementById('updateCurrentPassword');
                    if (currentPasswordField) {
                        currentPasswordField.style.display = 'none';
                        const label = currentPasswordField.previousElementSibling;
                        if (label && label.tagName === 'LABEL') label.style.display = 'none';
                    }
                    
                    showToast("Validación exitosa. Puedes actualizar tus datos sin ingresar tu contraseña actual.");
                } else {
                    showToast(data.message);
                }
            })
            .catch(err => showToast(err.message || "Error al conectar con el servidor."));
        });

        document.getElementById('closeDashBtn').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
    }

    // ==========================================
    // DELEGACIÓN GLOBAL DE CLICS
    // ==========================================
    document.addEventListener('click', (e) => {
        // Lengüeta de ingreso / administrar
        const tabBtn = e.target.closest('#btnNavIngresar');
        if (tabBtn) {
            e.preventDefault();
            const loginDrawer = document.getElementById('loginDrawer');
            const adminDashboard = document.getElementById('adminDashboardOverlay');
            
            if (currentUserEmail) {
                if (adminDashboard) adminDashboard.classList.add('open');
                if (loginDrawer) loginDrawer.classList.remove('open');
            } else {
                if (loginDrawer) loginDrawer.classList.toggle('open');
            }
        }

        // Cerrar drawer
        const closeDrawer = e.target.closest('#closeDrawer');
        if (closeDrawer) {
            e.preventDefault();
            const loginDrawer = document.getElementById('loginDrawer');
            if (loginDrawer) loginDrawer.classList.remove('open');
        }

        // Ocultar dashboard
        const hideDashboard = e.target.closest('#hideDashboardBtn');
        if (hideDashboard) {
            e.preventDefault();
            const adminDashboard = document.getElementById('adminDashboardOverlay');
            if (adminDashboard) adminDashboard.classList.remove('open');
        }

        // Cerrar sesión
        const logoutBtn = e.target.closest('#logoutDashboardBtn');
        if (logoutBtn) {
            e.preventDefault();
            localStorage.clear();
            location.reload();
        }

        // Recuperación desde el Login
        const forgotLogin = e.target.closest('#forgotPasswordLogin');
        if (forgotLogin) {
            e.preventDefault();
            const emailInput = document.getElementById('email');
            const email = emailInput ? emailInput.value.trim() : '';
            
            if (!email) {
                showToast("Por favor, ingresa tu correo electrónico arriba para solicitar la recuperación.");
                return;
            }

            fetch('Controllers/authController.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'recover_login', email: email })
            })
            .then(handleResponse)
            .then(data => {
                showToast(data.message);
                if (data.status === 'success') {
                    showRecoveryModal(email);
                }
            })
            .catch(err => {
                console.error("Detalle de fallo en recuperación:", err);
                showToast(err.message || "Error crítico de red.");
            });
        }

        // Recuperación desde el Dashboard (Bypass seguro con palabras)
        const forgotDashboard = e.target.closest('#forgotPasswordDashboard');
        if (forgotDashboard) {
            e.preventDefault();
            
            if (!currentUserEmail) {
                showToast("Error de sesión. Recarga la página.");
                return;
            }

            fetch('Controllers/authController.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'recover_login', email: currentUserEmail })
            })
            .then(handleResponse)
            .then(data => {
                showToast(data.message);
                if (data.status === 'success') {
                    showDashboardRecoveryModal(currentUserEmail);
                }
            })
            .catch(err => {
                console.error("Detalle de fallo en recuperación de panel:", err);
                showToast(err.message || "Error crítico de red.");
            });
        }
    });

    // ==========================================
    // DELEGACIÓN GLOBAL DE CAMBIOS (RADIOS)
    // ==========================================
    document.addEventListener('change', (e) => {
        if (e.target.name === 'authMode') {
            const isRegister = e.target.value === 'register';
            const nameField = document.getElementById('nameField');
            const submitBtn = document.getElementById('authSubmitBtn');
            const forgotLoginBtn = document.getElementById('forgotPasswordLogin');

            if (nameField) nameField.style.display = isRegister ? 'block' : 'none';
            if (submitBtn) submitBtn.innerText = isRegister ? 'Registrarse' : 'Entrar al Sistema';
            if (forgotLoginBtn) forgotLoginBtn.style.display = isRegister ? 'none' : 'block';
        }
    });

    // ==========================================
    // DELEGACIÓN GLOBAL DE FORMULARIOS (SUBMIT)
    // ==========================================
    document.addEventListener('submit', (e) => {
        
        // Autenticación (Registro / Login)
        if (e.target.id === 'authForm') {
            e.preventDefault();
            
            const selectedRadio = document.querySelector('input[name="authMode"]:checked');
            const isRegister = selectedRadio ? selectedRadio.value === 'register' : false;
            
            const action = isRegister ? 'pre_register' : 'login';
            
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const nombreInput = document.getElementById('nombre');
            const nombre = nombreInput ? nombreInput.value.trim() : '';

            if (!email || !password || (isRegister && !nombre)) {
                showToast("Por favor, completa todos los campos requeridos.");
                return;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/;
            if (!emailRegex.test(email)) {
                showToast("El formato del correo es inválido. Usa: usuario@dominio.com");
                return;
            }

            if (isRegister && !/^(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/.test(password)) {
                showToast("La contraseña requiere 8 caracteres y 1 carácter especial.");
                return;
            }

            let correosRegistrados = JSON.parse(localStorage.getItem('correos_registrados')) || [];
            if (isRegister && correosRegistrados.includes(email)) {
                showToast("Este correo ya está registrado en el sistema. Intenta iniciar sesión.");
                return;
            }

            fetch('Controllers/authController.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, email, password, nombre })
            })
            .then(handleResponse)
            .then(data => {
                showToast(data.message);
                
                if (data.status === 'success') {
                    if (isRegister) {
                        showRegistrationModal(email);
                    } else {
                        localStorage.setItem('user_email', data.email);
                        localStorage.setItem('user_nombre', data.nombre);
                        currentUserEmail = data.email;
                        checkAuthState();
                        document.getElementById('loginDrawer').classList.remove('open');
                        document.getElementById('adminDashboardOverlay').classList.add('open');
                    }
                }
            })
            .catch(err => showToast(err.message || "Error de conexión con el servidor."));
        }

        // Actualizar Perfil
        if (e.target.id === 'updateForm') {
            e.preventDefault();
            const nombre = document.getElementById('updateNombre').value.trim();
            const newPassword = document.getElementById('updateNewPassword').value;
            const currentPasswordElement = document.getElementById('updateCurrentPassword');
            const currentPassword = currentPasswordElement ? currentPasswordElement.value : '';

            if (!nombre) {
                showToast("El nombre es obligatorio.");
                return;
            }

            if (!isDashboardRecovery && !currentPassword) {
                showToast("La contraseña actual es obligatoria para verificar los cambios.");
                return;
            }

            const actionType = isDashboardRecovery ? 'update_bypass' : 'update';

            fetch('Controllers/authController.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: actionType, email: currentUserEmail, nombre, newPassword, currentPassword })
            })
            .then(handleResponse)
            .then(data => {
                showToast(data.message);
                if (data.status === 'success') {
                    localStorage.setItem('user_nombre', nombre);
                    setTimeout(() => location.reload(), 1500); 
                }
            })
            .catch(err => showToast(err.message || "Error al actualizar perfil."));
        }

        // Eliminar Cuenta
        if (e.target.id === 'deleteForm') {
            e.preventDefault();
            const password = document.getElementById('deletePassword').value;
            
            if (!password) {
                showToast("Ingresa tu contraseña para eliminar la cuenta.");
                return;
            }

            fetch('Controllers/authController.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'delete', email: currentUserEmail, password })
            })
            .then(handleResponse)
            .then(data => {
                showToast(data.message);
                if (data.status === 'success') {
                    setTimeout(() => {
                        localStorage.clear();
                        location.reload();
                    }, 1500);
                }
            })
            .catch(err => showToast(err.message || "Error al intentar eliminar la cuenta."));
        }
    });
});