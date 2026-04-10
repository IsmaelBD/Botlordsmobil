import pymem
import pymem.process
import struct

def extract_final_crypto():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        
        # Base de campos estáticos calculada (Real Static Fields)
        sf_base = 0x1fe9c264c60
        
        # 1. SessionKey (Offset 0x08)
        sk_ptr = pm.read_longlong(sf_base + 0x08)
        if sk_ptr:
            size = pm.read_int(sk_ptr + 0x18)
            data = pm.read_bytes(sk_ptr + 0x20, size)
            print(f"[+] Key (SessionKey): {data.hex()}")
            
        # 2. Veronica / IV (Offset 0xF0)
        # Según el dump anterior, en 0xF0 hay un puntero plausible
        iv_ptr = pm.read_longlong(sf_base + 0xF0)
        if iv_ptr:
            size = pm.read_int(iv_ptr + 0x18)
            data = pm.read_bytes(iv_ptr + 0x20, size)
            print(f"[+] IV (Veronica): {data.hex()}")
            
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    extract_final_crypto()
