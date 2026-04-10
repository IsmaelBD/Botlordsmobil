"""
INYECTOR v12 - CALIBRACIÓN FINAL (Protocolo 6615)
Usando los IDs reales obtenidos de la calibración del Castillo (v12).
Castillo (370, 492) -> Zone: 24576, Point: 192
Mina (375, 499) -> Zone: 24608, Point: 53
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def emit_call(sc, addr):
    sc += b"\x48\xB8" + struct.pack("<Q", addr)
    sc += b"\xFF\xD0"
    return sc

def main():
    print("="*60)
    print("  INYECTOR v12 - Operación Bosque Lv.3 K1977")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    # RVAs confirmados
    fn_get_mp  = base + 0x1D22900
    fn_add_seq = base + 0x1D22110
    fn_ab      = base + 0x1D22860 # Add(byte)
    fn_ah      = base + 0x1D224A0 # Add(ushort)
    fn_au      = base + 0x1D22430 # Add(uint)
    fn_nm_send = base + 0x1D28C40
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54\x41\x55"
    
    # 1. GetGuestMessagePack
    sc = emit_call(sc, fn_get_mp)
    sc += b"\x49\x89\xC4" # r12 = MessagePacket
    
    # 2. Protocol = 6615
    sc += b"\x66\x41\xC7\x44\x24\x30\xD7\x19"
    
    # 3. AddSeqId
    sc += b"\x4C\x89\xE1"
    sc = emit_call(sc, fn_add_seq)
    
    # --- PAYLOAD DE 32 PASOS (FRIDA LOG) ---
    # Heroes (5 x ushort) -> ID 9 + 4 vacíos
    hids = [9, 0, 0, 0, 0]
    for h in hids:
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA" + struct.pack("<H", h)
        sc = emit_call(sc, fn_ah)
        
    # Tropas T1-T4 (16 x uint) -> 1 T1 + 15 vacíos
    for i in range(16):
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA" + struct.pack("<I", 1 if i==0 else 0)
        sc = emit_call(sc, fn_au)
        
    # Coordenadas CALIBRADAS (Zone: 24608, Point: 53)
    # ZoneID (ushort)
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", 24608)
    sc = emit_call(sc, fn_ah)
    
    # PointID (byte)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", 53)
    sc = emit_call(sc, fn_ab)
    
    # Mascotas (5 x ushort vacíos)
    for _ in range(5):
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA\x00\x00"
        sc = emit_call(sc, fn_ah)
        
    # Tropas T5 (4 x uint vacíos)
    for _ in range(4):
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA\x00\x00\x00\x00"
        sc = emit_call(sc, fn_au)
        
    # 4. Enviar
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x01" # force = true
    sc = emit_call(sc, fn_nm_send)
    
    sc += b"\x41\x5D\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    print(f"[*] Lanzando Inyector v12 (Calibrado K1977)...")
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 5000)
    kernel32.CloseHandle(t)
    print(f"[+] Inyección v12 completada.")

if __name__ == "__main__":
    main()
