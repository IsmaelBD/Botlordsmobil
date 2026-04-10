var candidates = [
    '0x207fa32e402', '0x207fa64e2d2', '0x208b08aa810', '0x208c602e832', 
    '0x208d5b0e162', '0x208eb88e8ba', '0x208f4f8e5ea'
];

console.log('\n--- VERIFICACIÓN BIOMÉTRICA v22.1 ---');

candidates.forEach(function(hex) {
    var addr = ptr(hex);
    // El struct MarchEventDataType tiene Point en offset 0x18
    // Base = addr - 0x18
    var base = addr.sub(0x18);
    
    try {
        var type = base.readU8();
        // EMarchEventType suele ser entre 1 y 20
        if (type > 0 && type < 30) {
            console.log('[🔥] ¡CANDIDATO SÓLIDO HALLADO!');
            console.log('    Base: ' + base);
            console.log('    Tipo de Marcha: ' + type);
            console.log('    Hexdump del Objeto:');
            console.log(hexdump(base, {length: 64}));
        }
    } catch(e) {}
});
