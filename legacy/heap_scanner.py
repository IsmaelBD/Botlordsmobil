"""
PACKET HEAP SCANNER
Escanea toda la memoria del juego en busca de instancias de MessagePacket
y busca los que tienen Protocolo 2415 o 6615 retenidos en la memoria,
revelando la estructura del paquete exacto.
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def read_remote(h, a, s):
    b = ctypes.create_string_buffer(s)
    kernel32.ReadProcessMemory(h, ctypes.c_void_p(a), b, s, None)
    return b.raw

def main():
    print("="*60)
    print("  HEAP SCANNER - Rescatando el paquete perfecto")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    # 1. Obtener MP Klass
    guest = bridge.call_rva(0x1D22900)
    klass = bridge.read_ptr(guest)
    print(f"[+] MessagePacket Klass: 0x{klass:X}")
    
    klass_bytes = struct.pack("<Q", klass)
    
    # 2. Escanear memoria por el Klass pointer
    class MEMORY_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BaseAddress", ctypes.c_void_p),
            ("AllocationBase", ctypes.c_void_p),
            ("AllocationProtect", ctypes.c_uint32),
            ("RegionSize", ctypes.c_size_t),
            ("State", ctypes.c_uint32),
            ("Protect", ctypes.c_uint32),
            ("Type", ctypes.c_uint32),
        ]
    
    MEM_COMMIT = 0x1000
    PAGE_READWRITE = 0x04
    PAGE_EXECUTE_READWRITE = 0x40
    
    print("[*] Escaneando la heap del proceso (esto tomará ~5-15 segs)...")
    
    address = 0
    mbi = MEMORY_BASIC_INFORMATION()
    
    instances = []
    while kernel32.VirtualQueryEx(bridge.handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        # Si es un segmento de heap (ReadWrite y Commit)
        if mbi.State == MEM_COMMIT and (mbi.Protect == PAGE_READWRITE or mbi.Protect == PAGE_EXECUTE_READWRITE):
            try:
                buffer = read_remote(bridge.handle, mbi.BaseAddress, mbi.RegionSize)
                idx = 0
                while True:
                    idx = buffer.find(klass_bytes, idx)
                    if idx == -1: break
                    if idx % 8 == 0:  # Debe estar alineado a 8 bytes en x64
                        instances.append(mbi.BaseAddress + idx)
                    idx += 8
            except Exception:
                pass
        
        address += mbi.RegionSize
        if address > 0x7FFFFFFFFFFF: # Limite x64 usermode approx
            break
            
    print(f"[+] ¡Se encontraron {len(instances)} instancias de MessagePacket!")
    
    # Inspeccionar las instancias en busca de protocolos clave
    target_protos = {2415: "TROOPMARCH (Attack/Gather)", 6615: "TROOPMARCH_NOTATK"}
    found_packets = []
    
    for inst in instances:
        try:
            proto = bridge.read_memory(inst + 0x30, "<H")
            if not proto: continue
            
            p = proto[0]
            if p in target_protos:
                length = bridge.read_memory(inst + 0x18, "<I")[0]
                data_buf = bridge.read_ptr(inst + 0x28)
                
                # Leer bytes reales si los hay
                data_bytes = b""
                if data_buf and length > 0:
                    data_bytes = read_remote(bridge.handle, data_buf + 0x20, length)
                
                found_packets.append({
                    "addr": inst,
                    "proto": p,
                    "len": length,
                    "data": data_bytes,
                    "desc": target_protos[p]
                })
        except:
            pass
            
    print(f"\n[+] Paquetes rescatados: {len(found_packets)}")
    
    for idx, pk in enumerate(found_packets):
        print(f"\n--- PAQUETE {idx+1} (Protocol: {pk['proto']}, Len: {pk['len']}) ---")
        d = pk['data']
        hex_data = " ".join(f"{b:02X}" for b in d)
        print(f"RAW: {hex_data}")
        
        # Intentar decodificar
        pos = 0
        l = len(d)
        print("\nDecodificando asumiendo cabecera PointCode:")
        if l >= 2: print(f"  ZoneID: {struct.unpack_from('<H', d, pos)[0]}"); pos += 2
        if l >= pos+1: print(f"  PointID: {struct.unpack_from('B', d, pos)[0]}"); pos += 1
        if l >= pos+1:
            hc = struct.unpack_from("B", d, pos)[0]
            print(f"  HeroCount: {hc}"); pos += 1
            for _ in range(hc):
                if l >= pos+2:
                    print(f"    HeroID: {struct.unpack_from('<H', d, pos)[0]}")
                    pos += 2
        
        print(f"Resto ({l - pos} bytes) que podrían contener tropas/pet/PointKind/Level:")
        print(" ".join(f"{b:02X}" for b in d[pos:]))
        
        print("\nPara copiar/analizar los uints:")
        rest = d[pos:]
        uints = []
        for i in range(0, len(rest)-3, 4):
            uints.append(struct.unpack_from("<I", rest, i)[0])
        print(f"Como ints: {uints}")

if __name__ == "__main__":
    main()
