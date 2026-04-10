"""
INYECTOR v11 - CÁLCULO MATEMÁTICO (Protocolo 6615)
Usando la fórmula confirmada:
ZoneID = (X//16) + (Y//16)*32 = 1015
PointID = (X%16) + (Y%16)*16 = 55
Incluye AddSeqId para evitar la desconexión por asincronía.
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def emit_call(sc, addr):
    sc += b"\x48\xB8" + struct.pack("<Q", addr)
    sc += b"\xFF\xD0"
    return sc

def build_and_send(bridge, base):
    fn = {
        "get_mp":  base + 0x1D22900,
        "add_seq": base + 0x1D22110,
        "ab":      base + 0x1D22860, # Add(byte)
        "ah":      base + 0x1D224A0, # Add(ushort)
        "au":      base + 0x1D22430, # Add(uint)
        "nm_send": base + 0x1D28C40,
    }
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54\x41\x55"
    
    # 1. GetGuestMessagePack
    sc = emit_call(sc, fn["get_mp"])
    sc += b"\x49\x89\xC4" # r12 = MessagePacket
    
    # 2. Protocol = 6615
    sc += b"\x66\x41\xC7\x44\x24\x30\xD7\x19"
    
    # 3. AddSeqId (CRÍTICO: Evita desconexión)
    sc += b"\x4C\x89\xE1"
    sc = emit_call(sc, fn["add_seq"])
    
    # --- ESTRUCTURA DE 32 PASOS (CAPTURADA POR FRIDA) ---
    
    # Héroes (5 slots) -> ID 9 + 4 vacíos
    hids = [9, 0, 0, 0, 0]
    for h in hids:
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA" + struct.pack("<H", h)
        sc = emit_call(sc, fn["ah"])
        
    # Tropas T1-T4 (16 slots) -> 1 T1 + 15 vacíos
    for i in range(16):
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA" + struct.pack("<I", 1 if i==0 else 0)
        sc = emit_call(sc, fn["au"])
        
    # Coordenadas (Zone: 1015, Point: 55 para X:375 Y:499)
    # ZoneID (ushort)
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", 1015)
    sc = emit_call(sc, fn["ah"])
    
    # PointID (byte)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", 55)
    sc = emit_call(sc, fn["ab"])
    
    # Mascotas (5 slots vacíos)
    for _ in range(5):
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA\x00\x00"
        sc = emit_call(sc, fn["ah"])
        
    # Tropas T5 (4 slots vacíos)
    for _ in range(4):
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA\x00\x00\x00\x00"
        sc = emit_call(sc, fn["au"])
        
    # 4. Enviar
    sc += b"\x4C\x89\xE1" 
    sc += b"\xB2\x01" # force = true
    sc = emit_call(sc, fn["nm_send"])
    
    sc += b"\x41\x5D\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    print(f"[*] Lanzando Inyector v11 (X:375 Y:499 -> Zone:1015 Point:55)...")
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 5000)
    kernel32.CloseHandle(t)
    return True

def main():
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    
    if build_and_send(bridge, bridge.base):
        print("[+] Paquete v11 enviado. Cruza los dedos.")

if __name__ == "__main__":
    main()
