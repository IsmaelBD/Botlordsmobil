var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVA: 0x221DDF0 - PointCode.WriteMP(MessagePacket MP)
var fnPCWrite = baseAddr.add(0x221DDF0);

Interceptor.attach(fnPCWrite, {
    onEnter: function(args) {
        var mp = args[0];
        var proto = mp.add(0x30).readU16();
        console.log('\\n[📍] PointCode.WriteMP llamado!');
        console.log('    Protocolo del paquete: ' + proto);
        
        // Ver los bytes que escribe
        var zone = this.context.rcx.readU16();
        var point = this.context.rcx.add(2).readU8();
        console.log('    Escribiendo -> Zone: ' + zone + ', Point: ' + point);
    }
});

console.log('[+] ESCUCHANDO POINTCODE... Envía la marcha manual.');
