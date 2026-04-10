import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def discovery_scan():
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    dm_ptr = bridge.call_rva(0x2914F50)
    map_mgr_ptr = bridge.call_rva(0x2915080)
    layout_ptr = bridge.read_ptr(map_mgr_ptr + 0x68)
    
    if not layout_ptr:
        print("[!] Layout pointer is null.")
        return

    items_ptr = layout_ptr + 0x20
    print(f"[*] Escaneando cabecera de LayoutMapInfo en 0x{items_ptr:X}...")
    
    # Leer los primeros 128 bytes
    data = bridge.read_memory(items_ptr, "128B")
    if data:
        # Imprimir en formato hexadecimal para ver el patron
        hex_data = " ".join([f"{b:02X}" for b in data])
        print(f"[HEX] {hex_data}")
        
        # Intentar detectar el patron de 'pointKind'
        # pointKind suele ser 0 (vacio), 1 (jugador), 2 (mina)
        # Si vemos muchos 00 y algun valor, podemos deducir el stride.

if __name__ == "__main__":
    discovery_scan()
