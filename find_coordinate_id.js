var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;
console.log('[+] GameAssembly.dll Base: ' + baseAddr);

// RVA: 0x1E82480 - MapManager.MapIDToPointCode(int mapID)
var fnMapToPC = baseAddr.add(0x1E82480);

Interceptor.attach(fnMapToPC, {
    onEnter: function(args) {
        // En x64: args[0] es la instancia de MapManager, args[1] es mapID
        var mapID = args[1].toInt32();
        if (mapID > 0) {
            console.log('\\n[📍] CLICK DETECTADO!');
            console.log('    MapID Interno: ' + mapID);
        }
    },
    onLeave: function(retval) {
        // retval es el PointCode (3 bytes útiles en rax)
        // rax: [00 00 00 00 00 PointID ZoneIDHigh ZoneIDLow]
        var res = retval.toInt32();
        var zone = res & 0xFFFF;
        var point = (res >> 16) & 0xFF;
        if (zone > 0) {
            console.log('    ZoneID: ' + zone);
            console.log('    PointID: ' + point);
            send({type: 'coord', mapID: res, zone: zone, point: point});
        }
    }
});

console.log('[+] ESCUCHANDO... Haz click en el Bosque Lv.3 ahora.');
