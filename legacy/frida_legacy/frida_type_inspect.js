var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// Dirección calculada del puntero al TypeInfo del DataManager
var typeInfoPtrPtr = baseAddr.add(0xD458C5 + 0x04BAFA9D + 6);

console.log('\n--- ANALISIS DE TIPO v16.6 ---');
console.log('Lookup Address: ' + typeInfoPtrPtr);

try {
    var typeInfo = typeInfoPtrPtr.readPointer();
    console.log('TypeInfo Address: ' + typeInfo);
    
    if (!typeInfo.isNull()) {
        // En IL2CPP 64 bits, static_fields suele estar en offset 0xB8
        var staticFields = typeInfo.add(0xB8).readPointer();
        console.log('Static Fields Address: ' + staticFields);
        
        if (!staticFields.isNull()) {
            var instance = staticFields.readPointer();
            console.log('[✅] INSTANCIA REAL HALLADA: ' + instance);
            
            // Verificación final del campo MaxMarchEvent (0x1074)
            var max = instance.add(0x1074).readU8();
            console.log('  Verificación MaxMarch: ' + max);
        }
    }
} catch(e) {
    console.log('[!] Error en análisis estático: ' + e.message);
}
