var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVAs Maetros
// 0x1323500 - UIExpedition.SendExpedition
// 0x221DDF0 - PointCode.WriteMP (Para cambiar el destino)
var targetSend = baseAddr.add(0x1323500);
var targetWrite = baseAddr.add(0x221DDF0);

var autoTargetHost = 507; // Zona
var autoTargetPoint = 59; // Punto

function puppeteerMarch() {
    console.log('[🚀] Lanzando Inyector v13.12 (The Puppeteer)...');

    // 1. Interceptamos la escritura de coordenadas para cambiarlas "en el vuelo"
    var hookWrite = Interceptor.attach(targetWrite, {
        onEnter: function(args) {
            // PointCode.WriteMP(MP pak, ushort HostID, byte PointID)
            console.log('[📍] Redirigiendo marcha al Bosque (Zona 507, Punto 59)...');
            args[1] = ptr(autoTargetHost);
            args[2] = ptr(autoTargetPoint);
            
            // Una vez que lo cambiamos una vez, nos desconectamos para no afectar marchas futuras
            hookWrite.detach();
        }
    });

    // 2. Buscamos la instancia activa de la ventana UIExpedition
    // Para simplificar, hookeamos el método SendExpedition y lo invocamos
    // Pero necesitamos una instancia válida. 
    // TRUCO: Vamos a enganchar el próximo clic que hagas y "Secuestrarlo".
    
    console.log('[📡] TITIRITERO ACTIVO. Por favor, haz clic en el botón "Recolectar" del juego una última vez.');
    console.log('[!] El bot tomará el control total de ese clic y lo redirigirá a los recursos.');
}

puppeteerMarch();
