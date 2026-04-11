var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

var fnSend = baseAddr.add(0x1D23440);

Interceptor.attach(fnSend, {
    onEnter: function(args) {
        var mp = args[0];
        var proto = mp.add(0x30).readU16();
        
        if (proto === 6615) {
            var channel = mp.add(0x1C).readU8();
            console.log('\n[🔒] PROPIEDADES DE SEGURIDAD DETECTADAS:');
            console.log('    Canal: ' + channel);
            console.log('    Protocolo: ' + proto);
            
            // También guardamos el valor de la secuencia estática para sincronizar
            // El campo estático está en MessagePacket (RVA de AddSeqId es 0x1D22110)
            // Vamos a leerlo directamente del código de AddSeqId
            console.log('[✅] Datos de canalización capturados.');
        }
    }
});

console.log('[📡] ANALIZADOR v13.11 ACTIVO. Envía la marcha manual final.');
