var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;
var dm = ptr('0x207E0F34F00');

console.log('\n--- DIAGNOSTICO DE MEMORIA v17.1 ---');
try {
    var max = dm.add(0x1074).readU8();
    var marchArray = dm.add(0x1078).readPointer();
    
    console.log('Max Marches: ' + max);
    console.log('March Array Address: ' + marchArray);
    
    if (!marchArray.isNull()) {
        for (var i = 0; i < max; i++) {
            var slotAddr = marchArray.add(0x20 + (i * 0x50));
            console.log('\nSlot [' + i + '] (' + slotAddr + '):');
            console.log(hexdump(slotAddr, {length: 32}));
        }
    }

    var troopArray = dm.add(0xF40).readPointer();
    console.log('\n--- LISTA DE TROPAS EN CASA (0xF40) ---');
    if (!troopArray.isNull()) {
        console.log('Troop Array Address: ' + troopArray);
        console.log(hexdump(troopArray.add(0x20), {length: 64}));
    }
} catch(e) {
    console.log('[!] Error: ' + e.message);
}
