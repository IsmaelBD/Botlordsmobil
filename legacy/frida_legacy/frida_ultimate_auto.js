var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// DIRECCIÓN MAESTRA RECALIBRADA (v31.0 Logic)
var fnNetSend = new NativeFunction(baseAddr.add(0x1D28C40), 'void', ['pointer']);
var fnGetMP   = new NativeFunction(baseAddr.add(0x1D22900), 'pointer', []);
var fnAddSeq  = new NativeFunction(baseAddr.add(0x1D22110), 'void', ['pointer']);
var fnAddUS   = new NativeFunction(baseAddr.add(0x1D224A0), 'void', ['pointer', 'uint16']);

// GATILLO NATIVO v35.0
var fnNativeSend = new NativeFunction(baseAddr.add(0x1323500), 'void', ['pointer']);

var templateHex = "010009000000000000002c010000000000000000000000000000640000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000fb013b0000000000000000000000000000000000000000000000000000";
var templateBin = Memory.alloc(101);
for (var i = 0; i < 101; i++) templateBin.add(i).writeU8(parseInt(templateHex.substr(i*2, 2), 16));

var dmGlobal = null;

function autoLaunch() {
    if (!dmGlobal || dmGlobal.isNull()) return;

    try {
        var max = dmGlobal.add(0x1074).readU8(); 
        var marchArray = dmGlobal.add(0x1078).readPointer();
        if (!marchArray || marchArray.isNull()) return;

        var freeFound = false;
        for (var i = 0; i < max; i++) {
            var type = marchArray.add(0x20 + (i * 0x50)).readU8();
            if (type === 0) {
                freeFound = true;
                break;
            }
        }

        if (freeFound) {
            console.log('[🤖] BOT: Detectado hueco en ejército. Lanzando ataque autónomo...');
            var mp = fnGetMP();
            if (!mp.isNull()) {
                fnAddSeq(mp);
                fnAddUS(mp, 1);
                var raw = mp.add(0x28).readPointer().add(0x20).readPointer().add(0x20).add(mp.add(0x18).readU32());
                Memory.copy(raw, templateBin, 101);
                raw.add(72).writeU16(507); // Wood Lv.3
                raw.add(74).writeU8(59);
                mp.add(0x18).writeU32(mp.add(0x18).readU32() + 101);
                mp.add(0x30).writeU16(6615);
                fnNetSend(mp);
                console.log('[✅] BOT: Marcha despachada por si sola.');
            }
        }
    } catch(e) {}
}

// CAPTURA DIRECTA DE LATIDO
Interceptor.attach(baseAddr.add(0x1D2C9D0), { // NetworkManager.Update
    onEnter: function(args) {
        if (dmGlobal) return;
        var dm = args[0].add(0x10).readPointer();
        if (!dm.isNull() && dm.add(0x1074).readU8() === 7) {
            dmGlobal = dm;
            console.log('[🤴] COSECHADOR v35.0 SINCRONIZADO.');
            console.log('    Castillo de 7 Marchas Detectado.');
            setInterval(autoLaunch, 15000);
        }
    }
});

console.log('[📡] SISTEMA v35.0 ACTIVO. La autonomía total está lista.');
