"""
INYECTOR v9 - EL DEFINITIVO (Protocolo 6615)
Basado en el rastro exacto capturado por Frida: 32 llamadas Add.
Estructura: 5 Heroes -> 16 Tropas T1-T4 -> Zone/Point -> 5 Pets -> 4 Tropas T5.
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
        "ab":      base + 0x1D22860, # Add(byte)
        "ah":      base + 0x1D224A0, # Add(ushort)
        "au":      base + 0x1D22430, # Add(uint)
        "nm_send": base + 0x1D28C40,
    }
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    # result_buf en rmem + 2048
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54\x41\x55"
    
    # 1. GetGuestMessagePack
    sc = emit_call(sc, fn["get_mp"])
    sc += b"\x49\x89\xC4" # r12 = MessagePacket
    
    # 2. Protocol = 6615
    sc += b"\x66\x41\xC7\x44\x24\x30" + struct.pack("<H", 6615)
    
    # --- PAYLOAD DE 32 PASOS ---
    
    # Pass 1-5: Heroes (5 x ushort)
    # Seleccionamos HeroID 9, el resto 0
    ids = [9, 0, 0, 0, 0]
    for hid in ids:
        sc += b"\x4C\x89\xE1" # rcx = mp
        sc += b"\x66\xBA" + struct.pack("<H", hid) # rdx = val
        sc = emit_call(sc, fn["ah"])
        
    # Pass 6-21: Tropas T1-T4 (16 x uint)
    # Enviamos 1 tropa en el primer slot, resto 0
    troops = [0] * 16
    troops[0] = 1
    for tcount in troops:
        sc += b"\x4C\x89\xE1" 
        sc += b"\xBA" + struct.pack("<I", tcount)
        sc = emit_call(sc, fn["au"])
        
    # Pass 22: ZoneID (ushort)
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", 507)
    sc = emit_call(sc, fn["ah"])
    
    # Pass 23: PointID (byte)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", 59)
    sc = emit_call(sc, fn["ab"])
    
    # Pass 24-28: Pets (5 x ushort)
    for _ in range(5):
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA\x00\x00"
        sc = emit_call(sc, fn["ah"])
        
    # Pass 29-32: Tropas T5 (4 x uint)
    for _ in range(4):
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA\x00\x00\x00\x00"
        sc = emit_call(sc, fn["au"])
        
    # --- FINALIZAR Y ENVIAR ---
    
    # NetworkManager.Send(mp, force=true)
    sc += b"\x4C\x89\xE1" # rcx = mp
    sc += b"\xB2\x01"      # rdx = true (byte)
    sc = emit_call(sc, fn["nm_send"])
    
    sc += b"\x41\x5D\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    print(f"[*] Ejecutando v9 en el proceso {bridge.pid}...")
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 10000)
    kernel32.CloseHandle(t)
    return True

def main():
    print("="*60)
    print("  INYECTOR v9 - Protocolo 6615 (Exacto)")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    
    if build_and_send(bridge, bridge.base):
        print("[+] Operación completada. Revisa el juego.")

if __name__ == "__main__":
    main()
