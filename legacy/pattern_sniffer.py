import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def sniff_pattern():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    if not layout_ptr: return
    
    # Empezamos cerca del centro (index 126k)
    items_ptr = layout_ptr + 0x20
    start_addr = items_ptr + (126000 * 4)
    
    print(f"[*] Sniffing 2048 bytes at 0x{start_addr:X}...")
    data = bridge.read_memory(start_addr, "2048B")
    
    # Buscar patrones repetitivos
    # MapPoint es [ushort tableID][byte pointKind]
    # Si stride es 4: [T1][T2][K][P] [T1][T2][K][P]
    
    found_any = False
    for i in range(0, 2048, 4):
        block = data[i:i+4]
        if any(b != 0 for b in block):
            print(f"  + Offset {i:4} | Hex: {' '.join([f'{b:02X}' for b in block])}")
            found_any = True
            
    if not found_any:
        print("[!] No se detectó ningún byte activo en este bloque de 2KB.")

if __name__ == "__main__":
    sniff_pattern()
