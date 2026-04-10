var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

var targetSend = baseAddr.add(0x1D23440);

Interceptor.attach(targetSend, {
    onEnter: function(args) {
        var mp = args[0];
        // Basado en dump.cs: Protocolo en 0x30, Longitud en 0x18
        var proto = mp.add(0x30).readU16();
        var len = mp.add(0x18).readS32();

        if (len > 0) {
            console.log('\n[📡] PAQUETE ENVIADO: ' + proto + ' (' + len + ' bytes)');
            
            // Acceso profundo al buffer de bytes
            // mp + 0x28 (Buffer<byte>) + 0x20 (byte[] Data) + 0x20 (Raw Data)
            var bufferObj = mp.add(0x28).readPointer();
            if (!bufferObj.isNull()) {
                var dataObj = bufferObj.add(0x20).readPointer();
                if (!dataObj.isNull()) {
                    var rawData = dataObj.add(0x20).readByteArray(len);
                    console.log(hexdump(rawData));

                    // Si es el paquete de marcha (6615 o longitud ~111)
                    if (proto === 6615 || (len >= 105 && len <= 115)) {
                        console.log('[💎] ¡MARCHA DETECTADA Y CLONADA!');
                        var file = new File("d:\\BotLordsMobile\\master_march.bin", "wb");
                        file.write(rawData);
                        file.close();
                        console.log('[✅] Plantilla guardada en d:\\BotLordsMobile\\master_march.bin');
                    }
                }
            }
        }
    }
});

console.log('[📡] RADAR v13.4.3 ACTIVO. Envía la marcha manual ahora.');
