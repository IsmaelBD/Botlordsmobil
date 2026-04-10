/**
 * inject_march.js — Troop March Injection
 * Injects synchronized troop marches into Lords Mobile.
 * Based on v13.9.1 method with live sequence synchronization.
 *
 * Usage:
 *   frida -p <pid> -l inject_march.js
 *   or from FridaBridge: bridge.load_script("inject_march")
 */

var RVA = require('./_shared/rva_map');

var m = Process.getModuleByName(RVA.MODULE_NAME);
var baseAddr = m.base;

var fnGetMP   = new NativeFunction(baseAddr.add(RVA.rvass.GET_MP),   'pointer', []);
var fnAddSeq  = new NativeFunction(baseAddr.add(RVA.rvass.ADD_SEQ),  'void',    ['pointer']);
var fnAddUS   = new NativeFunction(baseAddr.add(RVA.rvass.ADD_US),   'void',    ['pointer', 'uint16']);
var fnNetSend = new NativeFunction(baseAddr.add(RVA.rvass.NET_SEND), 'void',    ['pointer']);

// Default troop march content (101 bytes, no header)
var DEFAULT_CONTENT_HEX =
    "09000000000000002c0100000000000000000000000000006400000000000000000000000000000064000000000000000000000000000000000000000000000000000000000000fb013b0000000000000000000000000000000000000000000000000000";

/**
 * Inject a synchronized troop march.
 * @param {number} zone - Zone ID (e.g., 507)
 * @param {number} point - Point ID (e.g., 59)
 * @param {string} contentHex - Optional custom 101-byte hex content
 */
function injectSyncedMarch(zone, point, contentHex) {
    var contentSize = 101;
    var contentBytes = contentHex || DEFAULT_CONTENT_HEX;

    console.log('[🚀] v13.9.1 — Synced March Injection');
    console.log('    Target: zone=' + zone + ', point=' + point);

    // 1. Get clean MessagePacket
    var mp = fnGetMP();
    if (mp.isNull()) {
        console.log('[!] Failed to get MessagePacket (pool empty?)');
        return false;
    }

    // 2. Allocate content in native memory
    var contentBin = Memory.alloc(contentSize);
    for (var i = 0; i < contentSize; i++) {
        contentBin.add(i).writeU8(parseInt(contentBytes.substr(i * 2, 2), 16));
    }

    // 3. Encode coordinates (little-endian)
    contentBin.add(RVA.march.zone_offset).writeU16(zone);
    contentBin.add(RVA.march.point_offset).writeU8(point);

    // 4. Synchronize sequence ID with server
    fnAddSeq(mp);
    fnAddUS(mp, 1);  // ushort prefix = 1 for protocol 6615

    // 5. Copy content after sequence header
    var bufObj   = mp.add(RVA.offsets.mp_buffer_obj).readPointer();
    var dataObj  = bufObj.add(RVA.offsets.mp_data_obj).readPointer();
    var curPos   = mp.add(RVA.offsets.mp_current_pos).readU32();
    var rawStart = dataObj.add(RVA.offsets.mp_raw_start).add(curPos);

    Memory.copy(rawStart, contentBin, contentSize);

    // 6. Update length and protocol
    mp.add(RVA.offsets.mp_current_pos).writeU32(curPos + contentSize);
    mp.add(RVA.offsets.mp_protocol).writeU16(RVA.march.protocol);

    // 7. Send!
    fnNetSend(mp);

    console.log('[✅] March sent — zone=' + zone + ', point=' + point);
    return true;
}

// Auto-execute demo (zone=507, point=59 = the forest)
rpc.exports = {
    injectMarch: function(zone, point, contentHex) {
        return injectSyncedMarch(zone || 507, point || 59, contentHex);
    }
};

// Default call if run directly
injectSyncedMarch(507, 59);
