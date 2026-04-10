var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;
var dm = ptr('0x207E0F34F00');

console.log('\n--- RASTREO GEOGRÁFICO v22.0 ---');
console.log('Instancia: ' + dm);

try {
    // Escaneamos la memoria del DataManager buscando 507, 59 (fb 01 3b 00)
    // Buscamos en un rango de 8KB desde la base del objeto
    var results = Memory.scanSync(dm, 0x2000, "fb 01 3b 00");
    
    for (var i = 0; i < results.length; i++) {
        var addr = results[i].address;
        console.log('[✅] Coordenada (507, 59) hallada en: ' + addr);
        console.log('    Offset desde DM: 0x' + addr.sub(dm).toString(16));
        
        // Vamos a ver qué hay alrededor de ese hallazgo
        console.log('    Contexto del Hallazgo (16 bytes):');
        console.log(hexdump(addr.sub(16), {length: 32, header: false}));
    }
    
    if (results.length === 0) {
        console.log('[!] Coordenadas no halladas en el bloque esperado. Ampliando búsqueda...');
        // Si no está cerca del DM, tal vez el array de marchas está en otro lugar del heap
        var ranges = Process.enumerateRanges('rw-');
        for (var k = 0; k < ranges.length; k++) {
            var range = ranges[k];
            try {
                var globalResults = Memory.scanSync(range.base, range.size, "fb 01 3b 00");
                for (var j = 0; j < globalResults.length; j++) {
                    console.log('[🌍] Coordenada hallada en el HEAP global: ' + globalResults[j].address);
                }
            } catch(ex) {}
        }
    }
} catch(e) {
    console.log('[!] Error en rastreo: ' + e.message);
}
