"""
INYECTOR v6 - Usar el Guest MessagePacket directamente
El Guest MP tiene Channel=1 y Delimiter=0 (correcto).
Crear uno nuevo daba Delimiter=1024 (incorrecto).
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

def main():
    print("="*55)
    print("  INYECTOR v6 - Guest MP Directo")
    print("="*55)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    # Obtener Guest MP  
    guest_mp = bridge.call_rva(0x1D22900)
    print(f"[+] Guest MP: 0x{guest_mp:X}")
    
    # Verificar su estado
    ch = bridge.read_memory(guest_mp + 0x1C, "B")
    dl = bridge.read_memory(guest_mp + 0x20, "<I")
    off = bridge.read_memory(guest_mp + 0x10, "<I")
    print(f"    Channel: {ch[0] if ch else '?'}")
    print(f"    Delimiter: {dl[0] if dl else '?'}")
    print(f"    Offset: {off[0] if off else '?'}")
    
    # Leer héroes libres
    dm_ptr = bridge.call_rva(0x2914F50)
    march_arr = bridge.read_ptr(dm_ptr + 0x1078)
    arr_len = bridge.read_memory(march_arr + 0x18, "<I")[0]
    
    used_heroes = set()
    for i in range(min(arr_len, 8)):
        mb = march_arr + 0x20 + (i * 0x50)
        mt = bridge.read_memory(mb, "<I")
        if mt and mt[0] > 0:
            ha = bridge.read_ptr(mb + 0x08)
            if ha:
                hc = bridge.read_memory(ha + 0x18, "<I")[0]
                for h in range(min(hc, 5)):
                    hid = bridge.read_memory(ha + 0x20 + (h*2), "<H")
                    if hid and hid[0] > 0:
                        used_heroes.add(hid[0])
    
    # Leer todos los héroes disponibles
    fight_hero_count = bridge.read_memory(dm_ptr + 0x1120, "<I")
    fhc = fight_hero_count[0] if fight_hero_count else 0
    fight_hero_ids = bridge.read_ptr(dm_ptr + 0x1110)
    
    all_heroes = []
    if fight_hero_ids:
        for h in range(min(fhc, 20)):
            hid = bridge.read_memory(fight_hero_ids + 0x20 + (h*4), "<I")
            if hid and hid[0] > 0:
                all_heroes.append(hid[0])
    
    free_heroes = [h for h in all_heroes if h not in used_heroes]
    print(f"\n[+] Héroes en uso: {used_heroes}")
    print(f"[+] Héroes totales: {all_heroes[:10]}")
    print(f"[+] Héroes libres: {free_heroes[:5]}")
    
    # Seleccionar un héroe libre (o ninguno)
    hero_to_send = free_heroes[0] if free_heroes else 0
    hero_count = 1 if hero_to_send > 0 else 0
    
    print(f"[+] Héroe a enviar: {hero_to_send} (count={hero_count})")
    
    fn = {
        "get_mp": base + 0x1D22900,  # GetGuestMessagePack
        "ab":     base + 0x1D22860,  # Add(byte)
        "ah":     base + 0x1D224A0,  # Add(ushort)  
        "au":     base + 0x1D22430,  # Add(uint)
        "send":   base + 0x1D23440,  # Send(bool)
    }
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 8192, 0x3000, 0x40)
    rret = rmem + 4096
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x68"
    sc += b"\x41\x54"
    
    # 1. GetGuestMessagePack() - retorna un MP fresco y limpio
    sc = emit_call(sc, fn["get_mp"])
    sc += b"\x49\x89\xC4"  # r12 = MP
    
    # 2. Protocol = 2415 en MP+0x30
    sc += b"\x66\x41\xC7\x44\x24\x30"
    sc += struct.pack("<H", 2415)
    
    # 3. Add(ushort zoneID=372)
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", ZONE_ID)
    sc = emit_call(sc, fn["ah"])
    
    # 4. Add(byte pointID=36)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", POINT_ID)
    sc = emit_call(sc, fn["ab"])
    
    # 5. Add(byte heroCount)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", hero_count)
    sc = emit_call(sc, fn["ab"])
    
    # 6. Add hero IDs if any
    if hero_to_send > 0:
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA" + struct.pack("<H", hero_to_send & 0xFFFF)
        sc = emit_call(sc, fn["ah"])
    
    # 7. TroopData: 4 tiers, T1=[1,0,0,0], rest=[0,0,0,0]
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x04"
    sc = emit_call(sc, fn["ab"])
    
    for t in range(4):
        for s in range(4):
            sc += b"\x4C\x89\xE1"
            v = 1 if (t == 0 and s == 0) else 0
            sc += b"\xBA" + struct.pack("<I", v)
            sc = emit_call(sc, fn["au"])
    
    # 8. petCount = 0
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x00"
    sc = emit_call(sc, fn["ab"])
    
    # 9. Send(false)
    sc += b"\x4C\x89\xE1"
    sc += b"\x31\xD2"
    sc = emit_call(sc, fn["send"])
    
    # Save result
    sc += b"\x49\x89\xC4"
    sc += b"\x48\xBB" + struct.pack("<Q", rret)
    sc += b"\x4C\x89\x23"
    
    sc += b"\x41\x5C"
    sc += b"\x48\x83\xC4\x68"  
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    print(f"\n[+] Shellcode: {len(sc)} bytes")
    print(f"    Protocol: 2415")
    print(f"    Zone={ZONE_ID}, Point={POINT_ID} -> (68, 185)")
    print(f"    Hero: {hero_to_send}")
    print(f"    Tropas: 1 infantería T1")
    
    confirm = input("\n¿Ejecutar? (s/n): ").strip().lower()
    if confirm != 's': return
    
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 15000)
    r = ctypes.c_ulonglong()
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(rret), ctypes.byref(r), 8, None)
    kernel32.CloseHandle(t)
    print(f"[+] Send() = 0x{r.value:X} (1=OK, 0=fail)")
    print("🎯 Verifica en el juego.")

if __name__ == "__main__":
    main()
