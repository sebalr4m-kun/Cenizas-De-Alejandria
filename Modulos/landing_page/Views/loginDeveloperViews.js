// Views/loginDeveloperViews.js
const LoginDeveloperView = {
    obtenerDrawerHTML: function() {
        return `
        <div id="loginDrawer" class="login-drawer">
            <div id="btnNavIngresar" class="login-tab">INGRESAR</div>
            <button id="closeDrawer" class="close-drawer">&times;</button>
            
            <div id="contentIngresar" class="drawer-content active">
                <div class="lan-info-box">
                    <span class="lan-icon">🌐</span>
                    <p id="lanStatusText">Esta cuenta es para administrar tus versiones compradas, no administrar tu base de datos local.</p>
                </div>
                <h3>Iniciar Sesión</h3>
                <div class="toggle-auth" style="margin-bottom: 15px;">
                    <label><input type="radio" name="authMode" value="login" checked> Iniciar Sesión</label>
                    <label style="margin-left: 10px;"><input type="radio" name="authMode" value="register"> Registrarse</label>
                </div>
                <form id="authForm" class="auth-form" novalidate>
                    <div id="nameField" class="form-group" style="display:none;">
                        <label>NOMBRE</label>
                        <input type="text" id="nombre" placeholder="Nombre de la cuenta" class="drawer-input">
                    </div>
                    <div class="form-group">
                        <label>CORREO ELECTRÓNICO</label>
                        <input type="email" id="email" placeholder="ejemplo@escuela.edu.ar" class="drawer-input">
                    </div>
                    <div class="form-group">
                        <label>CONTRASEÑA</label>
                        <input type="password" id="password" placeholder="********" class="drawer-input">
                        <a href="#" id="forgotPasswordLogin" style="font-size: 0.8rem; color: var(--color-acento); margin-top: 8px; text-decoration: none; font-weight: bold;">¿Olvidaste tu contraseña?</a>
                    </div>
                    <button type="submit" id="authSubmitBtn" class="login-btn">Entrar al Sistema</button>
                </form>
            </div>
        </div>
        <div id="toastContainer" class="toast-container"></div>`;
    },
    inicializarComportamiento: function() {
        // Inicialización delegada a mainController.js
    }
};