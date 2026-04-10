var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

Interceptor.attach(baseAddr.add(0xD458C0), {
    onLeave: function(retval) {
        if (retval.isNull()) return;
        
        console.log('\n[🔍] DataManager Instance detected at: ' + retval);
        
        try {
            // Verificamos si podemos leer el offset 0x1074 (MaxMarch)
            var maxMarch = retval.add(0x1074).readU8();
            console.log('  MaxMarch (0x1074): ' + maxMarch);
            
            // Verificamos si podemos leer el puntero del Array (0x1078)
            var marchArray = retval.add(0x1078).readPointer();
            console.log('  MarchArray Pointer (0x1078): ' + marchArray);
            
            if (!marchArray.isNull()) {
                console.log('  Array Length: ' + marchArray.add(0x18).readU32());
            }
        } catch (e) {
            console.log('  [!] Error al leer offsets del DataManager: ' + e.message);
            // Si falla, vamos a inspeccionar los primeros 100 bytes del objeto
            console.log('  [!] Inspeccionando cabecera del objeto:');
            console.log(hexdump(retval, {length: 64}));
        }
    }
});

console.log('[📡] INSPECTOR DE MEMORIA v15.4 ACTIVO. Realiza cualquier acción en el juego.');
