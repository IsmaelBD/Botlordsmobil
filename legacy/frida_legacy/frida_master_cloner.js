var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

var fnSend = baseAddr.add(0x1D23440);
var masterBuffer = null;

Interceptor.attach(fnSend, {
    onEnter: function(args) {
        var mp = args[0];
        var proto = mp.add(0x30).readU16();
        
        if (proto === 6615) {
            // Buscamos el buffer en el MessagePacket
            // MessagePacket -> MessageBuff (0x28)
            var buffPtr = mp.add(0x28).readPointer();
            if (buffPtr.isNull()) return;

            // MessageBuff -> Data (0x10), Position (0x18)
            var dataPtr = buffPtr.add(0x10).readPointer();
            var len = buffPtr.add(0x18).readS32();
            
            if (len > 0) {
                console.log('\n[💾] ¡ESTRUCTURA MAESTRA CAPTURADA! (' + len + ' bytes)');
                masterBuffer = dataPtr.add(0x20).readByteArray(len); // +0x20 para saltar cabecera de array C#
                
                // Imprimimos el HEX para guardarlo por si acaso
                console.log(hexdump(masterBuffer));
                
                // Exportamos a un archivo local en d:\ para persistencia
                var file = new File("d:\\BotLordsMobile\\master_march.bin", "wb");
                file.write(masterBuffer);
                file.close();
                
                console.log('[✅] Archivo "master_march.bin" generado. Sincronización completa.');
            }
        }
    }
});

console.log('[📡] CLONADOR v13.4.1 ACTIVO. Por favor, envía la marcha manual.');
