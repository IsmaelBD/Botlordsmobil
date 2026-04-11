"""
TEST v2: Con AddSeqId + verificar conectividad
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def emit_call(sc, addr):
    sc += b"\x48\xB8" + struct.pack("<Q", addr)
    sc += b"\xFF\xD0"
    return sc

def main():
    print("="*55)
    print("  TEST v2: Con AddSeqId + Check conectividad")
    print("="*55)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    # Primero verificar conectividad
    connected = bridge.call_rva(0x1D24FD0)  # NetworkManager.Connected()
    on_ready = bridge.call_rva(0x1D27000)    # NetworkManager.OnReady()
    
    print(f"[+] Connected(): {connected}")
    print(f"[+] OnReady(): {on_ready}")
    
    fn = {
        "get_mp":    base + 0x1D22900,
        "add_seq":   base + 0x1D22110,
        "ab":        base + 0x1D22860,
        "ah":        base + 0x1D224A0,
        "au":        base + 0x1D22430,
        "mp_send":   base + 0x1D23440,  # MessagePacket.Send(bool)
        "nm_send":   base + 0x1D28C40,  # NetworkManager.Send(MessagePacket) - static
    }
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    result_buf = rmem + 2048
    
    ZONE_ID = 372
    POINT_ID = 36
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54"
    sc += b"\x41\x55"
    
    sc += b"\x49\xBD" + struct.pack("<Q", result_buf)
    
    # 1. GetGuestMessagePack
    sc = emit_call(sc, fn["get_mp"])
    sc += b"\x49\x89\xC4"
    sc += b"\x4D\x89\x65\x00"  # save MP ptr
    
    # 2. Protocol = 2415
    sc += b"\x66\x41\xC7\x44\x24\x30"
    sc += struct.pack("<H", 2415)
    
    # 3. AddSeqId() - ESTA VEZ SÍ lo incluimos
    sc += b"\x4C\x89\xE1"
    sc = emit_call(sc, fn["add_seq"])
    
    # 4. Add data: zoneID, pointID, heroCount=0, tierCount=1, troops, petCount=0
    # zoneID (ushort)
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", ZONE_ID)
    sc = emit_call(sc, fn["ah"])
    
    # pointID (byte)
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
    
    # Save Length ANTES de send
    sc += b"\x41\x8B\x44\x24\x18"
    sc += b"\x41\x89\x45\x08"
    
    # 5. Llamar NetworkManager.Send(MP) - STATIC, no el instance Send
    sc += b"\x4C\x89\xE1"  # rcx = MP
    sc = emit_call(sc, fn["nm_send"])
    sc += b"\x41\x89\x45\x10"  # save result
    
    # Save Length DESPUÉS
    sc += b"\x41\x8B\x44\x24\x18"
    sc += b"\x41\x89\x45\x18"
    
    sc += b"\x41\x5D"
    sc += b"\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    print(f"\n[+] Shellcode: {len(sc)} bytes")
    confirm = input("¿Ejecutar? (s/n): ").strip().lower()
    if confirm != 's': return
    
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 15000)
    kernel32.CloseHandle(t)
    
    results = ctypes.create_string_buffer(64)
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(result_buf), results, 64, None)
    raw = results.raw
    
    mp = struct.unpack_from("<Q", raw, 0)[0]
    len_before = struct.unpack_from("<I", raw, 8)[0]
    nm_send_ret = struct.unpack_from("<I", raw, 16)[0]
    len_after = struct.unpack_from("<I", raw, 24)[0]
    
    print(f"\n  MP: 0x{mp:X}")
    print(f"  Length antes de NM.Send: {len_before}")
    print(f"  NM.Send() retorno: {nm_send_ret}")
    print(f"  Length después: {len_after}")
    print(f"\n🎯 Verifica en el juego.")

if __name__ == "__main__":
    main()
