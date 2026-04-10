import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar
import time

def scan_nearby_resources():
    print("="*60)
    print("           RADAR DE RECURSOS (BETA - ESCANEO DE RAM)")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients:
        print("[!] No hay clientes activos.")
        return

    client = radar.clients[0]
    pid = client["pid"]
    base = client["assembly_base"]
    
    bridge = InternalBridge(pid, base)
    
    # 1. Obtener Instancias
    # get_Instance() DataManager: 0x2914F50
    dm_ptr = bridge.call_rva(0x2914F50)
    if not dm_ptr:
        print("[!] Error: No se pudo obtener DataManager.")
        return
        
    # Usar RVA de get_MapDataController() para obtener MapManager: 0x2915080
    map_mgr_ptr = bridge.call_rva(0x2915080)
    if not map_mgr_ptr:
        print("[!] Error: No se pudo obtener MapManager.")
        return
        
    print(f"[*] Managers localizados: DM=0x{dm_ptr:X}, MapMgr=0x{map_mgr_ptr:X}")

    # 2. Localizar al Jugador (Mi Castillo)
    # RoleBuildingData get_PlayerCastle() -> RVA 0x327521 (o similar)
    # Intentaremos leer la posición directamente de DM si es posible
    # RolePosX/Y suele estar cerca de RoleInfo
    # Para el test, vamos a leer el 'FocusMapID' del MapManager (donde está mirando el jugador)
    focus_data = bridge.read_memory(map_mgr_ptr + 0x1E8, "<I")
    if not focus_data:
        print("[!] No se pudo leer el FocusMapID.")
        return
        
    focus_map_id = focus_data[0]
    player_x = focus_map_id % 512
    player_y = focus_map_id // 512
    
    print(f"[+] Posición Central detectada (Focus): X={player_x}, Y={player_y}")
    print(f"[*] Buscando Mineral (ResourceType=3) en radio 15m - 30m...")

    # 3. Acceder a LayoutMapInfo (offset 0x68) y ResourcesPointTable (offset 0xB0)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    res_table_ptr = bridge.read_ptr(map_mgr_ptr + 0xB0)
    
    print(f"[*] Punteros de Tablas: Layout=0x{layout_ptr:X}, ResTable=0x{res_table_ptr:X}")

    if not layout_ptr or not res_table_ptr:
        print("[!] Error: Tablas del mapa no inicializadas en memoria.")
        return

    # Ajuste para Arrays de Unity (Header de 0x20 o 0x28 bytes)
    layout_items_ptr = layout_ptr + 0x20
    res_items_ptr = res_table_ptr + 0x20

    # 4. Escaneo Circular (Caja de 60x60 alrededor del jugador)
    found_count = 0
    search_range = 40
    
    for dy in range(-search_range, search_range):
        for dx in range(-search_range, search_range):
            ty = player_y + dy
            tx = player_x + dx
            
            if tx < 0 or tx >= 512 or ty < 0 or ty >= 1024: continue
            
            tid = ty * 512 + tx
            # Estructura MapPoint (4 bytes align): ushort tableID (0x0), byte pointKind (0x2)
            point_data = bridge.read_memory(layout_items_ptr + (tid * 4), "<HB") 
            if not point_data: continue
            
            table_id, kind = point_data
            
            if kind == 2: # 2 = Resource
                dist = abs(dx) + abs(dy) # Manhattan distance
                if 2 <= dist <= 35: 
                    # El tableID es el índice en res_table_ptr
                    # level está en offset 0x12
                    res_base = res_items_ptr + (table_id * 48) # Ajustado a padding IL2CPP
                    level_data = bridge.read_memory(res_base + 0x12, "B")
                    level = level_data[0] if level_data else 0
                    # Por ahora listaremos las de nivel interesante
                    print(f"  [Mina Detectada] ID:{tid} | Coords:({tx},{ty}) | Dist:{dist}m | LV:{level} | TblID:{table_id}")
                    found_count += 1
                    
            if found_count >= 15: break
        if found_count >= 10: break

    print("\n" + "-"*40)
    if found_count == 0:
        print(" [?] No se detectaron minas en el radio inmediato.")
        print(" SUGERENCIA: Mueve la cámara hacia un grupo de minas en el juego.")
    else:
        print(f" ✅ Escaneo completo. {found_count} minas detectadas en la RAM.")
    print("-"*40)

if __name__ == "__main__":
    scan_nearby_resources()
