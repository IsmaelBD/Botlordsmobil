"""
INYECTOR v10 - DINÁMICO Y FINAL (Protocolo 6615)
Resuelve la desconexión calculando la ZoneID y PointID nativamente
para las coordenadas X, Y deseadas (375, 499 en K1977).
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
    print("  INYECTOR v10 - Operación Dinámica Bosque Lv.3")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    # RVAs
    fn_get_mp = base + 0x1D22900
    fn_ab = base + 0x1D22860 # Add(byte)
    fn_ah = base + 0x1D224A0 # Add(ushort)
    fn_au = base + 0x1D22430 # Add(uint)
    fn_nm_send = base + 0x1D28C40
    
    # RVAs de Mapeo
    fn_get_map_mgr = base + 0x2915080
    fn_mapid_to_pc = base + 0x1E82480
    
    # Coordenadas del usuario
    K = 1977
    X = 375
    Y = 499
    
    # MapID = Kingdom * 256*1024 + Y * 1024 + X? 
    # Usaremos el cálculo estándar del juego si lo encontramos, o 
    # simplemente calculamos el MapID local para el reino actual.
    # En Lords Mobile PC, el MapID absoluto suele ser: (Reino << 20) | (Y << 10) | X
    mapID = (K << 20) | (Y << 10) | X
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    res_buf = rmem + 2048
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54\x41\x55"
    sc += b"\x49\xBD" + struct.pack("<Q", res_buf) # r13 = result_buf
    
    # 1. Obtener Instancia de MapManager
    sc = emit_call(sc, fn_get_map_mgr)
    sc += b"\x49\x89\xC6" # r14 = MapManager Instance
    
    # 2. Llamar MapIDToPointCode(mapID)
    sc += b"\x4C\x89\xF1" # rcx = MapManager
    sc += b"\xBA" + struct.pack("<I", mapID) # rdx = mapID
    sc = emit_call(sc, fn_mapid_to_pc)
    # rax contiene el PointCode (3 bytes: zoneID low, zoneID high, pointID)
    sc += b"\x49\x89\x45\x00" # Guardar PointCode en result_buf
    
    # 3. GetGuestMessagePack
    sc = emit_call(sc, fn_get_mp)
    sc += b"\x49\x89\xC4" # r12 = MessagePacket
    
    # 4. Protocol = 6615
    sc += b"\x66\x41\xC7\x44\x24\x30\xD7\x19"
    
    # --- 32 LLAMADAS PASO POR PASO ---
    
    # Hero 9 + 4 Vacíos
    hids = [9, 0, 0, 0, 0]
    for h in hids:
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA" + struct.pack("<H", h)
        sc = emit_call(sc, fn_ah)
        
    # Tropas 1 T1 + 15 Vacíos
    for i in range(16):
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA" + struct.pack("<I", 1 if i==0 else 0)
        sc = emit_call(sc, fn_au)
        
    # Coordenadas DINÁMICAS (Lote 22 y 23)
    # Recuperar del result_buf
    sc += b"\x41\x0F\xB7\x45\x00" # rax = zoneID (ushort)
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\x89\xC2" # rdx = zoneID
    sc = emit_call(sc, fn_ah)
    
    sc += b"\x41\x0F\xB6\x45\x02" # rax = pointID (byte)
    sc += b"\x4C\x89\xE1"
    sc += b"\x89\xC2" # rdx = pointID
    sc = emit_call(sc, fn_ab)
    
    # Mascotas (5 vacías)
    for _ in range(5):
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA\x00\x00"
        sc = emit_call(sc, fn_ah)
        
    # T5 (4 vacías)
    for _ in range(4):
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA\x00\x00\x00\x00"
        sc = emit_call(sc, fn_au)
        
    # 5. Send(force=true)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x01"
    sc = emit_call(sc, fn_nm_send)
    
    sc += b"\x41\x5D\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    print(f"[*] Lanzando Inyector Dinámico v10 para K:{K} X:{X} Y:{Y}...")
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 10000)
    
    # Leer resultados de depuración
    r = ctypes.create_string_buffer(16)
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(res_buf), r, 8, None)
    pc_low, pc_high, point = struct.unpack_from("<HBB", r.raw, 0)
    zone = pc_low
    print(f"[+] Coordenadas calculadas por el juego: ZoneID={zone}, PointID={point}")
    
    kernel32.CloseHandle(t)
    print("[+] Proceso finalizado.")

if __name__ == "__main__":
    main()
