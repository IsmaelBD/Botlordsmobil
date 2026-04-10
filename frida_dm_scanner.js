var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// En IL2CPP, la instancia estática suele estar en un bloque de StaticFields
// Vamos a usar una técnica de escaneo para encontrar el puntero de DataManager
// Reconocemos un DataManager por:
// 1. Un puntero a su VTable al inicio.
// 2. MaxMarchEvent (6 o 5) en offset 0x1074.

function findDataManager() {
    console.log('[📡] Buscando DataManager mediante escaneo de patrones...');
    
    // Escaneamos un rango amplio de la memoria del heap
    var ranges = Process.enumerateRanges('rw-');
    for (var i = 0; i < ranges.length; i++) {
        var range = ranges[i];
        try {
            var results = Memory.scanSync(range.base, range.size, "05 00 00 00"); // Buscamos un posible MaxMarch 5
            for (var j = 0; j < results.length; j++) {
                var addr = results[j].address.sub(0x1074);
                try {
                    // Verificamos si parece un objeto (puntero a GameAssembly en 0x0)
                    var klassMatch = addr.readPointer();
                    if (klassMatch.compare(baseAddr) > 0 && klassMatch.compare(baseAddr.add(0x5000000)) < 0) {
                        console.log('[✅] ¡DataManager potencial hallado en: ' + addr);
                        return addr;
                    }
                } catch(e) {}
            }
        } catch(e) {}
    }
    return null;
}

var dm = findDataManager();
if (dm) {
    console.log('[🚀] Calibrando autonomía con dirección: ' + dm);
} else {
    console.log('[!] No se halló el DataManager en el escáner rápido.');
}
