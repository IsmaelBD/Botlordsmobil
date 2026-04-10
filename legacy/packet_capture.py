"""
CAPTURA DE PAQUETE - Lee los buffers internos de red
después de una marcha manual para obtener el formato real.
"""
import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def read_remote(handle, addr, size):
    buf = ctypes.create_string_buffer(size)
    kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, size, None)
    return buf.raw

def main():
    print("="*60)
    print("  CAPTURA DE PAQUETE DE MARCHA")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    dm_ptr = bridge.call_rva(0x2914F50)
    print(f"[+] DataManager: 0x{dm_ptr:X}")
    
    # ============================================================
    # 1. Leer MarchEventData activa (datos de la marcha manual)
    # ============================================================
    march_array_ptr = bridge.read_ptr(dm_ptr + 0x1078)
    array_len = bridge.read_memory(march_array_ptr + 0x18, "<I")[0]
    items_base = march_array_ptr + 0x20
    
    print(f"\n[*] MarchEventData[] len={array_len}")
    
    for i in range(min(array_len, 8)):
        base = items_base + (i * 0x50)
        mt = bridge.read_memory(base, "<I")
        march_type = mt[0] if mt else 0
        if march_type == 0: continue
        
        print(f"\n  [MARCHA #{i}]")
        print(f"    Type (EMarchEventType): {march_type}")
        
        # PointCode (raw)
        pc_raw = bridge.read_memory(base + 0x18, "8B")
        if pc_raw:
            print(f"    PointCode raw: {' '.join(f'{b:02X}' for b in pc_raw)}")
            zone_id = pc_raw[0] | (pc_raw[1] << 8)
            point_id = pc_raw[2]
            print(f"    ZoneID={zone_id}, PointID={point_id}")
            
            # Verificar coords
            mid = bridge.call_rva(0x5A5380, [zone_id, point_id, 1977])
            mx, my = mid % 512, mid // 512
            print(f"    -> Coordenadas: ({mx}, {my})")
        
        # Héroes
        hero_arr = bridge.read_ptr(base + 0x08)
        if hero_arr:
            hc = bridge.read_memory(hero_arr + 0x18, "<I")[0]
            heroes = []
            for h in range(min(hc, 10)):
                hid = bridge.read_memory(hero_arr + 0x20 + (h*2), "<H")
                if hid: heroes.append(hid[0])
            print(f"    Héroes ({hc}): {heroes}")
        
        # Tropas
        troop_arr = bridge.read_ptr(base + 0x10)
        if troop_arr:
            tc = bridge.read_memory(troop_arr + 0x18, "<I")[0]
            print(f"    TroopData ({tc} tiers):")
            for t in range(min(tc, 5)):
                inner = bridge.read_ptr(troop_arr + 0x20 + (t*8))
                if inner:
                    il = bridge.read_memory(inner + 0x18, "<I")[0]
                    vals = []
                    for s in range(min(il, 4)):
                        v = bridge.read_memory(inner + 0x20 + (s*4), "<I")
                        vals.append(v[0] if v else 0)
                    if any(v > 0 for v in vals):
                        print(f"      T{t+1}: {vals}")
        
        # PointKind y Level
        pk = bridge.read_memory(base + 0x30, "B")
        dl = bridge.read_memory(base + 0x32, "<H")
        print(f"    PointKind: {pk[0] if pk else '?'}")
        print(f"    Level: {dl[0] if dl else '?'}")
    
    # ============================================================
    # 2. Intentar leer los static fields del NetworkManager
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  ESTADO DEL NETWORKMANAGER")
    print(f"{'='*60}")
    
    # Obtener klass de NetworkManager
    nm_instance = bridge.call_rva(0x1D2CD40)
    if nm_instance:
        nm_klass = bridge.read_ptr(nm_instance)
        print(f"[+] NM Instance: 0x{nm_instance:X}")
        print(f"[+] NM Klass: 0x{nm_klass:X}")
        
        # En IL2CPP, static_fields suele estar en klass + 0xB8
        # Pero varía. Escanear offsets comunes
        for sf_offset in [0xB8, 0xC0, 0xC8, 0xD0, 0xD8]:
            sf_ptr = bridge.read_ptr(nm_klass + sf_offset)
            if sf_ptr and 0x100000000 < sf_ptr < 0x800000000000:
                # Verificar si SendData (offset 0xA8 en statics) es un array válido
                send_data_ptr = bridge.read_ptr(sf_ptr + 0xA8)
                if send_data_ptr and 0x100000000 < send_data_ptr < 0x800000000000:
                    # Verificar si es un byte[] (tiene length > 0)
                    sd_len = bridge.read_memory(send_data_ptr + 0x18, "<I")
                    if sd_len and 0 < sd_len[0] < 65536:
                        write_pos = bridge.read_memory(sf_ptr + 0xB8, "<I")
                        wp = write_pos[0] if write_pos else 0
                        print(f"\n[+] Static fields en klass+0x{sf_offset:X}: 0x{sf_ptr:X}")
                        print(f"    SendData[]: 0x{send_data_ptr:X} (len={sd_len[0]})")
                        print(f"    write_pos: {wp}")
                        
                        if wp > 0 and wp < sd_len[0]:
                            # Leer los últimos bytes enviados
                            raw = read_remote(bridge.handle, 
                                            send_data_ptr + 0x20, 
                                            min(wp, 256))
                            print(f"\n    [RAW PACKET DATA] ({wp} bytes):")
                            # Mostrar en filas de 16
                            for row in range(0, min(wp, 256), 16):
                                chunk = raw[row:row+16]
                                hex_str = " ".join(f"{b:02X}" for b in chunk)
                                ascii_str = "".join(
                                    chr(b) if 32 <= b <= 126 else "." 
                                    for b in chunk
                                )
                                print(f"    {row:04X}: {hex_str:<48} {ascii_str}")
                        break

if __name__ == "__main__":
    main()
