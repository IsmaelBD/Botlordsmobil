var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

// Definición de funciones nativas para inyección estable
var fnGetMP = new NativeFunction(baseAddr.add(0x1D22900), 'pointer', []);
var fnAddUS = new NativeFunction(baseAddr.add(0x1D224A0), 'void', ['pointer', 'uint16']);
var fnAddUI = new NativeFunction(baseAddr.add(0x1D22430), 'void', ['pointer', 'uint32']);
var fnAddBY = new NativeFunction(baseAddr.add(0x1D22860), 'void', ['pointer', 'uint8']);
var fnSend  = new NativeFunction(baseAddr.add(0x1D23440), 'int', ['pointer', 'int']);

function injectMarchV13() {
    console.log('[🚀] Iniciando Inyector v13.1 (Thread-Safe)...');
    
    // 1. Obtener instancia de MessagePacket
    var mp = fnGetMP();
    if (mp.isNull()) {
        console.log('[-] Error: No se pudo obtener el MessagePacket.');
        return;
    }
    
    // 2. Set Protocol 6615
    mp.add(0x30).writeU16(6615);
    
    // --- Secuencia de 33 pasos capturada por el escáner ---
    
    // 1: Prefijo de Protocolo
    fnAddUS(mp, 1);
    
    // 2-6: Héroes (5 slots)
    // Usamos el héroe 9 (manual) y el resto 0
    fnAddUS(mp, 9); 
    fnAddUS(mp, 0); 
    fnAddUS(mp, 0); 
    fnAddUS(mp, 0); 
    fnAddUS(mp, 0);
    
    // 7-22: Tropas (16 tipos)
    // T1 Espadachines = 1
    fnAddUI(mp, 1);
    for (var i = 0; i < 15; i++) fnAddUI(mp, 0);
    
    // 23-24: PointCode CALIBRADO (Reino 1977)
    // Forest (375, 499) -> Zone 24608, Point 53
    fnAddUS(mp, 24608); // ZoneID
    fnAddBY(mp, 53);    // PointID
    
    // 25-29: Mascotas (5 slots)
    for (var i = 0; i < 5; i++) fnAddUS(mp, 0);
    
    // 30-33: Tropas T5 (4 tipos)
    for (var i = 0; i < 4; i++) fnAddUI(mp, 0);
    
    // --- ENVÍO ---
    var success = fnSend(mp, 0);
    
    if (success) {
        console.log('[✅] v13.1: Marcha enviada con éxito sin crash.');
    } else {
        console.log('[-] El servidor rechazó el paquete (posiblemente por tropas/héroes ocupados).');
    }
}

// Ejecutamos la inyección
injectMarchV13();
