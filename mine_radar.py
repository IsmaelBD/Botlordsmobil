import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def find_mineral_mines():
    print("="*60)
    print("         RADAR DE MINERAL (138, 180) - RADIO 15M-30M")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    res_table_ptr = bridge.read_ptr(map_mgr_ptr + 0x70)
    
    items_ptr = layout_ptr + 0x20
    res_items_ptr = res_table_ptr + 0x20
    
    # Origen: Tu Castillo (Detectado previamente)
    home_x, home_y = 138, 180
    
    found_targets = []
    
    # Rango de busqueda (Radio 35m)
    for dy in range(-35, 35):
        for dx in range(-35, 35):
            tx, ty = home_x + dx, home_y + dy
            if tx < 0 or tx >= 512 or ty < 0 or ty >= 1024: continue
            
            # Manhattan distance
            dist = abs(dx) + abs(dy)
            
            # Filtro de distancia solicitado (15m - 30m)
            if 15 <= dist <= 35:
                tid = ty * 512 + tx
                data = bridge.read_memory(items_ptr + (tid * 4), "<HB")
                if data and data[1] == 2: # Kind 2 = Resource
                    tbl_id = data[0]
                    # Leer nivel de la tabla
                    res_base = res_items_ptr + (tbl_id * 48) # Padding IL2CPP
                    level_data = bridge.read_memory(res_base + 0x12, "B")
                    level = level_data[0] if level_data else 0
                    
                    found_targets.append({
                        "id": tid, "x": tx, "y": ty, "dist": dist, "lv": level, "tbl_id": tbl_id
                    })

    # Mostrar Resultados
    found_targets.sort(key=lambda x: x["dist"])
    
    print(f"{'DIST':<6} | {'COORD':<10} | {'LV':<3} | {'ID':<8}")
    print("-" * 40)
    for t in found_targets[:12]:
        print(f"{t['dist']:2}m    | ({t['x']:3},{t['y']:3}) | {t['lv']:2} | {t['id']:<8}")

    if not found_targets:
        print("[!] No se encontró mineral en el rango solicitado.")
    else:
        print(f"\n✅ Radar completo: {len(found_targets)} minas detectadas.")

if __name__ == "__main__":
    find_mineral_mines()
