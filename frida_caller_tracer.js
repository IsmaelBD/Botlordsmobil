var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// Hookeamos MessagePacket.Add(ushort) y Add(byte)
var fnAddUS = baseAddr.add(0x1D224A0);
var fnAddBY = baseAddr.add(0x1D22860);

function traceCaller(context, type, val) {
    var mp = context.r0 || context.rcx; 
    var proto = mp.add(0x30).readU16();
    
    if (proto === 6615) {
        var lr = Thread.backtrace(context, Backtracer.ACCURATE)[0];
        var rva = lr.sub(baseAddr);
        console.log('[🔍] ' + type + ' Detectado: ' + val + ' | Invocado desde RVA: ' + rva);
    }
}

Interceptor.attach(fnAddUS, {
    onEnter: function(args) { traceCaller(this.context, "USHORT", args[1].toInt32()); }
});

Interceptor.attach(fnAddBY, {
    onEnter: function(args) { traceCaller(this.context, "BYTE", args[1].toInt32()); }
});

console.log('[📡] RASTREADOR v13.13 ACTIVO. Envía la marcha manual.');
