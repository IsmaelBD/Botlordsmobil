var baseAddr = Module.findBaseAddress('GameAssembly.dll');
console.log('[+] GameAssembly.dll Base: ' + baseAddr);

var fnAddByte = baseAddr.add(0x1D22860);
var fnAddUshort = baseAddr.add(0x1D224A0);
var fnAddUint = baseAddr.add(0x1D22430);
var fnAddUlong = baseAddr.add(0x1D22470);
var fnSend = baseAddr.add(0x1D23440);

var packetLog = [];

try {
    Interceptor.attach(fnSend, {
        onEnter: function(args) {
            var proto = args[0].add(0x30).readU16();
            if (proto === 2415 || proto === 6615) {
                console.log('\\n[🚀] ¡PAQUETE DE MARCHA ENVIADO! Protocol: ' + proto);
                console.log('ESTRUCTURA DEL PAYLOAD:');
                for (var i = 0; i < packetLog.length; i++) {
                    console.log('  -> ' + packetLog[i]);
                }
            }
            packetLog = []; 
        }
    });

    function hookAdd(addr, typeStr) {
        Interceptor.attach(addr, {
            onEnter: function(args) {
                var mp = args[0];
                var proto = mp.add(0x30).readU16();
                if (proto === 2415 || proto === 6615) {
                    var val = args[1].toInt32(); 
                    packetLog.push('Add(' + typeStr + ') = ' + val);
                }
            }
        });
    }

    hookAdd(fnAddByte, 'byte');
    hookAdd(fnAddUshort, 'ushort');
    hookAdd(fnAddUint, 'uint');
    //hookAdd(fnAddUlong, 'ulong'); // ulong toInt32 can fail

    console.log('[+] Hooks inyectados con éxito. Esperando que envíes la marcha...');
} catch(e) {
    console.log("Error: " + e.message);
}
