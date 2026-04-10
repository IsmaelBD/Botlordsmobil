var m = Process.getModuleByName('GameAssembly.dll');

console.log('\n--- CAZADOR DE ADN v29.0 ---');

function scanForKlass() {
    // Buscamos la huella del DataManager en los metadatos globales
    // Intentamos encontrar punteros que parezcan objetos de Unity
    var ranges = Process.enumerateRanges('rw-');
    var found = false;

    ranges.forEach(function(range) {
        if (found) return;
        try {
            // Buscamos el patrón típico de un DataManager (MaxMarch 7 en offset 0x1074)
            var results = Memory.scanSync(range.base, range.size, "07 00 00 00"); 
            for (var i = 0; i < results.length; i++) {
                var addr = results[i].address;
                var potentialDM = addr.sub(0x1074);
                
                // Verificación: ¿El primer byte es un puntero (Klass)?
                try {
                    var klass = potentialDM.readPointer();
                    if (!klass.isNull() && klass.readPointer().and(0xFFF) === 0) { // Alineación de Klass
                        console.log('[🧬] ¡ADN ENCONTRADO!');
                        console.log('    Instancia Detectada: ' + potentialDM);
                        console.log('    Klass Pointer: ' + klass);
                        found = true;
                        break;
                    }
                } catch(e) {}
            }
        } catch(e) {}
    });

    if (!found) console.log('[!] El Cazador sigue rastreando... mueve algo en el mapa.');
}

scanForKlass();
