"""
INYECTOR v7 - Protocolo 6615 NOTATK + MarchType byte
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

def read_remote(h, a, s):
    b = ctypes.create_string_buffer(s)
    kernel32.ReadProcessMemory(h, ctypes.c_void_p(a), b, s, None)
    return b.raw

def resolve_export(h, base, name):
    dos = read_remote(h, base, 64)
    elf = struct.unpack_from("<I", dos, 0x3C)[0]
    pe = read_remote(h, base+elf, 264)
    erva = struct.unpack_from("<I", pe, 24+112)[0]
    if not erva: return 0
    ed = read_remote(h, base+erva, 40)
    nf,nn = struct.unpack_from("<II", ed, 20)
    at,nt,ot = struct.unpack_from("<III", ed, 28)
    nps = read_remote(h, base+nt, nn*4)
    ords = read_remote(h, base+ot, nn*2)
    addrs = read_remote(h, base+at, nf*4)
    t = name.encode("ascii")
    for i in range(nn):
        nr = struct.unpack_from("<I", nps, i*4)[0]
        nb = read_remote(h, base+nr, 128).split(b"\x00")[0]
        if nb == t:
            o = struct.unpack_from("<H", ords, i*2)[0]
            return base + struct.unpack_from("<I", addrs, o*4)[0]
    return 0

def build_and_send(bridge, base, protocol_id, include_march_type, march_type_val):
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
    
    # Protocol
    sc += b"\x66\x41\xC7\x44\x24\x30"
    sc += struct.pack("<H", protocol_id)
    
    # AddSeqId
    sc += b"\x4C\x89\xE1"
    sc = emit_call(sc, fn["add_seq"])
    
    # MarchType byte (si se incluye)
    if include_march_type:
        sc += b"\x4C\x89\xE1"
        sc += b"\xB2" + struct.pack("B", march_type_val)
        sc = emit_call(sc, fn["ab"])
    
    # PointCode: zoneID (ushort) + pointID (byte)
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
    
    # tierCount = 1
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x01"
    sc = emit_call(sc, fn["ab"])
    
    # T1: [1, 0, 0, 0]
    for v in [1, 0, 0, 0]:
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA" + struct.pack("<I", v)
        sc = emit_call(sc, fn["au"])
    
    # petCount = 0
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x00"
    sc = emit_call(sc, fn["ab"])
    
    # Save Length
    sc += b"\x41\x8B\x44\x24\x18"
    sc += b"\x41\x89\x45\x00"
    
    # NetworkManager.Send(MP)
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
    print("="*55)
    print("  INYECTOR v7 - Pruebas de protocolo")
    print("="*55)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    connected = bridge.call_rva(0x1D27000)
    print(f"[+] OnReady: {connected}")
    print(f"[+] Destino: ({68}, {185}) Zone={ZONE_ID} Point={POINT_ID}")
    
    tests = [
        ("Proto 6615, sin MarchType", 6615, False, 0),
        ("Proto 6615, MarchType=7 (GatherMarching)", 6615, True, 7),
        ("Proto 6615, MarchType=2 (Gathering)", 6615, True, 2),
        ("Proto 2415, MarchType=7", 2415, True, 7),
    ]
    
    for i, (desc, proto, inc_mt, mt_val) in enumerate(tests):
        print(f"\n--- Test {i+1}: {desc} ---")
        confirm = input(f"¿Ejecutar? (s/n/q): ").strip().lower()
        if confirm == 'q': break
        if confirm != 's': continue
        
        pkt_len = build_and_send(bridge, base, proto, inc_mt, mt_val)
        print(f"  Packet length: {pkt_len} bytes")
        print(f"  → Verifica en el juego...")
        
        result = input("  ¿Resultado? (ok=marcha/dc=desconexión/nada): ").strip().lower()
        if result == 'ok':
            print(f"\n🎯 ¡ÉXITO con: {desc}!")
            return
        elif result == 'dc':
            print(f"  ✗ Desconexión — formato incorrecto")
        else:
            print(f"  ✗ Sin efecto — servidor rechazó")
    
    print("\n[*] Tests completados.")

if __name__ == "__main__":
    main()
