// Views/adminDashboardViews.js
const AdminDashboardViews = {
    obtenerDashboardHTML: function(nombreUsuario = 'Omen', rol = 'BIBLIOTECARIO') {
        return `
        <div id="adminDashboardOverlay" class="admin-dashboard-overlay">
            <button id="hideDashboardBtn" class="hide-dashboard-btn">Ocultar 🔽</button>
            <div class="admin-dashboard-layout">
                <aside class="admin-sidebar">
                    <h3 class="sidebar-title">GESTIÓN DE PERFIL DE USUARIO</h3>
                    <div class="user-card">
                        <div class="user-avatar">👤 ${nombreUsuario}</div>
                        <div class="user-role">ROL: ${rol}</div>
                    </div>
                    
                    <form id="updateForm" novalidate class="workspace-form">
                        <label>Actualizar Nombre</label>
                        <input type="text" id="updateNombre" placeholder="Tu Nombre" class="workspace-input">
                        
                        <label>Nueva Contraseña (Opcional)</label>
                        <input type="password" id="updateNewPassword" placeholder="***" class="workspace-input">
                        
                        <label>Contraseña Actual (Requerida)</label>
                        <input type="password" id="updateCurrentPassword" placeholder="***" class="workspace-input">
                        <a href="#" id="forgotPasswordDashboard" style="font-size: 0.8rem; color: var(--color-acento); margin-bottom: 15px; text-decoration: none; font-weight: bold;">¿Olvidaste tu contraseña actual?</a>
                        
                        <button type="submit" class="workspace-btn-blue">Actualizar Datos</button>
                    </form>
                    
                    <hr class="workspace-divider">
                    
                    <form id="deleteForm" novalidate class="workspace-form">
                        <label>Zona de Peligro</label>
                        <input type="password" id="deletePassword" placeholder="Contraseña para borrar cuenta" class="workspace-input">
                        <button type="submit" class="workspace-btn-red">Eliminar Cuenta</button>
                    </form>

                    <button id="logoutDashboardBtn" class="logout-owo-btn" style="width: 100%; margin-top: 30px;">CERRAR SESIÓN DEL NAVEGADOR. OWO</button>
                </aside>
                <main class="admin-workspace">
                    <div class="workspace-header">
                        <h2>ESPACIO DE TRABAJO RESERVADO</h2>
                    </div>
                    <div class="workspace-content">
                        <!-- El área principal ahora está despejada para futuras implementaciones -->
                    </div>
                </main>
            </div>
        </div>`;
    }
};