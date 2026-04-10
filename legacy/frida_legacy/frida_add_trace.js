var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVA: 0x1D22860 - MessagePacket.Add(byte data) 
// Usamos este como disparador para el rastro
var fnAddByte = baseAddr.add(0x1D22860);

Interceptor.attach(fnAddByte, {
    onEnter: function(args) {
        var proto = args[0].add(0x30).readU16();
        if (proto === 6615) {
            console.log('\n[🔥] ADD(byte) DETECTADO en Protocolo 6615!');
            console.log('Call Stack:');
            console.log(Thread.backtrace(this.context, Backtracer.ACCURATE)
                .map(DebugSymbol.fromAddress).join('\n'));
            // Removemos el hook para no saturar
            this.detach(); 
        }
    }
});

console.log('[+] ESCUCHANDO ADD(6615)... Envía la marcha manual.');
