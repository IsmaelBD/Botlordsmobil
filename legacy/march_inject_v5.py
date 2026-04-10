"""
INYECTOR v5 - Con héroes libres + sin AddSeqId
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

ZONE_ID = 372
POINT_ID = 36
FREE_HERO = 9  # Héroe libre (ID 1 está en marcha activa)

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
    nf = struct.unpack_from("<I", ed, 20)[0]
    nn = struct.unpack_from("<I", ed, 24)[0]
    at = struct.unpack_from("<I", ed, 28)[0]
    nt = struct.unpack_from("<I", ed, 32)[0]
    ot = struct.unpack_from("<I", ed, 36)[0]
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

def emit_call(sc, addr):
    sc += b"\x48\xB8" + struct.pack("<Q", addr)
    sc += b"\xFF\xD0"
    return sc

def main():
    print("="*55)
    print("  INYECTOR v5 - Héroe libre + Sin AddSeqId")
    print("="*55)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    il2cpp_new = resolve_export(bridge.handle, base, "il2cpp_object_new")
    guest = bridge.call_rva(0x1D22900)
    klass = bridge.read_ptr(guest)
    
    print(f"[+] il2cpp_object_new: 0x{il2cpp_new:X}")
    print(f"[+] MP Klass: 0x{klass:X}")
    print(f"[+] Héroe libre: {FREE_HERO}")
    print(f"[+] Destino: Zone={ZONE_ID}, Point={POINT_ID}")
    
    fn = {
        "new":  il2cpp_new,
        "ctor": base + 0x1D238A0,
        "ab":   base + 0x1D22860, # Add(byte)
        "ah":   base + 0x1D224A0, # Add(ushort)
        "au":   base + 0x1D22430, # Add(uint)
        "send": base + 0x1D23440,
    }
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 8192, 0x3000, 0x40)
    rret = rmem + 4096
    
    sc = bytearray()
    # Prologue
    sc += b"\x48\x83\xEC\x68"
    sc += b"\x41\x54"
    sc += b"\x41\x55"
    
    # 1. il2cpp_object_new(klass)
    sc += b"\x48\xB9" + struct.pack("<Q", klass)
    sc = emit_call(sc, fn["new"])
    sc += b"\x49\x89\xC4"  # r12 = MP
    
    # 2. .ctor(MP, 1024)
    sc += b"\x4C\x89\xE1"
    sc += b"\xBA\x00\x04\x00\x00"
    sc = emit_call(sc, fn["ctor"])
    
    # 3. Channel = 1
    sc += b"\x41\xC6\x44\x24\x1C\x01"
    
    # 4. Protocol = 2415
    sc += b"\x66\x41\xC7\x44\x24\x30"
    sc += struct.pack("<H", 2415)
    
    # 5. Add(ushort zoneID)
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", ZONE_ID)
    sc = emit_call(sc, fn["ah"])
    
    # 6. Add(byte pointID)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", POINT_ID)
    sc = emit_call(sc, fn["ab"])
    
    # 7. Add(byte heroCount = 1)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x01"
    sc = emit_call(sc, fn["ab"])
    
    # 8. Add(ushort heroID)
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", FREE_HERO)
    sc = emit_call(sc, fn["ah"])
    
    # 9. Add(byte tierCount = 4) 
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x04"
    sc = emit_call(sc, fn["ab"])
    
    # 10. T1: [1,0,0,0]
    for v in [1, 0, 0, 0]:
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA" + struct.pack("<I", v)
        sc = emit_call(sc, fn["au"])
    # T2-T4: [0,0,0,0] x3
    for _ in range(12):
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA\x00\x00\x00\x00"
        sc = emit_call(sc, fn["au"])
    
    # 11. Add(byte petCount = 0)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x00"
    sc = emit_call(sc, fn["ab"])
    
    # 12. Send(false)
    sc += b"\x4C\x89\xE1"
    sc += b"\x31\xD2"
    sc = emit_call(sc, fn["send"])
    
    # Save result
    sc += b"\x49\x89\xC5"
    sc += b"\x48\xBB" + struct.pack("<Q", rret)
    sc += b"\x4C\x89\x2B"
    
    # Epilogue
    sc += b"\x41\x5D"
    sc += b"\x41\x5C"
    sc += b"\x48\x83\xC4\x68"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    print(f"\n[+] Shellcode: {len(sc)} bytes")
    confirm = input("¿Ejecutar? (s/n): ").strip().lower()
    if confirm != 's': return
    
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 15000)
    r = ctypes.c_ulonglong()
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(rret), ctypes.byref(r), 8, None)
    kernel32.CloseHandle(t)
    print(f"[+] Resultado: 0x{r.value:X}")
    print("🎯 Verifica en el juego.")

if __name__ == "__main__":
    main()
