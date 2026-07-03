// Controllers/heartbeat.js

function iniciarMonitoreoAdmin() {
    if (localStorage.getItem('nodo_sincronizado') !== 'true') return;

    const emailUsuario = localStorage.getItem('usuario_email');
    if (!emailUsuario) return;

    setInterval(() => {
        fetch(`Controllers/verificar_sesion.php?email=${encodeURIComponent(emailUsuario)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) return;

                if (!data.activo) {
                    if (data.razon === 'privilegios_perdidos') {
                        ejecutarExpulsionAdmin();
                    }
                } else {
                    const panelNameSpan = document.querySelector('.panel-admin-name');
                    if (panelNameSpan && panelNameSpan.textContent !== `👤 ${data.nombre}`) {
                        panelNameSpan.textContent = `👤 ${data.nombre}`;
                        localStorage.setItem('usuario_nombre', data.nombre);
                        console.log(`[Heartbeat] Nombre sincronizado en panel lateral: ${data.nombre}`);
                    }

                    const permisosLocalesStr = localStorage.getItem('usuario_permisos') || '{}';
                    const permisosRemotosStr = JSON.stringify(data.permisos || {});
                    const rolLocal = localStorage.getItem('usuario_rol');

                    if (permisosLocalesStr !== permisosRemotosStr || rolLocal !== data.rol) {
                        localStorage.setItem('usuario_permisos', permisosRemotosStr);
                        localStorage.setItem('usuario_rol', data.rol || 'Sin Rol');
                        localStorage.setItem('usuario_role', data.rol || 'Sin Rol');
                        
                        const adminPanel = document.getElementById('adminPanel');
                        if (adminPanel && typeof AdminDashboardView !== 'undefined') {
                            const estabaAbierto = adminPanel.classList.contains('open');
                            
                            adminPanel.outerHTML = AdminDashboardView.obtenerPanelAdminHTML();
                            
                            const nuevoAdminPanel = document.getElementById('adminPanel');
                            if (nuevoAdminPanel && estabaAbierto) {
                                nuevoAdminPanel.classList.add('open');
                                const nuevoTongue = document.getElementById('adminTongue');
                                if (nuevoTongue) nuevoTongue.innerHTML = 'Ocultar 🔽';
                            }
                            
                            AdminDashboardView.vincularEventosPanel();
                            
                            console.log('[Heartbeat] Matriz RBAC y vistas dinámicas actualizadas preservando la lengüeta.');
                        }
                    }
                }
            })
            .catch(err => console.error("Error en el latido de seguridad:", err));
    }, 4000); 
}

function ejecutarExpulsionAdmin() {
    console.warn("[SEGURIDAD] Se detectó pérdida de privilegios. Desmantelando entorno administrativo...");
    
    localStorage.clear();
    
    const adminPanel = document.getElementById('adminPanel');
    if (adminPanel) adminPanel.remove();
    
    document.body.classList.remove('admin-mode');

    if (typeof mostrarTostada === 'function') {
        mostrarTostada("⚠️ Privilegios perdidos: Tu cuenta ya no cumple las condiciones administrativas.");
    } else {
        alert("⚠️ Privilegios perdidos: Tu cuenta ya no cumple las condiciones administrativas.");
    }
    
    setTimeout(() => {
        window.location.reload();
    }, 3500);
}

document.addEventListener('DOMContentLoaded', iniciarMonitoreoAdmin);