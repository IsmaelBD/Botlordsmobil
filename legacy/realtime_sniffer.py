"""
SNIFFER EN TIEMPO REAL
Monitorea continuamente el buffer de NetworkManager para capturar el instante
exacto en que se envía el paquete de marcha (2415 o 6615) y vuelca sus bytes.
"""
import ctypes, struct, time, sys
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def read_remote(h, a, s):
    b = ctypes.create_string_buffer(s)
    kernel32.ReadProcessMemory(h, ctypes.c_void_p(a), b, s, None)
    return b.raw

def hex_dump(data, max_len=256):
    res = []
    for i in range(0, min(len(data), max_len), 16):
        chunk = data[i:i+16]
        hex_str = " ".join(f"{b:02X}" for b in chunk)
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        res.append(f"    {i:04X}: {hex_str:<48} {ascii_str}")
    return "\n".join(res)

def main():
    print("="*60)
    print("  SNIFFER EN TIEMPO REAL - Esperando Marcha...")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    nm_instance = bridge.call_rva(0x1D2CD40)
    nm_klass = bridge.read_ptr(nm_instance)
    
    sf_ptr = bridge.read_ptr(nm_klass + 0xB8)
    send_data_ptr = bridge.read_ptr(sf_ptr + 0xA8)
    sd_len = bridge.read_memory(send_data_ptr + 0x18, "<I")[0]
    
    print(f"[*] Escaneando buffer de red (Len={sd_len})...")
    print(f"[*] ENVÍA TU MARCHA AHORA. El script detectará el paquete.")
    
    last_write_pos = 0
    buffer_ptr = send_data_ptr + 0x20
    
    start_time = time.time()
    found = False
    
    # Escanear continuamente durante 60 segundos
    while time.time() - start_time < 60:
        wp_raw = bridge.read_memory(sf_ptr + 0xB8, "<I")
        wp = wp_raw[0] if wp_raw else 0
        
        # Si la posición de escritura avanzó, nuevos datos fueron enviados
        if wp > last_write_pos:
            chunk_size = wp - last_write_pos
            if chunk_size > 4: # Ignorar keep-alives diminutos
                new_data = read_remote(bridge.handle, buffer_ptr + last_write_pos, chunk_size)
                
                # Buscar protocolo de marcha (0x096F = 2415, 0x19D7 = 6615)
                # Formato MP: [Len(int)][Seq(int)?][Protocol(ushort)]...
                # Vamos a buscar en todo el chunk nuevo
                
                is_march = False
                if b"\x6F\x09" in new_data or b"\xD7\x19" in new_data:
                    is_march = True
                    found = True
                    print(f"\n[🚀] ¡PAQUETE DE MARCHA DETECTADO! (Pos: {last_write_pos} -> {wp}, {chunk_size} bytes)")
                    print(hex_dump(new_data, chunk_size))
                    
                    # Decodificación de campos
                    if chunk_size >= 14:
                        print("    --- Decodificación Estructural ---")
                        try:
                            # En un Array<byte> raw, los datos pueden tener un offset
                            idx = 0
                            if b"\x6F\x09" in new_data:
                                idx = new_data.find(b"\x6F\x09")
                            elif b"\xD7\x19" in new_data:
                                idx = new_data.find(b"\xD7\x19")
                            
                            proto = struct.unpack_from("<H", new_data, idx)[0]
                            print(f"    Protocol: {proto}")
                            
                            if idx + 2 < len(new_data):
                                print("    Campos siguientes:")
                                fields = struct.unpack_from(f"<{chunk_size - (idx+2)}B", new_data, idx+2)
                                print(f"    Raw bytes: {list(fields)}")
                        except Exception as e:
                            print(f"Error decodificando: {e}")
                    
                    break
            last_write_pos = wp
            
        elif wp < last_write_pos:
            # Buffer reseteado
            last_write_pos = wp
            
        time.sleep(0.01) # 10ms
        
    if not found:
        print("\n[-] Tiempo de espera agotado o no se detectó el paquete.")

if __name__ == "__main__":
    main()
