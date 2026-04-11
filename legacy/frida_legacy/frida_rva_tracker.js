var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

var fnSend = baseAddr.add(0x1D23440);

Interceptor.attach(fnSend, {
    onEnter: function(args) {
        var proto = args[0].add(0x30).readU16();
        if (proto === 6615) {
            console.log('\\n[!] SEND(6615) DETECTADO. Call Stack (RVA):');
            var backtrace = Thread.backtrace(this.context, Backtracer.ACCURATE);
            for (var i = 0; i < backtrace.length; i++) {
                var addr = backtrace[i];
                var mod = Process.getModuleByAddress(addr);
                if (mod && mod.name === 'GameAssembly.dll') {
                    console.log('    GameAssembly.dll + 0x' + addr.sub(mod.base).toString(16).toUpperCase());
                } else {
                    console.log('    ' + addr + ' (Unknown Module)');
                }
            }
        }
    }
});

console.log('[+] ESCUCHANDO RVA. Envía la marcha manual.');
