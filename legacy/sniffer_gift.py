import pymem
import pymem.process
import struct
import time

def sniff_gift_packet():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
        base = module.lpBaseOfDll
        
        # Sincronizar con NetworkManager
        addr = base + 0x1D2CD40
        code = pm.read_bytes(addr, 128)
        idx = code.find(b"\x48\x8b\x0d")
        disp = struct.unpack("<i", code[idx+3:idx+7])[0]
        klass_ptr = addr + idx + 7 + disp
        klass = pm.read_longlong(klass_ptr)
        sf_base = pm.read_longlong(klass + 0xB8)
        if not sf_base: sf_base = pm.read_longlong(klass + 0xB0)
            
        print(f"[*] Radar activado en {hex(sf_base)}. ¡Canjea el código ahora!")
        
        start_time = time.time()
        last_data = b""
        
        # Monitoreamos por 60 segundos
        while time.time() - start_time < 60:
            send_data_ptr = pm.read_longlong(sf_base + 0xA8)
            seq = pm.read_int(sf_base + 0x11C)
            
            if send_data_ptr:
                size = pm.read_int(send_data_ptr + 0x18)
                if size > 0:
                    data = pm.read_bytes(send_data_ptr + 0x20, min(size, 512))
                    if data != last_data:
                        print(f"\n[+] PAQUETE DETECTADO (Secuencia: {seq}, Tamaño: {size})")
                        print(f"[*] Hex: {data.hex()}")
                        last_data = data
            
            time.sleep(0.1)

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    sniff_gift_packet()
