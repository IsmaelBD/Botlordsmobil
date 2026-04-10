import pymem
import struct

def find_account_id():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        # Tu IGGID: 2129137494 -> Hex: 0x7EE98756 -> Little Endian: 56 87 e9 7e 00 00 00 00
        id_bytes = b"\x56\x87\xe9\x7e\x00\x00\x00\x00"
        print("[*] Buscando IGGID en la memoria profunda...")
        
        found = False
        # Escaneo optimizado sobre regiones comunes de objetos
        addr = 0x16000000000
        while addr < 0x40000000000:
            try:
                data = pm.read_bytes(addr, 0x1000000)
                idx = data.find(id_bytes)
                if idx != -1:
                    actual_addr = addr + idx
                    print(f"[+] IGGID LOCALIZADO EN: {hex(actual_addr)}")
                    # Volcamos 512 bytes alrededor para encontrar la SessionKey
                    dump = pm.read_bytes(actual_addr - 128, 512)
                    print(f"SESSION_DUMP:{dump.hex()}")
                    found = True
                    break
                addr += 0x1000000
            except:
                addr += 0x1000000
                
        if not found:
            print("[!] No se encontró el rastro del IGGID. Asegúrate de estar dentro del juego.")
            
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    find_account_id()
