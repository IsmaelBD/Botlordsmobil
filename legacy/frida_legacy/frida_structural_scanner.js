var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;
console.log('[+] GameAssembly.dll Base: ' + baseAddr);

var off = {
   AddByte: 0x1D22860,
   AddUshort: 0x1D224A0,
   AddUint: 0x1D22430,
   Send: 0x1D23440
};

var packetLog = [];

function hookAdd(addr, typeStr) {
    Interceptor.attach(baseAddr.add(addr), {
        onEnter: function(args) {
            var mp = args[0];
            var proto = mp.add(0x30).readU16();
            if (proto === 6615) {
                var pos = mp.add(0x24).readU32(); // Position field
                var val = args[1].toInt32();
                console.log('    [+] Add(' + typeStr + ') val=' + val + ' at pos=' + pos);
            }
        }
    });
}

hookAdd(off.AddByte, 'byte');
hookAdd(off.AddUshort, 'ushort');
hookAdd(off.AddUint, 'uint');

Interceptor.attach(baseAddr.add(off.Send), {
    onEnter: function(args) {
        var mp = args[0];
        var proto = mp.add(0x30).readU16();
        if (proto === 6615) {
            var len = mp.add(0x18).readU16();
            var dataPtr = mp.add(0x28).readPointer();
            console.log('\\n[🚀] SEND(6615) - Len: ' + len);
            if (dataPtr && !dataPtr.isNull()) {
                var raw = dataPtr.add(0x20).readByteArray(len);
                console.log(hexdump(raw, { length: len, header: true }));
            }
        }
    }
});

console.log('[+] ESCÁNER ESTRUCTURAL ACTIVO. Envía la marcha manual.');
