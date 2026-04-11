var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;
var fnGetInstance = new NativeFunction(baseAddr.add(0xD458C0), 'pointer', []);

function debugDataManager() {
    var dm = fnGetInstance();
    if (dm.isNull()) {
        console.log('[!] DataManager no encontrado.');
        return;
    }

    var max = dm.add(0x1074).readU8();
    var marchPtr = dm.add(0x1078).readPointer();
    
    console.log('\n--- DIAGNÓSTICO DE CEREBRO v15.3 ---');
    console.log('Max Marches (0x1074): ' + max);
    console.log('March Data Pointer (0x1078): ' + marchPtr);

    if (!marchPtr.isNull()) {
        console.log('Array Length (0x18): ' + marchPtr.add(0x18).readU32());
        for (var i = 0; i < 5; i++) {
            var type = marchPtr.add(0x20 + (i * 0x50)).readU8();
            console.log('  Marcha [' + i + '] Tipo: ' + type);
        }
    }
}

// Ejecutar diagnóstico cada 5 segundos
setInterval(debugDataManager, 5000);
