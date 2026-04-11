"""
PACKET CAPTURE v2 - Escáner de Buffer de Red
Busca la firma del Protocolo 2415 y 6615 en los buffers de red del juego
para recuperar la estructura exacta enviada.
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def read_remote(h, a, s):
    b = ctypes.create_string_buffer(s)
    kernel32.ReadProcessMemory(h, ctypes.c_void_p(a), b, s, None)
    return b.raw

def hex_dump(data, max_len=64):
    res = []
    for i in range(0, min(len(data), max_len), 16):
        chunk = data[i:i+16]
        hex_str = " ".join(f"{b:02X}" for b in chunk)
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        res.append(f"    {i:04X}: {hex_str:<48} {ascii_str}")
    return "\n".join(res)

def main():
    print("="*60)
    print("  CAPTURA v2 - Búsqueda de firma en buffers")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    nm_instance = bridge.call_rva(0x1D2CD40)
    if not nm_instance:
        print("[!] No se encontró NetworkManager")
        return
        
    nm_klass = bridge.read_ptr(nm_instance)
    
    # SendData estático está en klass+0xB8
    sf_ptr = bridge.read_ptr(nm_klass + 0xB8)
    if not sf_ptr:
        return
        
    send_data_ptr = bridge.read_ptr(sf_ptr + 0xA8)
    if not send_data_ptr:
        return
        
    sd_len = bridge.read_memory(send_data_ptr + 0x18, "<I")[0]
    print(f"[+] SendData[] buffer length: {sd_len}")
    
    # Leer TODO el buffer (max 4096 bytes)
    read_size = min(sd_len, 4096)
    buffer = read_remote(bridge.handle, send_data_ptr + 0x20, read_size)
    
    print("\n[*] Buscando firmas de Marcha (2415 / 6615)...")
    
    # Patrones para buscar (little endian)
    patterns = {
        "Proto 2415": b"\x6F\x09",
        "Proto 6615": b"\xD7\x19"
    }
    
    found = False
    for p_name, p_bytes in patterns.items():
        idx = 0
        while True:
            idx = buffer.find(p_bytes, idx)
            if idx == -1: break
            
            found = True
            print(f"\n  [🎯 ENCONTRADO: {p_name} en offset 0x{idx:X}]")
            
            # Extraer el paquete (desde 4 bytes antes, que suele ser la longitud/header)
            # Imprimir hasta 48 bytes después
            start = max(0, idx - 4)
            data_slice = buffer[start:idx+48]
            print(hex_dump(data_slice, 64))
            
            # Intentar decodificar los campos asumiendo el formato estándar
            if idx + 4 <= len(buffer):
                try:
                    # Formato a decodificar usando los offsets más comunes
                    zone = struct.unpack_from("<H", buffer, idx+2)[0]
                    point = struct.unpack_from("B", buffer, idx+4)[0]
                    hero_count = struct.unpack_from("B", buffer, idx+5)[0]
                    print(f"    Posible decodificación:")
                    print(f"      ZoneID: {zone}")
                    print(f"      PointID: {point}")
                    print(f"      HeroCount: {hero_count}")
                    
                    if hero_count <= 5 and idx + 6 + (hero_count*2) < len(buffer):
                        heroes = []
                        for h in range(hero_count):
                            heroes.append(struct.unpack_from("<H", buffer, idx+6+(h*2))[0])
                        print(f"      Héroes: {heroes}")
                        
                        tc_offset = idx + 6 + (hero_count*2)
                        tier_count = struct.unpack_from("B", buffer, tc_offset)[0]
                        print(f"      TierCount: {tier_count}")
                except Exception as e:
                    print(f"    Error decodificando: {e}")
                    
            idx += 1
            
    if not found:
        print("  [-] No se encontraron rastros recientes de marchas en el buffer.")
        print("      Puede que se hayan sobrescrito o que el patrón sea diferente.")

if __name__ == "__main__":
    main()
