// Views/adminDashboardView.js

const AdminDashboardView = {
    obtenerPanelAdminHTML: () => {
        const nombre = localStorage.getItem('usuario_nombre') || 'Administrador';
        const rol = localStorage.getItem('usuario_rol') || 'Sin Rol';
        
        let permisosHTML = '';
        try {
            const permsRaw = localStorage.getItem('usuario_permisos');
            const permisos = permsRaw ? JSON.parse(permsRaw) : {
                "Usuarios": { "ver": true, "editar": true },
                "Parametros": { "ver": true, "editar": true }
            };
            
            permisosHTML = Object.keys(permisos).map(modulo => {
                const verOk = permisos[modulo].ver && (String(permisos[modulo].ver) === 'true' || permisos[modulo].ver === true);
                const editOk = permisos[modulo].editar && (String(permisos[modulo].editar) === 'true' || permisos[modulo].editar === true);
                return `
                    <div style="background: rgba(255,255,255,0.03); padding: 6px; border-radius: 4px; border-left: 3px solid #c0392b; font-size: 11px; margin-top: 4px; box-sizing: border-box; text-align: left;">
                        <span style="font-weight: bold; color: #eee;">${modulo}:</span><br>
                        <span style="color: ${verOk ? '#2ecc71' : '#e74c3c'}; font-weight: 500;">${verOk ? '✔ Ver' : '✘ No Ver'}</span> | 
                        <span style="color: ${editOk ? '#2ecc71' : '#e74c3c'}; font-weight: 500;">${editOk ? '✔ Editar' : '✘ No Editar'}</span>
                    </div>
                `;
            }).join('');
        } catch (e) {
            permisosHTML = '<div style="font-size: 11px; color: #e74c3c; padding: 4px;">Error al indexar la matriz de accesos</div>';
        }

        return `
            <div id="adminPanel" class="admin-panel">
                <div id="adminTongue" class="admin-tongue">Administrar 🔼</div>

                <div class="admin-content" style="display: flex; height: calc(100% - 20px); padding: 10px 20px; gap: 20px; box-sizing: border-box; align-items: stretch;">

                    <div class="admin-sidebar-left" style="width: 260px; min-width: 260px; display: flex; flex-direction: column; justify-content: space-between; color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; box-sizing: border-box;">
                        
                        <div style="display: flex; flex-direction: column; flex: 1; min-height: 0;">
                            <div style="padding-bottom: 10px; text-align: left;">
                                <h4 style="margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; color: #c0392b; font-weight: bold;">
                                    Navegación / Control
                                </h4>
                            </div>
                            
                            <div class="admin-identity-card" style="background: rgba(20, 20, 20, 0.4); border: 2px solid #c0392b; border-radius: 6px; padding: 12px; margin-top: 10px; box-sizing: border-box; text-align: left; flex: 1; display: flex; flex-direction: column; min-height: 0;">
                                <div style="margin-bottom: 6px; overflow: hidden;">
                                    <div class="ticker-container">
                                        <span class="ticker-text panel-admin-name">👤 ${nombre}</span>
                                    </div>
                                </div>
                                <div style="margin-bottom: 10px; overflow: hidden;">
                                    <div class="ticker-container">
                                        <span class="ticker-text panel-admin-role">Rol: ${rol}</span>
                                    </div>
                                </div>
                                
                                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1); flex: 1; display: flex; flex-direction: column; min-height: 0;">
                                    <div style="font-size: 10px; color: #888; text-transform: uppercase; font-weight: bold; margin-bottom: 4px;">Matriz de Accesos:</div>
                                    <div style="display: flex; flex-direction: column; gap: 2px; flex: 1; overflow-y: auto; padding-right: 4px; box-sizing: border-box;">
                                        ${permisosHTML}
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="padding-top: 15px; margin-bottom: 5px;">
                            <button id="btnLogout" style="width: 100%; background-color: #c0392b; color: #ffffff; border: none; padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#a93226'" onmouseout="this.style.backgroundColor='#c0392b'">
                                Cerrar Sesión Del Navegador. OwO
                            </button>
                        </div>
                    </div>
                    
                    <div class="admin-barrier" style="width: 2px; background: linear-gradient(to bottom, #c0392b, #2c3e50, transparent); opacity: 0.75;"></div>
                    
                    <div class="admin-workspace-reserved" style="flex: 1; background-color: rgba(255, 255, 255, 0.02); border: 1px dashed rgba(192, 57, 43, 0.15); border-radius: 6px; position: relative; display: flex; align-items: center; justify-content: center;">
                        <span style="color: rgba(255, 255, 255, 0.1); font-family: sans-serif; font-size: 12px; font-weight: bold; letter-spacing: 3px; text-transform: uppercase; pointer-events: none; user-select: none;">
                            Espacio de Trabajo Reservado
                        </span>
                    </div>

                </div>
            </div>
        `;
    },

    vincularEventosPanel: () => {
        const adminPanel = document.getElementById('adminPanel');
        const adminTongue = document.getElementById('adminTongue');

        if (!adminPanel || !adminTongue) return;
        const clonTongue = adminTongue.cloneNode(true);
        adminTongue.parentNode.replaceChild(clonTongue, adminTongue);

        clonTongue.addEventListener('click', () => {
            adminPanel.classList.toggle('open');
            clonTongue.innerHTML = adminPanel.classList.contains('open') ? 'Ocultar 🔽' : 'Administrar 🔼';
        });
    }
};