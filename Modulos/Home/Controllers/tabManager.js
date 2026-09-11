// Genera un identificador único para esta pestaña específica al cargar
const tabId = Math.random().toString(36).substring(2);

// Detecta el proyecto actual desde la URL (ej. /Inicio/ o /Landing_Page/)
// pathArray[1] tomará el nombre de la primera carpeta después del localhost
const pathArray = window.location.pathname.split('/');
const projectName = pathArray[1] || 'general';

// Crea un canal único concatenando el nombre del proyecto dinámicamente
const appChannel = new BroadcastChannel(`cenizas_alejandria_channel_${projectName}`);

let esMaestro = false;
let estaBloqueada = false;

// 1. Pregunta al canal si ya existe un maestro activo controlando el localhost
appChannel.postMessage({ type: 'SOLICITAR_MAESTRO', id: tabId });

// 2. Da un breve margen de espera (150ms). Si nadie responde, coronamos como la pestaña principal
const verificarTronoTimeout = setTimeout(() => {
    if (!estaBloqueada) {
        esMaestro = true;
        console.log(`[TabManager] Instancia maestra establecida. Canal: ${projectName}, ID: ${tabId}`);
    }
}, 150);

// 3. Gestión de la frecuencia de radio del dominio
appChannel.onmessage = (event) => {
    // Si es el maestro legítimo y escucha que una pestaña nueva está buscando un rey:
    if (esMaestro && !estaBloqueada && event.data.type === 'SOLICITAR_MAESTRO') {
        // Le respondemos directamente a esa pestaña usando su ID único para no interferir con otras
        appChannel.postMessage({ type: 'MAESTRO_ALIVE', destinoId: event.data.id });
    }

    // Si es la pestaña nueva y recibe una confirmación de que el maestro está vivo y va dirigida a mi ID:
    if (event.data.type === 'MAESTRO_ALIVE' && event.data.destinoId === tabId) {
        estaBloqueada = true;
        clearTimeout(verificarTronoTimeout); // Cancelamos inmediatamente nuestro intento de ser maestro

        // Renderiza la pantalla de bloqueo de seguridad interactiva con clases desvinculadas de CSS
        document.body.innerHTML = `
            <div class="system-in-use-overlay">
                <div class="system-in-use-card">
                    <h1 class="system-in-use-title">⚠️ Sistema en Uso</h1>
                    <p class="system-in-use-text">
                        Ya tienes una instancia de <strong>Cenizas de Alejandría</strong> abierta en otra pestaña.
                        Por seguridad e integridad de la base de datos, solo se permite una sesión activa a la vez.
                    </p>
                    <p class="system-in-use-subtext">
                        Cierra esta pestaña para continuar.
                    </p>
                </div>
            </div>
        `;
        window.stop(); // Frenamos en seco la carga de los controladores siguientes (mainController, heartbeat, etc.)
    }
};