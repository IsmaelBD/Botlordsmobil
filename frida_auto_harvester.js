var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVAs Estables
var fnGetInstance = new NativeFunction(baseAddr.add(0xD458C0), 'pointer', []);
var fnNetSend     = new NativeFunction(baseAddr.add(0x1D28C40), 'void', ['pointer']);
var fnGetMP       = new NativeFunction(baseAddr.add(0x1D22900), 'pointer', []);
var fnAddSeq      = new NativeFunction(baseAddr.add(0x1D22110), 'void', ['pointer']);
var fnAddUS       = new NativeFunction(baseAddr.add(0x1D224A0), 'void', ['pointer', 'uint16']);

// Plantilla Maestra
var rawHex = "0e007804e8010000010009000000000000002c010000000000000000000000000000640000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000fb013b0000000000000000000000000000000000000000000000000000";
var templateBin = Memory.alloc(111);
for (var i = 0; i < 111; i++) templateBin.add(i).writeU8(parseInt(rawHex.substr(i*2, 2), 16));

var lastCheckTime = 0;

function checkAndDispatch() {
    var now = Date.now();
    if (now - lastCheckTime < 20000) return; // Solo revisamos cada 20 segs para no saturar
    lastCheckTime = now;

    var dm = fnGetInstance();
    if (dm.isNull()) return;

    var max = dm.add(0x1074).readU8();
    var marchPtr = dm.add(0x1078).readPointer();
    if (marchPtr.isNull()) return;

    var freeCount = 0;
    for (var i = 0; i < max; i++) {
        var type = marchPtr.add(0x20 + (i * 0x50)).readU8();
        if (type === 0) freeCount++;
    }

    if (freeCount > 0) {
        console.log('[💡] El Cerebro Maestro detectó ' + freeCount + ' hueco(s). Despachando...');
        
        var mp = fnGetMP();
        if (mp.isNull()) return;

        fnAddSeq(mp);
        fnAddUS(mp, 1);
        
        var buffObj = mp.add(0x28).readPointer();
        var dataObj = buffObj.add(0x20).readPointer();
        var currentPos = mp.add(0x18).readU32();
        var rawStart = dataObj.add(0x20).add(currentPos);

        Memory.copy(rawStart, templateBin.add(10), 101);
        rawStart.add(72).writeU16(507); // Bosque fijo por ahora
        rawStart.add(74).writeU8(59);

        mp.add(0x18).writeU32(currentPos + 101);
        mp.add(0x30).writeU16(6615);

        fnNetSend(mp);
    }
}

// Hookeamos el corazón del juego (DataManager.Update)
// RVA: 0xD47E90
Interceptor.attach(baseAddr.add(0xD47E90), {
    onEnter: function(args) { checkAndDispatch(); }
});

console.log('[🧠] CEREBRO MAESTRO v15.2 SINCRONIZADO CON EL JUEGO.');
