var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// El RVA maestro calculado desde el ensamblador v15.5
// 0x58FD368 es el puntero global hacia el DataManager
var masterPtr = baseAddr.add(0x58FD368);

console.log('\n--- ANALISIS SOBERANO v23.1 ---');
console.log('Puntero Maestro: ' + masterPtr);

try {
    var typeInfo = masterPtr.readPointer();
    console.log('TypeInfo: ' + typeInfo);
    
    if (!typeInfo.isNull()) {
        // En IL2CPP 64-bit, static_fields suele estar en +0xB8
        var staticFields = typeInfo.add(0xB8).readPointer();
        console.log('Static Fields: ' + staticFields);
        
        if (!staticFields.isNull()) {
            var instance = staticFields.readPointer();
            console.log('[✅] INSTANCIA FINAL HALLADA: ' + instance);
            
            // Verificación del "ADN" del castillo (MaxMarchEvent en 0x1074)
            var max = instance.add(0x1074).readU8();
            console.log('Capacidad de Marchas: ' + max);
            
            // Verificación de Lista de Tropas (0x1078)
            var marchArray = instance.add(0x1078).readPointer();
            if (!marchArray.isNull()) {
                console.log('Lista de Marchas (Array): ' + marchArray);
                console.log('Longitud del Array: ' + marchArray.add(0x18).readU32());
            }
        }
    }
} catch(e) {
    console.log('[!] Error en acceso soberano: ' + e.message);
}
