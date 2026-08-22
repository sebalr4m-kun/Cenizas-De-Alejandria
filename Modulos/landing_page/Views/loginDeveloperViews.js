// Views/loginDeveloperView.js

const LoginDeveloperView = {
    obtenerDrawerHTML: () => {
        return `
            <div id="loginDrawer" class="login-drawer">
                <div id="loginTab" class="login-tab">INGRESAR</div>
                <button id="closeDrawer" class="close-drawer">✕</button>
                
                <div class="lan-info-box" id="lanInfoBox">
                    <span class="lan-icon">🌐</span>
                    <p id="lanStatusText">Estamos buscando una conexión a tu base de datos local...</p>
                </div>

                <h3 id="loginTitle">Iniciar Sesión</h3>
                <form id="loginForm" novalidate>
                    <div id="loginFieldsWrapper" style="display: none;">
                        <div class="form-group">
                            <label for="email">Correo Electrónico</label>
                            <input type="email" id="email" placeholder="ejemplo@escuela.edu.ar" required>
                        </div>
                        <div class="form-group">
                            <label for="password">Contraseña</label>
                            <input type="password" id="password" placeholder="••••••••" required>
                        </div>
                        <button type="submit" class="login-btn">Entrar al Sistema</button>
                    </div>
                </form>
            </div>
        `;
    },

    inicializarComportamiento: () => {
        const loginDrawer = document.getElementById('loginDrawer');
        const loginTab = document.getElementById('loginTab');
        const closeDrawer = document.getElementById('closeDrawer');

        if (!loginDrawer || !loginTab || !closeDrawer) return;

        loginTab.addEventListener('click', () => {
            loginDrawer.classList.toggle('open');
        });

        closeDrawer.addEventListener('click', () => {
            loginDrawer.classList.remove('open');
        });
    }
};