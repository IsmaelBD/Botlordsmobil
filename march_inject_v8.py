"""
INYECTOR v8 - T5 TroopData + 2415
El secreto podría ser que el servidor espera siempre 5 tiers (T1 a T5),
es decir 20 uints (80 bytes), en lugar de los 4 tiers viejos.
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32
ZONE_ID = 372
POINT_ID = 36

def emit_call(sc, addr):
    sc += b"\x48\xB8" + struct.pack("<Q", addr)
    sc += b"\xFF\xD0"
    return sc

def build_and_send(bridge, base):
    fn = {
        "get_mp":  base + 0x1D22900,
        "add_seq": base + 0x1D22110,
        "ab":      base + 0x1D22860,
        "ah":      base + 0x1D224A0,
        "au":      base + 0x1D22430,
        "nm_send": base + 0x1D28C40,
    }
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    rbuf = rmem + 2048
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54\x41\x55"
    sc += b"\x49\xBD" + struct.pack("<Q", rbuf)
    
    # GetGuestMessagePack
    sc = emit_call(sc, fn["get_mp"])
    sc += b"\x49\x89\xC4"
    
    # Protocol = 2415
    sc += b"\x66\x41\xC7\x44\x24\x30"
    sc += struct.pack("<H", 2415)
    
    # AddSeqId
    sc += b"\x4C\x89\xE1"
    sc = emit_call(sc, fn["add_seq"])
    
    # Zone y Point
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", ZONE_ID)
    sc = emit_call(sc, fn["ah"])
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", POINT_ID)
    sc = emit_call(sc, fn["ab"])
    
    # heroCount = 0
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x00"
    sc = emit_call(sc, fn["ab"])
    
    # tierCount = 5 (CRÍTICO: T1 a T5 = 5 arrays)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x05"
    sc = emit_call(sc, fn["ab"])
    
    # Enviar 5 tiers x 4 tropas = 20 uints
    for t in range(5):
        for s in range(4):
            sc += b"\x4C\x89\xE1"
            # 1 infantería T1 (t=0, s=0), 0 para el resto
            v = 1 if (t == 0 and s == 0) else 0
            sc += b"\xBA" + struct.pack("<I", v)
            sc = emit_call(sc, fn["au"])
    
    # petCount = 0
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x00"
    sc = emit_call(sc, fn["ab"])
    
    # Save Length
    sc += b"\x41\x8B\x44\x24\x18"
    sc += b"\x41\x89\x45\x00"
    
    # Send
    sc += b"\x4C\x89\xE1"
    sc = emit_call(sc, fn["nm_send"])
    
    sc += b"\x41\x5D\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 15000)
    kernel32.CloseHandle(t)
    
    r = ctypes.create_string_buffer(8)
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(rbuf), r, 8, None)
    pkt_len = struct.unpack_from("<I", r.raw, 0)[0]
    return pkt_len

def main():
    print("="*60)
    print("  INYECTOR v8 - Prueba con 5 Tiers (T5)")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    
    pkt_len = build_and_send(bridge, bridge.base)
    print(f"[+] Paquete enviado. Tamaño: {pkt_len} bytes.")
    print("🎯 Verifica en el juego si la marcha fue aceptada o si causó desconexión.")

if __name__ == "__main__":
    main()
