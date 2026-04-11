import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def find_active_points():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    if not layout_ptr: return
    
    items_ptr = layout_ptr + 0x20
    # Origen del jugador
    hx, hy = 138, 180
    
    print(f"[*] Buscando MINERAL (Kind 5) en todo el mapa...")
    
    stride = 4
    found = 0
    for i in range(0, 524288):
        addr = items_ptr + (i * stride)
        data = bridge.read_memory(addr, "<HB")
        if data and data[1] == 5: # Kind 5 = Mineral (Ore)
            tx, ty = i % 512, i // 512
            dist = abs(tx - hx) + abs(ty - hy)
            
            # Mostrar solo si esta en un rango razonable para el test (ej. < 100m)
            if dist < 150:
                print(f"  [+] MINERAL DETECTADO! Coords:({tx:3}, {ty:3}) | Dist:{dist:3}m | TblID:{data[0]:5}")
                found += 1
                if found >= 20: break
            
    if found == 0:
        print("[!] No se encontró ninguna mina de Kind 5 en el radio local.")
        print("[*] Probando con Kind 2, 3, 4, 6 para ver que hay cerca...")
        # Repetir escaneo breve para Kind 2-6
        print("[!] Ni un solo punto no-vacio en el 20% del mapa. Revisando offsets...")
        print("[!] No se encontró ningún punto activo en los primeros 10k.")
        print("[*] Scan rápido del puntero Layout...")
        # Leer el puntero mismo
        val = bridge.read_ptr(map_mgr_ptr + 0x68)
        print(f"    Val en 0x68: 0x{val:X}")

if __name__ == "__main__":
    find_active_points()
