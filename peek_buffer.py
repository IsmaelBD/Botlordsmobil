import pymem
import pymem.process
import struct
import time

def sniff_output_buffer():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        # Dirección base del motor de red que confirmamos antes
        sf_base = 0x27a3ba04c60
        
        print(f"[*] Sensor activado en {hex(sf_base)}. Buscando ráfagas de red...")
        
        last_data = b""
        start_time = time.time()
        
        # Escaneamos por 30 segundos buscando cambios en el buffer de salida
        while time.time() - start_time < 30:
            try:
                # SendData suele estar en offset 0xA8
                send_data_ptr = pm.read_longlong(sf_base + 0xA8)
                if send_data_ptr > 0xFFFF:
                    # En IL2CPP byte[] tiene tamaño en +18 y datos reales en +20
                    size = pm.read_int(send_data_ptr + 0x18)
                    if size > 0 and size < 2048:
                        data = pm.read_bytes(send_data_ptr + 0x20, size)
                        if data != last_data and any(b != 0 for b in data):
                            print(f"\n[+] RÁFURGA CAPTURADA (Tamaño: {size})")
                            print(f"[*] Hex: {data.hex()}")
                            last_data = data
                            # Si capturamos algo, mostramos también la secuencia (0x11C)
                            seq = pm.read_int(sf_base + 0x11C)
                            print(f"[*] Secuencia Actual: {seq}")
            except:
                pass
            time.sleep(0.1) # Polling rápido
            
        print("\n[*] Tiempo de espera agotado.")

    except Exception as e:
        print(f"[!] Error de sensor: {e}")

if __name__ == "__main__":
    sniff_output_buffer()
