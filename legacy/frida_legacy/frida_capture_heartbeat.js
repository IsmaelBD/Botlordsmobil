var m = Process.getModuleByName('GameAssembly.dll');

// RVA de DataManager.Update (El latido del juego)
Interceptor.attach(m.base.add(0xD47E90), {
    onEnter: function(args) {
        var dm = args[0]; // El primer argumento es SIEMPRE la instancia (rcx)
        if (!dm.isNull()) {
            console.log('\n[💓] LATIDO DETECTADO. Dirección: ' + dm);
            
            try {
                var max = dm.add(0x1074).readU8();
                console.log('[🎖️] Capacidad de Marchas: ' + max);
                
                if (max === 7) {
                    console.log('[✅] ¡ÉXITO! Cimientos localizados.');
                    // Detener el hook para no saturar
                    // Interceptor.detachAll(); // Opcional
                }
            } catch(e) {}
        }
    }
});

console.log('[📡] CAPTURADOR DE LATIDO v28.0 ACTIVO. Sincronizando...');
