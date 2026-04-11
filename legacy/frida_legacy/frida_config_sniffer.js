var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVA: 0x1D224A0 - MessagePacket.Add(ushort)
// RVA: 0x1D22430 - MessagePacket.Add(uint)
var fnAddUS = baseAddr.add(0x1D224A0);
var fnAddUI = baseAddr.add(0x1D22430);

var capturing = false;
var heroes = [];
var troops = [];

Interceptor.attach(fnAddUS, {
    onEnter: function(args) {
        var proto = args[0].add(0x30).readU16();
        if (proto === 6615) {
            capturing = true;
            var val = args[1].toInt32();
            if (heroes.length < 5 && heroes.length >= 0) {
                // El primer ushort es el prefijo(1), los siguientes 5 son héroes
                if (heroes.length > 0) heroes.push(val);
                else heroes.push("SKIP_PREFIX"); // Saltamos el ushort(1)
            }
        }
    }
});

Interceptor.attach(fnAddUI, {
    onEnter: function(args) {
        if (capturing) {
            var val = args[1].toInt32();
            if (troops.length < 16) {
                troops.push(val);
            }
        }
    }
});

// Hook final para imprimir resultados despuès de enviar
var fnSend = baseAddr.add(0x1D23440);
Interceptor.attach(fnSend, {
    onEnter: function(args) {
        if (capturing) {
            console.log('\n[✨] CONFIGURACIÓN CAPTURADA:');
            console.log('Héroes: ' + JSON.stringify(heroes.slice(1)));
            console.log('Tropas: ' + JSON.stringify(troops));
            capturing = false;
            heroes = [];
            troops = [];
        }
    }
});

console.log('[📡] ESCUCHANDO CONFIGURACIÓN... Envía una marcha manual ahora.');
