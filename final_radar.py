import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def final_radar_scan():
    print("="*60)
    print("         RADAR ORBITAL - LOCALIZADOR DE RECURSOS")
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
    
    # Origen: Tu Castillo (138, 180)
    hx, hy = 138, 180
    
    print(f"[*] Escaneando recursos alrededor de tu posición central ({hx}, {hy})...\n")
    
    targets = []
    # Rango amplio (100m)
    stride = 4
    for dy in range(-45, 45):
        for dx in range(-45, 45):
            tx, ty = hx + dx, hy + dy
            if tx < 0 or tx >= 512 or ty < 0 or ty >= 1024: continue
            
            tid = ty * 512 + tx
            data = bridge.read_memory(items_ptr + (tid * stride), "<HB")
            if data and 2 <= data[1] <= 10: # Kind 2-6 son recursos tipicos
                kind = data[1]
                tbl_id = data[0]
                dist = abs(tx - hx) + abs(ty - hy)
                
                # Probar stride 40 (34 bytes + padding)
                res_base = res_items_ptr + (tbl_id * 40)
                level_data = bridge.read_memory(res_base + 0x12, "B")
                level = level_data[0] if level_data else 0
                
                targets.append({
                    "dist": dist, "x": tx, "y": ty, "kind": kind, "lv": level, "tid": tid
                })

    targets.sort(key=lambda x: x["dist"])
    
    print(f"{'DIST':<5} | {'COORD':<10} | {'TIPO':<10} | {'NIVEL'}")
    print("-" * 50)
    
    kind_names = {
        2: "Comida (Grain)",
        3: "Piedra (Rock)",
        4: "Madera (Timber)",
        5: "MINERAL (Ore)",
        6: "Oro (Gold)"
    }
    
    for t in targets[:20]:
        t_name = kind_names.get(t["kind"], "Desconocido")
        print(f"{t['dist']:3}m | ({t['x']:3}, {t['y']:3}) | {t_name:<10} | LV {t['lv']}")

    if not targets:
        print("[!] No se detectaron recursos en el radio escaneado.")
    else:
        print(f"\n✅ Análisis completo: {len(targets)} minas identificadas.")

if __name__ == "__main__":
    final_radar_scan()
