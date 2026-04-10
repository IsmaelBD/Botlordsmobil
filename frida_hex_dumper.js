var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;
console.log('[+] GameAssembly.dll Base: ' + baseAddr);

// RVA: 0x1D23440 - NetworkManager.Send(MessagePacket mp)
var fnSend = baseAddr.add(0x1D23440);

Interceptor.attach(fnSend, {
    onEnter: function(args) {
        var mp = args[0];
        var proto = mp.add(0x30).readU16();
        
        // Solo nos interesan los protocolos de marcha
        if (proto === 2415 || proto === 6615) {
            var len = mp.add(0x18).readU16();
            var dataPtr = mp.add(0x28).readPointer();
            
            console.log('\\n[🚀] CAPTURA DE HEXADECIMAL (Proto: ' + proto + ', Len: ' + len + ')');
            
            if (dataPtr.isNull()) {
                console.log('    [!] Data buffer is NULL');
                return;
            }

            // El buffer en C# tiene un encabezado de 0x20 bytes (Array header)
            // Los datos reales empiezan en dataPtr + 0x20
            var rawData = dataPtr.add(0x20).readByteArray(len);
            console.log(hexdump(rawData, {
                offset: 0,
                length: len,
                header: true,
                ansi: true
            }));
        }
    }
});

console.log('[+] ESCUCHANDO HEX... Envía una marcha manual en el juego.');
