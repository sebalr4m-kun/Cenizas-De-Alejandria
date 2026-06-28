// Views/mainViews.js

const MainViews = {
    /**
     * Genera el HTML de la Landing Page Comercial
     */
    obtenerLandingHTML: (content) => {
        return `
            <header>
                <h1>${content.hero.title}</h1>
                <h2>${content.hero.tagline}</h2>
                <p>${content.hero.description}</p>
                <button id="heroCta">${content.hero.cta}</button>
            </header>
            
            <section id="problem">
                <h3>${content.problem.title}</h3>
                <ul>
                    ${content.problem.items.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </section>
            
            <section id="features">
                ${content.features.map(f => `
                    <div class="feature-card">
                        <h4>${f.title}</h4>
                        <p>${f.desc}</p>
                    </div>
                `).join('')}
            </section>
            
            <section id="pricing">
                <h3>${content.pricing.title}</h3>
                <div class="price-card">
                    <h4>${content.pricing.type}</h4>
                    <div class="price-tag">${content.pricing.price}</div>
                    <p><em>${content.pricing.period}</em></p>
                    <ul>
                        ${content.pricing.benefits.map(b => `<li>${b}</li>`).join('')}
                    </ul>
                </div>
            </section>

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

    /**
     * Componente de la Barra de Navegación del Administrador
     */
    obtenerBarraSuperiorHTML: (nombreAdmin) => {
        return `<span>🔥 Bienvenido, <strong>${nombreAdmin}</strong></span>`;
    },

    /**
     * Componente del Panel de Consola Deslizante
     */
    obtenerPanelAdminHTML: () => {
        return `
            <div id="adminTongue" class="admin-tongue">Administrar 🔼</div>
            <div class="admin-content">
                <h2>⚙️ Consola de Sincronización del Nodo LAN</h2>
                <hr style="border: 0; border-top: 1px solid #dcdde1; margin-bottom: 20px;">
                <p>Has iniciado sesión con éxito. El puente seguro con tu software de escritorio está establecido de forma permanente.</p>
                <p>Próximamente verás aquí las herramientas de clonación de bases de datos para tus terminales hijas.</p>
            </div>
        `;
    }
};