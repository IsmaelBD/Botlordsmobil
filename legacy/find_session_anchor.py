import pymem
import struct

def find_anchor():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        udid_part = b"eyJha2lkIjoyMDIxMDQy" # Parte inicial de tu UDID
        print("[*] Buscando ancla de sesión en memoria...")
        
        # Escaneo optimizado
        found = False
        # Empezamos en un rango alto donde suelen estar los objetos de sesion
        addr = 0x15000000000
        while addr < 0x40000000000:
            try:
                data = pm.read_bytes(addr, 0x1000000)
                idx = data.find(udid_part)
                if idx != -1:
                    actual_addr = addr + idx
                    print(f"[+] ANCLA DETECTADA: {hex(actual_addr)}")
                    # Extraemos datos cercanos (128 bytes antes, 512 despues)
                    # El bloque suele contener el IGGID y la SessionKey
                    dump = pm.read_bytes(actual_addr - 128, 640)
                    print(f"DUMP_HEX:{dump.hex()}")
                    found = True
                    break
                addr += 0x1000000
            except:
                addr += 0x1000000
                
        if not found:
            print("[!] No se encontró el rastro del UDID. Asegúrate de que el juego está en el castillo.")
            
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    find_anchor()
