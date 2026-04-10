var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVAs Quirúrgicos (Detectados en v13.13)
var rvaZone = baseAddr.add(0x1323D5B);
var rvaPoint = baseAddr.add(0x1323D6D);

var targetZone = 507;
var targetPoint = 59;

function surgicalHijack() {
    console.log('[🚀] Lanzando Inyector v13.14 (Surgical Hijacker)...');

    // Hijack de Zona
    Interceptor.attach(rvaZone, {
        onEnter: function(args) {
            console.log('[📍] SECUESTRO DE ZONA: Redirigiendo a 507...');
            args[1] = ptr(targetZone);
        }
    });

    // Hijack de Punto
    Interceptor.attach(rvaPoint, {
        onEnter: function(args) {
            console.log('[📍] SECUESTRO DE PUNTO: Redirigiendo a 59...');
            args[1] = ptr(targetPoint);
        }
    });

    console.log('[📡] SECUESTRADOR ACTIVO. Por favor, envía una marcha manual ahora.');
    console.log('[!] El destino será automáticamente cambiado al Bosque Lv.3.');
}

surgicalHijack();
