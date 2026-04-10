var matches = [
    '0x207fa32e402', '0x207fa64e2d2', '0x208b08aa810'
];

console.log('\n--- VOLCADO DE HALLAZGOS v24.1 ---');

matches.forEach(function(hex) {
    var addr = ptr(hex);
    console.log('\n--- Hallazgo en ' + hex + ' ---');
    console.log(hexdump(addr.sub(64), {length: 128, header: true}));
});
