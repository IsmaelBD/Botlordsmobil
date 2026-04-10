var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

console.log('\n--- RASTREADOR GEOGRÁFICO v24.0 ---');

function inspectMatch(addr) {
    try {
        console.log('\n[🛰️] Analizando hallazgo en: ' + addr);
        // El struct MarchEventDataType tiene Point en +0x18. 
        // Intentamos ver si hay un EMarchEventType razonable en -0x18.
        var base = addr.sub(0x18);
        var type = base.readU8();
        
        if (type > 0 && type < 30) {
            console.log('    [🔥] ¡POSIBLE MARCHA DETECTADA!');
            console.log('    Tipo: ' + type);
            console.log(hexdump(base, {length: 64}));
            
            // Buscamos quién apunta a esta dirección en la memoria global
            // (Para encontrar el Array o el Manager)
            var ranges = Process.enumerateRanges('rw-');
            ranges.forEach(function(r) {
                try {
                    var pointerResults = Memory.scanSync(r.base, r.size, base.toString(16).match(/.{1,2}/g).reverse().join(' ')); 
                    for (var k=0; k<pointerResults.length; k++) {
                       console.log('    [🔗] Puntero a esta marcha hallado en: ' + pointerResults[k].address);
                    }
                } catch(e) {}
            });
        }
    } catch(e) {}
}

var ranges = Process.enumerateRanges('rw-');
ranges.forEach(function(range) {
    try {
        // Buscamos 507, 59 (fb 01 3b 00)
        var results = Memory.scanSync(range.base, range.size, "fb 01 3b 00");
        for (var i = 0; i < results.length; i++) {
            inspectMatch(results[i].address);
        }
    } catch(e) {}
});

console.log('[✅] Búsqueda finalizada.');
