var m = Process.getModuleByName('GameAssembly.dll');

Interceptor.attach(m.base.add(0xD458C0), {
    onLeave: function(retval) {
        if (!retval.isNull()) {
            console.log('\n[🏰] DIRECCIÓN REAL DETECTADA: ' + retval);
            
            // Verificamos si podemos leer el número de marchas (offset 0x1074)
            try {
                var max = retval.add(0x1074).readU8();
                console.log('[🎖️] Capacidad de Marchas Verificada: ' + max);
                
                // Si la capacidad es 7, esta es definitivamente la instancia correcta.
                if (max === 7) {
                    console.log('[✅] ¡ÉXITO! Esta es la instancia Maestra.');
                }
            } catch(e) {}
        }
    }
});

console.log('[📡] CAPTURADOR v27.0 ACTIVO. Toca cualquier menú del juego...');
