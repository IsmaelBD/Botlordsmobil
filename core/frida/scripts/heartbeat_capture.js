/**
 * heartbeat_capture.js — Heartbeat / Keep-Alive Packet Capture
 * Hooks network send to capture periodic heartbeat packets.
 * These packets keep the session alive and can be replayed.
 *
 * Usage:
 *   frida -p <pid> -l heartbeat_capture.js
 */

var RVA = require('./_shared/rva_map');

var m = Process.getModuleByName(RVA.MODULE_NAME);
var baseAddr = m.base;

var netSendAddr = baseAddr.add(RVA.rvass.NET_SEND);

// Heartbeat candidates (small packets, sent periodically)
var heartbeatCandidates = [];
var lastCaptureTime = 0;

Interceptor.attach(netSendAddr, {
    onEnter: function(args) {
        try {
            var mp = args[0];
            var curPos = mp.add(RVA.offsets.mp_current_pos).readU32();
            var protocol = mp.add(RVA.offsets.mp_protocol).readU16();

            // A heartbeat is typically small (<50 bytes) and sent regularly
            if (curPos > 0 && curPos < 50) {
                var bufObj  = mp.add(RVA.offsets.mp_buffer_obj).readPointer();
                var dataObj = bufObj.add(RVA.offsets.mp_data_obj).readPointer();
                var rawStart = dataObj.add(RVA.offsets.mp_raw_start);
                var data = rawStart.readByteArray(curPos);

                var hex = '';
                for (var i = 0; i < data.length; i++) {
                    hex += ('0' + (data[i] & 0xFF).toString(16)).slice(-2);
                }

                var now = Date.now();
                var interval = heartbeatCandidates.length > 0
                    ? now - lastCaptureTime
                    : 0;
                lastCaptureTime = now;

                console.log('[💓 HEARTBEAT CANDIDATE]');
                console.log('    Protocol: ' + protocol);
                console.log('    Size:     ' + curPos + ' bytes');
                console.log('    Interval: ' + interval + 'ms');
                console.log('    Hex:      ' + hex);

                heartbeatCandidates.push({
                    protocol: protocol,
                    data: hex,
                    timestamp: now,
                    interval: interval,
                });
            }
        } catch (e) {
            // Ignore read errors
        }
    }
});

console.log('[💓] Heartbeat capture active\n');

rpc.exports = {
    getCandidates: function() {
        return heartbeatCandidates;
    },
    getLastInterval: function() {
        if (heartbeatCandidates.length >= 2) {
            var last = heartbeatCandidates[heartbeatCandidates.length - 1];
            var prev = heartbeatCandidates[heartbeatCandidates.length - 2];
            return last.timestamp - prev.timestamp;
        }
        return 0;
    },
    clear: function() { heartbeatCandidates = []; }
};
