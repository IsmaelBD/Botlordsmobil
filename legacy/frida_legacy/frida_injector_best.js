var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// Funciones nativas
var fnGetMP  = new NativeFunction(baseAddr.add(0x1D22900), 'pointer', []);
var fnAddSeq = new NativeFunction(baseAddr.add(0x1D22110), 'void', ['pointer']);
var fnSend   = new NativeFunction(baseAddr.add(0x1D23440), 'int', ['pointer', 'int']);

function injectClonedMarch(zone, point) {
    console.log('[🚀] Iniciando Inyector Maestro v13.7 (Full Clone)...');
    
    // 1. Cargamos el clon binario (leído desde el archivo en la parte de python o definido aquí)
    // Para asegurar éxito, definimos los 111 bytes capturados aquí directamente
    var rawHex = "0e007804e8010000010009000000000000002c010000000000000000000000000000640000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000fb013b0000000000000000000000000000000000000000000000000000";
    var bin = Memory.alloc(111);
    for (var i = 0; i < 111; i++) {
        bin.add(i).writeU8(parseInt(rawHex.substr(i*2, 2), 16));
    }

    // 2. Modificamos coordenadas en el clon (offset 82 y 84)
    bin.add(82).writeU16(zone);
    bin.add(84).writeU8(point);

    // 3. Obtenemos un MessagePacket real del juego
    var mp = fnGetMP();
    if (mp.isNull()) {
        console.log('[-] Error: DataManager no listo.');
        return;
    }

    // 4. Inyectamos nuestro clon en el buffer del objeto
    // mp + 0x28 (Buffer) + 0x20 (byte[] Data) + 0x20 (Raw Start)
    var buffObj = mp.add(0x28).readPointer();
    var dataObj = buffObj.add(0x20).readPointer();
    var rawDataAddr = dataObj.add(0x20);

    Memory.copy(rawDataAddr, bin, 111);
    
    // Sincronizamos longitud y protocolo en el objeto de C#
    mp.add(0x18).writeU32(111); // len
    mp.add(0x30).writeU16(6615); // proto

    // 5. Sello de Seguridad (AddSeqId)
    fnAddSeq(mp);

    // 6. ¡FUEGO!
    var res = fnSend(mp, 0);
    
    if (res === 1) {
        console.log('[✅] v13.7: ¡MARCHA CLONADA ENVIADA CON ÉXITO!');
    } else {
        console.log('[-] Fallo en el envío.');
    }
}

// Ejecución
injectClonedMarch(507, 59);
