"""
TEST - Llamada nativa a PointCode.WriteMP
Esto nos dirá exactamente cuántos y cuáles bytes escribe el juego
para la estructura PointCode en el paquete.
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
    print("  TEST - Native PointCode.WriteMP()")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    fn_get_mp = base + 0x1D22900
    fn_write_mp = base + 0x221DDF0  # PointCode.WriteMP(MessagePacket)
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    result_buf = rmem + 2048
    
    # Escribir el PointCode crudo en memoria (2 bytes zone, 1 byte point, 5 bytes zero)
    # Zone 372 = 0x0174. Point 36 = 0x24.
    point_data = struct.pack("<HB5x", 372, 36)
    kernel32.WriteProcessMemory(bridge.handle, rmem + 3000, point_data, 8, None)
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54\x41\x55"
    sc += b"\x49\xBD" + struct.pack("<Q", result_buf)
    
    # 1. GetGuestMessagePack -> r12
    sc = emit_call(sc, fn_get_mp)
    sc += b"\x49\x89\xC4"  
    sc += b"\x4D\x89\x65\x00"  # Guardar MP 
    
    # 2. Guardar Length original
    sc += b"\x41\x8B\x44\x24\x18"
    sc += b"\x41\x89\x45\x08"
    
    # 3. Llamar a PointCode.WriteMP(rcx = pPoint, rdx = MP)
    sc += b"\x48\x8D\x0D" + struct.pack("<I", 3000 - len(sc) - 7) # rcx = rmem+3000
    sc += b"\x4C\x89\xE2" # rdx = MP
    sc = emit_call(sc, fn_write_mp)
    
    # 4. Guardar Length nuevo
    sc += b"\x41\x8B\x44\x24\x18"
    sc += b"\x41\x89\x45\x10"
    
    sc += b"\x41\x5D\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    # Parchear el cálculo RIP-relativo de rcx
    # El lea es 7 bytes (48 8D 0D xx xx xx xx)
    # La instrucción lea termina en sc[offset]
    # Calculamos bien con absolute addr
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54\x41\x55"
    sc += b"\x49\xBD" + struct.pack("<Q", result_buf)
    
    sc = emit_call(sc, fn_get_mp)
    sc += b"\x49\x89\xC4"  
    sc += b"\x4D\x89\x65\x00"  
    sc += b"\x41\x8B\x44\x24\x18"
    sc += b"\x41\x89\x45\x08"
    
    sc += b"\x48\xB9" + struct.pack("<Q", rmem + 3000) # rcx = abs addr
    sc += b"\x4C\x89\xE2" # rdx = MP
    sc = emit_call(sc, fn_write_mp)
    
    sc += b"\x41\x8B\x44\x24\x18"
    sc += b"\x41\x89\x45\x10"
    
    sc += b"\x41\x5D\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 5000)
    kernel32.CloseHandle(t)
    
    r = ctypes.create_string_buffer(32)
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(result_buf), r, 32, None)
    
    mp_ptr = struct.unpack_from("<Q", r.raw, 0)[0]
    len_pre = struct.unpack_from("<I", r.raw, 8)[0]
    len_post = struct.unpack_from("<I", r.raw, 16)[0]
    
    print(f"[*] MP ptr: 0x{mp_ptr:X}")
    print(f"[*] Length pre:  {len_pre}")
    print(f"[*] Length post: {len_post}")
    print(f"[+] Bytes escritos por WriteMP: {len_post - len_pre}")
    
    if len_post > len_pre:
        # Extraer los bytes
        data_ptr = bridge.read_ptr(mp_ptr + 0x28) + 0x20
        raw_written = read_remote(bridge.handle, data_ptr + len_pre, len_post - len_pre)
        hex_data = " ".join(f"{b:02X}" for b in raw_written)
        print(f"[*] Raw Data: {hex_data}")

if __name__ == "__main__":
    main()
