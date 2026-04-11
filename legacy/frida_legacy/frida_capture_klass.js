var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

Interceptor.attach(baseAddr.add(0xD458C0), {
    onLeave: function(retval) {
        if (!retval.isNull()) {
            console.log('\n[🧬] ADN (Klass) Detectado: ' + retval.readPointer());
            console.log('[🏰] Instancia Actual: ' + retval);
            
            // Verificamos MaxMarch en tiempo real
            try {
                var max = retval.add(0x1074).readU8();
                console.log('[🎖️] Capacidad de Marchas: ' + max);
            } catch(e) {}
        }
    }
});

console.log('[📡] SENSOR DE ADN v20.0 ACTIVO. Realiza cualquier acción en el juego.');
