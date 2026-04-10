var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVA: 0x1D23440 - NetworkManager.Send(MessagePacket mp)
var fnSend = baseAddr.add(0x1D23440);

Interceptor.attach(fnSend, {
    onEnter: function(args) {
        var proto = args[0].add(0x30).readU16();
        if (proto === 6615) {
            console.log('\n[!] SEND(6615) DETECTADO. Call Stack:');
            console.log(Thread.backtrace(this.context, Backtracer.ACCURATE)
                .map(DebugSymbol.fromAddress).join('\n'));
        }
    }
});

console.log('[+] ESCUCHANDO CALLSTACK. Por favor, envía una última marcha manual (con tus 2 héroes).');
