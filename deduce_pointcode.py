"""
Deducir la formula de PointCode desde datos conocidos
"""
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def deduce():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    kingdom_id = bridge.read_memory(map_mgr_ptr + 0x1B4, "<H")[0]
    world_ox = bridge.read_memory(map_mgr_ptr + 0x1B6, "<H")[0]
    world_oy = bridge.read_memory(map_mgr_ptr + 0x1B8, "<H")[0]
    world_max_x = bridge.read_memory(map_mgr_ptr + 0x1BA, "<H")[0]
    world_max_y = bridge.read_memory(map_mgr_ptr + 0x1BC, "<H")[0]
    
    print(f"Kingdom={kingdom_id}, OX={world_ox}, OY={world_oy}, MaxX={world_max_x}, MaxY={world_max_y}")
    
    # Dato conocido: PointCode(507, 59) -> MapID=127931 -> (443, 249)
    known_zone = 507
    known_point = 59
    known_x = 443
    known_y = 249
    
    # Probar multiples PointCodes para deducir el patron
    test_cases = [
        (507, 59),
        (506, 59),
        (508, 59),
        (507, 58),
        (507, 60),
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
        (100, 50),
    ]
    
    print("\nVerificando PointCodes con la función del juego:")
    print(f"{'Zone':>6} {'Pt':>3} | {'MapID':>8} | {'X':>4} {'Y':>4}")
    print("-"*40)
    
    results = []
    for zone, pt in test_cases:
        mid = bridge.call_rva(0x5A5380, [zone, pt, kingdom_id])
        x = mid % 512
        y = mid // 512
        results.append((zone, pt, mid, x, y))
        print(f"{zone:6} {pt:3} | {mid:8} | {x:4} {y:4}")
    
    # Ahora la inversa: para (68, 185) cual es el PointCode?
    target_map_id = 185 * 512 + 68  # 94788
    
    # Probar la función estática MapIDToPointCode
    # RVA: 0x5A4C60
    # Firma: static void MapIDToPointCode(int mapID, out ushort zoneID, out byte pointID, ushort kingdomID)
    # Los out params son complicados. Usemos shellcode que escriba los resultados.
    
    import ctypes
    import struct
    
    kernel32 = ctypes.windll.kernel32
    base = bridge.base
    
    # Alocar buffer para out params
    remote_mem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    out_zone_addr = remote_mem + 256  # ushort
    out_point_addr = remote_mem + 264  # byte
    ret_addr = remote_mem + 272
    
    # Shellcode: call MapIDToPointCode(mapID, &outZone, &outPoint, kingdomID)
    # rcx = mapID, rdx = &outZone, r8 = &outPoint, r9 = kingdomID
    func_addr = base + 0x5A4C60
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x28"  # sub rsp, 0x28
    
    # rcx = mapID
    sc += b"\x48\xB9" + struct.pack("<Q", target_map_id)
    # rdx = &outZone
    sc += b"\x48\xBA" + struct.pack("<Q", out_zone_addr)
    # r8 = &outPoint
    sc += b"\x49\xB8" + struct.pack("<Q", out_point_addr)
    # r9 = kingdomID
    sc += b"\x49\xB9" + struct.pack("<Q", kingdom_id)
    
    # call func
    sc += b"\x48\xB8" + struct.pack("<Q", func_addr)
    sc += b"\xFF\xD0"
    
    sc += b"\x48\x83\xC4\x28"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, remote_mem, bytes(sc), len(sc), None)
    
    thread = kernel32.CreateRemoteThread(bridge.handle, None, 0, remote_mem, None, 0, None)
    kernel32.WaitForSingleObject(thread, 5000)
    kernel32.CloseHandle(thread)
    
    # Leer out params
    zone_val = bridge.read_memory(out_zone_addr, "<H")
    point_val = bridge.read_memory(out_point_addr, "B")
    
    target_zone = zone_val[0] if zone_val else 0
    target_point = point_val[0] if point_val else 0
    
    print(f"\n{'='*40}")
    print(f"  MapIDToPointCode({target_map_id}) para ({68}, {185}):")
    print(f"  ZoneID = {target_zone}")  
    print(f"  PointID = {target_point}")
    print(f"{'='*40}")
    
    # Verificar reversa
    if target_zone > 0 or target_point > 0:
        verify = bridge.call_rva(0x5A5380, [target_zone, target_point, kingdom_id])
        vx = verify % 512
        vy = verify // 512
        print(f"  Verificación: PointCodeToMapID -> ({vx}, {vy})")

if __name__ == "__main__":
    deduce()
