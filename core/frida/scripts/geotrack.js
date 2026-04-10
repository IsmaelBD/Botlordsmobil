/**
 * geotrack.js — Geographic Tracking
 * Scans game memory for coordinate patterns (zone/point encoding).
 * Finds active marches and target coordinates.
 *
 * Usage:
 *   frida -p <pid> -l geotrack.js
 */

var RVA = require('./_shared/rva_map');

var m = Process.getModuleByName(RVA.MODULE_NAME);
var baseAddr = m.base;

// Known coordinate signatures
var SIGNATURES = [
    { name: "Forest (507,59)", hex: "fb 01 3b 00", zone: 507, point: 59 },
    { name: "Test Zone",       hex: "00 02 00 00", zone: 512, point: 0  },
];

console.log('\n=== GEO TRACKING v22.0 ===\n');

/**
 * Scan memory range for a hex pattern.
 */
function scanForPattern(pattern, base, size) {
    try {
        var results = Memory.scanSync(base, size, pattern);
        return results;
    } catch (e) {
        return [];
    }
}

/**
 * Dump memory around a found address.
 */
function dumpContext(addr, contextBytes) {
    console.log('    Context (' + contextBytes * 2 + ' hex chars):');
    try {
        var dump = hexdump(addr.sub(contextBytes), { length: contextBytes * 2, header: false });
        console.log('    ' + dump.split('\n').join('\n    '));
    } catch (e) {
        console.log('    [dump failed: ' + e.message + ']');
    }
}

/**
 * Scan all rw- memory ranges for coordinate signatures.
 */
function globalScan() {
    var ranges = Process.enumerateRanges('rw-');
    var totalFound = 0;

    for (var sig of SIGNATURES) {
        var found = 0;
        console.log('[*] Scanning for: ' + sig.name + ' — pattern: ' + sig.hex);

        for (var r of ranges) {
            try {
                var results = scanForPattern(sig.hex, r.base, r.size);
                for (var res of results) {
                    found++;
                    totalFound++;
                    console.log('  [✅] Found at: ' + res.address);
                    console.log('      Offset from base: 0x' + res.address.sub(m.base).toString(16));
                    dumpContext(res.address, 16);
                }
            } catch (e) { /* skip inaccessible ranges */ }
        }

        if (found === 0) {
            console.log('  [!] Not found in mapped memory');
        } else {
            console.log('  → ' + found + ' occurrence(s)');
        }
        console.log('');
    }

    console.log('[i] Total: ' + totalFound + ' coordinate match(es)');
}

// Run on load
globalScan();

rpc.exports = {
    rescan: function(sigName) {
        if (sigName) {
            var sig = SIGNATURES.find(s => s.name === sigName);
            if (sig) {
                console.log('[*] Rescanning: ' + sig.name);
                var ranges = Process.enumerateRanges('rw-');
                for (var r of ranges) {
                    var results = scanForPattern(sig.hex, r.base, r.size);
                    for (var res of results) {
                        console.log('  [✅] ' + res.address + '  offset: 0x' + res.address.sub(m.base).toString(16));
                        dumpContext(res.address, 16);
                    }
                }
            }
        } else {
            globalScan();
        }
    }
};
