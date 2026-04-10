import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def neighbor_scan():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    res_table_ptr = bridge.read_ptr(map_mgr_ptr + 0x70)
    
    items_ptr = layout_ptr + 0x20
    res_items_ptr = res_table_ptr + 0x20
    
    hx, hy = 138, 180
    print(f"[*] Analizando recursos en el radio de tu castillo ({hx}, {hy})...\n")
    
    found = []
    # Rango 150m
    for dy in range(-150, 150):
        for dx in range(-150, 150):
            tx, ty = hx + dx, hy + dy
            if tx < 0 or tx >= 512 or ty < 0 or ty >= 1024: continue
            
            tid = ty * 512 + tx
            data = bridge.read_memory(items_ptr + (tid * 4), "<HB")
            if data and 2 <= data[1] <= 6:
                kind = data[1]
                dist = abs(tx - hx) + abs(ty - hy)
                
                # Intentar leer playerName (offset 0x20)
                res_base = res_items_ptr + (data[0] * 40)
                p_name_ptr = bridge.read_ptr(res_base + 0x20)
                p_name = bridge.read_cstring(p_name_ptr) if p_name_ptr else "Nadie"
                
                found.append((dist, tx, ty, kind, p_name))

    found.sort() # Por distancia
    
    print(f"{'DIST':<5} | {'COORD':<10} | {'KIND':<4} | {'OCUPANTE'}")
    print("-" * 45)
    for f in found[:30]:
        print(f"{f[0]:3}m | ({f[1]:3}, {f[2]:3}) | {f[3]:4} | {f[4]}")

if __name__ == "__main__":
    neighbor_scan()
