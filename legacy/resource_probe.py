import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def resource_probe():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    # ResourcesPointTable en 0x70 (segun dump.cs 64895)
    res_table_ptr = bridge.read_ptr(map_mgr_ptr + 0x70)
    
    if not res_table_ptr:
        print("[!] ResourcesPointTable pointer is null at 0x70.")
        return

    items_ptr = res_table_ptr + 0x20
    print(f"[*] Escaneando ResourcesPointTable en 0x{items_ptr:X}...")
    
    # Cada ResourcesPoint es aprox 48 bytes
    for i in range(10):
        addr = items_ptr + (i * 48)
        # Leer level (offset 0x12)
        level_data = bridge.read_memory(addr + 0x12, "B")
        if level_data and level_data[0] > 0:
            print(f"  [+] Registro {i}: LV {level_data[0]}")
        else:
            print(f"  [-] Registro {i}: Vacio o 0")

if __name__ == "__main__":
    resource_probe()
