import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def map_explorer():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    
    # Lectura del Focus para saber donde estamos
    focus_data = bridge.read_memory(map_mgr_ptr + 0x1E8, "<I")
    f_id = focus_data[0]
    fx, fy = f_id % 512, f_id // 512
    
    print(f"[*] Escaneando recursos cerca de Focus: ({fx}, {fy}) | Layout: 0x{layout_ptr:X}")
    
    items_ptr = layout_ptr + 0x20
    # Escanear 200x200
    stride = 4
    for dy in range(-20, 20):
        for dx in range(-20, 20):
            tx, ty = fx + dx, fy + dy
            if tx < 0 or tx >= 512 or ty < 0 or ty >= 1024: continue
            tid = ty * 512 + tx
            data = bridge.read_memory(items_ptr + (tid * stride), "<HB")
            if data and data[1] != 0:
                print(f"  [Tile] ({tx:3}, {ty:3}) | Kind:{data[1]:2} | TblID:{data[0]:5}")

if __name__ == "__main__":
    map_explorer()
