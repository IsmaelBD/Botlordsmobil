var dm = ptr('0x207E0F34F00');

console.log('\n--- INSPECCIÓN DE OFFSETS v17.2 ---');
console.log('Instancia: ' + dm);

try {
    // Escaneamos el bloque donde deberían estar los eventos
    console.log('Inspeccionando bloque 0x1000 - 0x1100:');
    console.log(hexdump(dm.add(0x1000), {length: 256, header: true}));
    
    // También revisamos un poco antes por si acaso
    console.log('\nInspeccionando bloque 0xF00 - 0xF80:');
    console.log(hexdump(dm.add(0xF00), {length: 128, header: true}));
} catch(e) {
    console.log('[!] Error: ' + e.message);
}
