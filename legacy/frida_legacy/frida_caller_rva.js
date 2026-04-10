var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// RVA: 0x1D224A0 - MessagePacket.Add(ushort data)
var fnAddUS = baseAddr.add(0x1D224A0);

Interceptor.attach(fnAddUS, {
    onEnter: function(args) {
        var proto = args[0].add(0x30).readU16();
        if (proto === 6615) {
            var retAddr = this.returnAddress;
            var rva = retAddr.sub(baseAddr);
            console.log('\n[📍] Add(ushort) llamado desde RVA: 0x' + rva.toString(16).toUpperCase());
            // No nos detenemos, queremos ver quién llama varias veces
        }
    }
});

console.log('[+] ESCUCHANDO... Envía la marcha manual (Bosque Lv.3 con tus 2 héroes).');
