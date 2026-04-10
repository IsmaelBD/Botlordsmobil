import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def proximity_scan():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    items_ptr = layout_ptr + 0x20
    
    # Origen: Tu Castillo
    hx, hy = 138, 180
    
    print(f"[*] Analizando vecindario de ({hx}, {hy})...")
    
    found = []
    # Rango 100m
    for dy in range(-100, 100):
        for dx in range(-100, 100):
            tx, ty = hx + dx, hy + dy
            if tx < 0 or tx >= 512 or ty < 0 or ty >= 1024: continue
            
            tid = ty * 512 + tx
            data = bridge.read_memory(items_ptr + (tid * 4), "<HB")
            if data and data[1] != 0:
                dist = abs(dx) + abs(dy)
                found.append((dist, tx, ty, data[1], data[0]))

    found.sort() # Ordenar por distancia
    
    print(f"{'DIST':<5} | {'COORD':<10} | {'KIND':<4} | {'TblID'}")
    print("-" * 35)
    for f in found[:30]:
        print(f"{f[0]:3}m | ({f[1]:3}, {f[2]:3}) | {f[3]:4} | {f[4]}")

if __name__ == "__main__":
    proximity_scan()
