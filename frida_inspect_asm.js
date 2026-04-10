var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;
var targetRVA = 0xD458C0;

console.log('\n--- ANALIZADOR DE ENSAMBLADOR v15.5 ---');
console.log('Base: ' + baseAddr);
console.log('Target: ' + baseAddr.add(targetRVA));
console.log(hexdump(baseAddr.add(targetRVA), {length: 64, header: true}));

// Intentamos desensamblar las primeras instrucciones
try {
    var cursor = baseAddr.add(targetRVA);
    for (var i = 0; i < 10; i++) {
        var ins = Instruction.parse(cursor);
        console.log(ins.address + ': ' + ins.toString());
        cursor = ins.next;
    }
} catch(e) {
    console.log('[!] Error desensamblando: ' + e);
}
