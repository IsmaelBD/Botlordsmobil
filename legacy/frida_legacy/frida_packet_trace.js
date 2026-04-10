var m = Process.getModuleByName('GameAssembly.dll');

console.log('\n--- RADAR DE RED v30.2 ---');

Interceptor.attach(m.base.add(0x1D28C40), { // NetworkManager.Send
    onEnter: function(args) {
        var msg = args[1]; // MessagePacket
        if (!msg.isNull()) {
            try {
                var protocol = msg.add(0x30).readU16();
                console.log('[📡] PAQUETE ENVIADO: ' + protocol);
                
                // Rango de protocolos de expedición
                if (protocol >= 6600 && protocol <= 6650) {
                     var dm = this.context.rcx;
                     console.log('\n[✅] ¡CASTILLO CAPTURADO!');
                     console.log('    Dirección: ' + dm);
                     
                     // Verificamos MaxMarch en tiempo real (0x1074)
                     var max = dm.add(0x1074).readU8();
                     console.log('    Capacidad verificada: ' + max);
                     
                     if (max === 7) console.log('[🏆] ÉXITO TOTAL: Sincronización completa.');
                }
            } catch(e) {}
        }
    }
});

console.log('[📡] RADAR v30.2 ACTIVO. Envía una marcha manual.');
