"""
DUMP INSTRUCTIONS
Lee los primeros bytes de NetworkManager.Send(MessagePacket)
para preparar el hook.
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def read_remote(h, a, s):
    b = ctypes.create_string_buffer(s)
    kernel32.ReadProcessMemory(h, ctypes.c_void_p(a), b, s, None)
    return b.raw

def hex_dump(data):
    return " ".join(f"{b:02X}" for b in data)

def main():
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    nm_send = base + 0x1D28C40
    print(f"NetworkManager.Send RVA: 0x{nm_send:X}")
    
    bytes_start = read_remote(bridge.handle, nm_send, 32)
    print("Primeros 32 bytes:")
    print(hex_dump(bytes_start))

if __name__ == "__main__":
    main()
