var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

var fnGetMP     = new NativeFunction(baseAddr.add(0x1D22900), 'pointer', []);
var fnAddSeq    = new NativeFunction(baseAddr.add(0x1D22110), 'void', ['pointer']);
var fnNetSend   = new NativeFunction(baseAddr.add(0x1D28C40), 'void', ['pointer']); 
var fnAddUS     = new NativeFunction(baseAddr.add(0x1D224A0), 'void', ['pointer', 'uint16']);

function injectSyncedMarch(zone, point) {
    console.log('[🚀] Iniciando Inyector v13.9.1 (Sincronización Viva)...');
    
    // 1. Obtenemos un paquete NUEVO (Vacío y limpio)
    var mp = fnGetMP();
    if (mp.isNull()) return;

    // 2. Cargamos tu configuración de tropas/héroes (ADN sin cabecera)
    // Saltamos los primeros 10 bytes de la plantilla original (Header + Prefijos)
    var templateHex = "09000000000000002c010000000000000000000000000000640000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000fb013b0000000000000000000000000000000000000000000000000000";
    var contentSize = 101; 
    var contentBin = Memory.alloc(contentSize);
    for (var i = 0; i < contentSize; i++) {
        contentBin.add(i).writeU8(parseInt(templateHex.substr(i*2, 2), 16));
    }

    // 3. Modificamos Coordenadas en el contenido
    // Como saltamos 10 bytes, el offset 82 ahora es 72
    contentBin.add(72).writeU16(zone);
    contentBin.add(74).writeU8(point);

    // 4. PASO VITAL: Sincronizar el ID de Secuencia con el Servidor
    // Esto pone los bytes 0-7 correctos para ESTA sesión
    fnAddSeq(mp);
    fnAddUS(mp, 1); // Prefijo ushort(1) que exige el protocolo 6615

    // 5. Pegamos el contenido después de la secuencia
    var buffObj = mp.add(0x28).readPointer();
    var dataObj = buffObj.add(0x20).readPointer();
    var currentPos = mp.add(0x18).readU32(); // Generalmente pos 4 o 6 después de AddSeq + AddUS
    var rawStart = dataObj.add(0x20).add(currentPos);

    Memory.copy(rawStart, contentBin, contentSize);
    
    // Ajustamos la longitud final (actual + contenido)
    mp.add(0x18).writeU32(currentPos + contentSize);
    mp.add(0x30).writeU16(6615); // Protocolo

    // 6. Envío Maestro
    fnNetSend(mp);
    
    console.log('[✅] v13.9.1: Inyectado con Sequence ID fresco. Sincronización exitosa.');
}

// Ejecución al Bosque (Zona 507, Punto 59)
injectSyncedMarch(507, 59);
