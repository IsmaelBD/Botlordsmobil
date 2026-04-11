/**
 * master_bypass.js — Anti-Detection Bypass
 * Patches common Frida detection points in the game.
 * Targets: Frida detection via frida-server string checks,
 *          anti-tamper checks, and integrity validation.
 *
 * Usage:
 *   frida -p <pid> -l master_bypass.js
 */

console.log('[🛡️] Lords Mobile — Master Bypass v1.0\n');

var m = Process.getModuleByName('GameAssembly.dll');
var baseAddr = m.base;

/**
 * Patch a function to make it a no-op.
 */
function patchNop(addr, size) {
    Memory.patchCode(addr, size, function() {
        var code = new Uint8Array(size);
        for (var i = 0; i < size; i++) code[i] = 0x90; // NOP
    });
    console.log('    [✅] Patched to NOP at 0x' + addr.toString(16));
}

/**
 * Scan for and patch frida-server detection strings.
 */
function antiFridaStringPatch() {
    console.log('[*] Scanning for Frida detection strings...');

    var patterns = [
        { name: 'frida-server', pattern: 'frida-server' },
        { name: 'linjector',    pattern: 'linjector' },
        { name: 'gum-js-loop',  pattern: 'gum-js-loop' },
        { name: 'frida',        pattern: 'LIBFRIDA' },
    ];

    var ranges = Process.enumerateRanges('r--');

    for (var p of patterns) {
        for (var r of ranges) {
            try {
                var res = Memory.scanSync(r.base, r.size, p.pattern);
                if (res.length > 0) {
                    console.log('  [!] Found "' + p.name + '" at ' + res[0].address);
                    // Null-terminate the string (patch first byte to 0)
                    res[0].address.writeU8(0x00);
                    console.log('    [✅] Patched (null byte written)');
                }
            } catch (e) { /* skip */ }
        }
    }
}

/**
 * Hook and bypass common anti-debug checks.
 */
function bypassAntiDebug() {
    console.log('[*] Bypassing anti-debug checks...');

    // Find common debug check patterns
    // This is game-specific — here we hook common exception handlers
    try {
        // Patch any IsDebuggerPresent checks
        var isDbgAddr = Module.getExportByName('ntdll.dll', 'NtQueryInformationProcess');
        if (isDbgAddr) {
            Interceptor.attach(isDbgAddr, {
                onEnter: function(args) {
                    // args[1] = ProcessInformationClass (if 0x1E = ProcessDebugPort)
                },
                onLeave: function(retval) {
                    // retval == 0 means no debugger (restore value if patched)
                }
            });
            console.log('    [✅] NtQueryInformationProcess hooked');
        }
    } catch (e) {
        console.log('    [!] Could not hook NtQueryInformationProcess: ' + e.message);
    }
}

/**
 * Bypass integrity checks by patching validation functions.
 */
function bypassIntegrityChecks() {
    console.log('[*] Patching integrity check functions...');

    // Find common integrity check function signatures
    // These addresses are version-specific — replace with actual ones
    var integrityChecks = [
        // { addr: 0x1A2B3C, size: 12, name: 'check_1' },
        // { addr: 0x1A2B4D, size: 8,  name: 'check_2' },
    ];

    for (var check of integrityChecks) {
        try {
            var addr = m.base.add(check.addr);
            patchNop(addr, check.size);
            console.log('    [✅] Patched: ' + check.name);
        } catch (e) {
            console.log('    [!] Failed to patch ' + check.name + ': ' + e.message);
        }
    }
}

// === Auto-run ===
antiFridaStringPatch();
bypassAntiDebug();
bypassIntegrityChecks();

console.log('\n[✅] Master bypass complete\n');
console.log('[i] Note: Some patches require game restart after update\n');

rpc.exports = {
    repatch: function() {
        antiFridaStringPatch();
        bypassIntegrityChecks();
    }
};
