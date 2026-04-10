var targetPoint = "fb 01 3b 00"; // Coordenadas 507, 59 del bosque

console.log('\n--- CAPTURA DE PLANTILLA MAESTRA v33.0 ---');

var ranges = Process.enumerateRanges('rw-');
var found = false;

ranges.forEach(function(r) {
    if (found) return;
    try {
        var results = Memory.scanSync(r.base, r.size, targetPoint);
        for (var i = 0; i < results.length; i++) {
            var addr = results[i].address;
            // TargetPoint está en +0x18. La base del struct es -0x18.
            var base = addr.sub(0x18);
            
            // Verificamos si parece ser una estructura de marcha (Type > 0)
            var type = base.readU8();
            if (type > 0 && type < 30) {
                console.log('[🔥] ¡PLANTILLA IDENTIFICADA!');
                console.log('    Dirección: ' + base);
                console.log('    Contenido RAW (0x50 bytes):');
                var raw = base.readByteArray(0x50);
                console.log(hexdump(raw, {header: false}));
                
                // Guardamos el buffer para usarlo en el bot autónomo
                // Convertimos a hex para que el bot pueda leerlo
                var hex = "";
                var uint8 = new Uint8Array(raw);
                for(var j=0; j<uint8.length; j++) hex += uint8[j].toString(16).padStart(2, '0');
                console.log('[🔑] CLAVE_CLONACIÓN: ' + hex);
                
                found = true;
                break;
            }
        }
    } catch(e) {}
});

if (!found) console.log('[!] No se hallaron marchas activas en (507, 59). Asegúrate de que una tropa esté en el bosque.');
