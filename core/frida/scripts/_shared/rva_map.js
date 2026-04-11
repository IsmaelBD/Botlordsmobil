/**
 * _shared/rva_map.js — Shared RVA constants for all Frida scripts
 * Load with: var RVA = require('./rva_map');
 */

module.exports = {
    // Process + module
    PROCESS_NAME: "Lords Mobile PC",
    MODULE_NAME: "GameAssembly.dll",

    // Critical RVAs (relative to module base)
    rvass: {
        GET_MP:  0x1D22900,  // Get empty MessagePacket from pool
        ADD_SEQ: 0x1D22110,  // Add sequence ID to packet
        ADD_US:  0x1D224A0,  // Add ushort prefix (protocol=6615)
        NET_SEND: 0x1D28C40, // Send packet to server
    },

    // MessagePacket offsets
    offsets: {
        mp_buffer_obj:   0x28,  // +0x28 → buffer object
        mp_data_obj:     0x20,  // +0x20 inside buffer → data object
        mp_raw_start:    0x20,  // +0x20 inside data → raw data start
        mp_current_pos:  0x18,  // current write position
        mp_protocol:     0x30,  // protocol ID
    },

    // March packet layout
    march: {
        protocol:     6615,
        header_size:  10,
        content_size:  101,
        total_size:   111,
        zone_offset:  72,   // Zone ID offset in content (after 10-byte header)
        point_offset: 74,   // Point ID offset in content
    },

    // Protocol IDs
    protocols: {
        VERSION:     13000,
        HARDWARE:   1024,
        LOGIN:      1043,
        GIFT_REDEEM: 1420,
        TROOP_MARCH:  6615,
    },
};
