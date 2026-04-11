import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def find_my_castle():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    items_ptr = layout_ptr + 0x20
    
    print(f"[*] Buscando CASTILLO (Kind 1) en el reino...")
    
    # Escaneamos todo el mapa (512,000 puntos)
    # Stride 4
    for i in range(0, 524288):
        # Leemos en bloques de 1000 para ir mas rapido si es posible, 
        # pero aqui vamos uno a uno para precision
        addr = items_ptr + (i * 4)
        data = bridge.read_memory(addr, "<HB")
        if data and data[1] == 1: # Kind 1 = Player/Castle
            tx, ty = i % 512, i // 512
            print(f"  [FOUND] Castle found at Index:{i} ({tx}, {ty}) | TblID:{data[0]}")
            # Ver mas detalles en DataManager si es necesario
            break
    else:
        print("[!] No se encontró ningun castillo (Kind 1) en el mapa.")

if __name__ == "__main__":
    find_my_castle()
