/**
 * packet_sniff.js — Network Packet Sniffer via Inline Hook
 * Hooks the NET_SEND function to capture all outgoing packets.
 * Captures protocol ID, packet data, and timing.
 *
 * Usage:
 *   frida -p <pid> -l packet_sniff.js
 */

var RVA = require('./_shared/rva_map');

var m = Process.getModuleByName(RVA.MODULE_NAME);
var baseAddr = m.base;

// Hook target
var netSendAddr = baseAddr.add(RVA.rvass.NET_SEND);
var origNetSend = new NativeFunction(netSendAddr, 'void', ['pointer']);

// Packet log
var packetLog = [];
var packetCount = 0;
var MAX_LOG = 1000;

/**
 * Parse a MessagePacket and extract protocol + data.
 */
function parsePacket(mp) {
    try {
        var protocol = mp.add(RVA.offsets.mp_protocol).readU16();
        var curPos   = mp.add(RVA.offsets.mp_current_pos).readU32();

        var bufObj  = mp.add(RVA.offsets.mp_buffer_obj).readPointer();
        var dataObj = bufObj.add(RVA.offsets.mp_data_obj).readPointer();
        var rawStart = dataObj.add(RVA.offsets.mp_raw_start);

        var dataHex = rawStart.readByteArray(curPos);

        return {
            protocol: protocol,
            length: curPos,
            data: hexfromBytes(dataHex),
            timestamp: Date.now(),
        };
    } catch (e) {
        return { protocol: -1, error: e.message };
    }
}

function hexfromBytes(bytes) {
    var hex = '';
    for (var i = 0; i < bytes.length; i++) {
        hex += ('0' + (bytes[i] & 0xFF).toString(16)).slice(-2);
    }
    return hex;
}

/**
 * Hook: intercept NET_SEND and log the packet.
 */
Interceptor.attach(netSendAddr, {
    onEnter: function(args) {
        var mp = args[0];
        var info = parsePacket(mp);
        packetCount++;

        var protoName = 'PROTO_' + info.protocol;
        console.log('\n[📤 PKT #' + packetCount + ']');
        console.log('    Protocol: ' + info.protocol + ' (0x' + info.protocol.toString(16) + ')');
        console.log('    Length:   ' + info.length + ' bytes');
        console.log('    Data:     ' + info.data.substring(0, 200) + (info.data.length > 200 ? '...' : ''));

        // Save to log (ring buffer)
        if (packetLog.length >= MAX_LOG) packetLog.shift();
        packetLog.push(info);
    }
});

console.log('[📡] Packet sniffer active — hooked NET_SEND at 0x' + netSendAddr.toString(16));
console.log('[i] Logging all outgoing packets...\n');

rpc.exports = {
    getLog: function(limit) {
        var l = limit || 100;
        return packetLog.slice(-l);
    },
    getCount: function() { return packetCount; },
    clearLog: function() { packetLog = []; },
    getByProtocol: function(proto) {
        return packetLog.filter(p => p.protocol === proto);
    }
};
