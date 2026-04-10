var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

console.log('\n--- CAZADOR UNIVERSAL v22.2 ---');

function verifyStruct(addr) {
    // MarchEventDataType: Point en offset 0x18. Base = addr - 0x18
    var base = addr.sub(0x18);
    try {
        var type = base.readU8();
        // EMarchEventType: Recolectar suele ser 9 o valor cercano
        if (type > 0 && type < 30) {
            console.log('[🔥] ¡ESTRUCTURA REAL IDENTIFICADA!');
            console.log('    Dirección Base: ' + base);
            console.log('    Tipo Detectado: ' + type);
            
            // Verificamos si hay punteros de Troops en 0x10 y Heroes en 0x8
            var heroPtr = base.add(0x8).readPointer();
            if (!heroPtr.isNull()) {
                console.log('    [🧬] ADN de Héroes confirmado.');
                return base;
            }
        }
    } catch(e) {}
    return null;
}

var ranges = Process.enumerateRanges('rw-');
var found = false;

ranges.forEach(function(range) {
    if (found) return;
    try {
        var results = Memory.scanSync(range.base, range.size, "fb 01 3b 00");
        for (var i = 0; i < results.length; i++) {
            var match = verifyStruct(results[i].address);
            if (match) {
                console.log('[🏆] ÉXITO: Tu ejército ha sido localizado en: ' + match);
                found = true;
                break;
            }
        }
    } catch(e) {}
});

if (!found) console.log('[!] El Cazador no halló el objetivo. Intenta mover la cámara en el mapa.');
