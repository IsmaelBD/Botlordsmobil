import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def decode_resources():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    map_mgr_ptr = bridge.call_rva(0x2915080)
    res_table_ptr = bridge.read_ptr(map_mgr_ptr + 0x70)
    items_ptr = res_table_ptr + 0x20
    
    # IDs de recursos encontrados en el escaneo manual
    test_ids = [46, 72, 54, 117, 79] # Mezcla de Kind 2, 4 y 8
    
    print(f"{'ID':<5} | {'LV':<3} | {'Bytes 0x24-0x2C'}")
    print("-" * 40)
    
    for tid in test_ids:
        addr = items_ptr + (tid * 48)
        # Leer bloque de datos para inspección
        # level @ 0x12
        level = bridge.read_memory(addr + 0x12, "B")[0]
        # bytes significativos al final de la estructura
        extra = bridge.read_memory(addr + 0x24, "8B")
        hex_extra = " ".join([f"{b:02X}" for b in extra])
        
        print(f"{tid:<5} | {level:<3} | {hex_extra}")

if __name__ == "__main__":
    decode_resources()
