import pymem
import re
import struct

def universal_scan():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        # Usamos la base que confirmamos antes
        sf_base = 0x27a3ba04c60 
        print(f"[*] Escaneando motor de red en {hex(sf_base)}...")
        
        candidates = set()
        # Escaneamos los primeros 512 bytes del motor de red como punteros
        for i in range(0, 512, 8):
            try:
                ptr = pm.read_longlong(sf_base + i)
                if ptr > 0x10000: # Dirección válida
                    # Leemos un bloque de datos del puntero
                    data = pm.read_bytes(ptr, 512)
                    # Buscamos patrones hexadecimales de 32 chars
                    matches = re.findall(b"[a-f0-9]{32}", data)
                    for m in matches:
                        candidates.add(m.decode())
            except:
                continue
                
        if not candidates:
            # Si no hay suerte, escaneamos las regiones cercanas
            print("[*] No se halló en punteros directos. Escaneando bloque de proximidad...")
            data = pm.read_bytes(sf_base - 0x5000, 0x10000)
            matches = re.findall(b"[a-f0-9]{32}", data)
            for m in matches:
                candidates.add(m.decode())

        if candidates:
            print(f"[+] SE HAN ENCONTRADO {len(candidates)} LLAVES:")
            for c in candidates:
                print(f"  > {c}")
        else:
            print("[!] No se encontró ninguna llave. ¿Estás seguro de que la sesión está activa?")
            
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    universal_scan()
