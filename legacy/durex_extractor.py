import pymem
import struct
import time

def extract_durex_table():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
        base = module.lpBaseOfDll
        
        print("[*] ANALIZADOR DUREX ACTIVO. Buscando tabla de cifrado...")
        
        # El NetworkManager.Cipher usa una tabla estática
        # Vamos a buscar el puntero a la tabla de semillas (seeds)
        # Segun patrones comunes de IGG, suele estar cerca de la instancia de NetworkManager
        addr = base + 0x1D2CD40 # NetworkManager.get_Instance
        disp = struct.unpack("<i", pm.read_bytes(addr + 3, 4))[0]
        klass_ptr = pm.read_longlong(addr + 7 + disp)
        sf_base = pm.read_longlong(klass_ptr + 0xB8)
        
        # En la instancia, buscamos el campo 'Durex' (índice) y la tabla de semillas
        durex_index = pm.read_int(sf_base + 0x1C) # Sequence/Durex
        print(f"[+] Índice Durex actual: {durex_index}")
        
        # Intentamos localizar la tabla de 256 bytes (XOR Key)
        # Suele ser un campo estático en la clase NetworkManager
        # Vamos a escanear un rango de la clase en busca de un array de 256 bytes
        print("[*] Escaneando tabla de semillas en memoria...")
        for i in range(0, 0x200, 8):
            ptr = pm.read_longlong(sf_base + i)
            if ptr > 0x10000:
                try:
                    potential_table = pm.read_bytes(ptr + 0x20, 16)
                    # Si los bytes parecen una tabla de cifrado (aleatorios pero consistentes)
                    if potential_table:
                        print(f"[!!!] POSIBLE TABLA ENCONTRADA EN OFFSET {hex(i)}!")
                        print(f"  > HEX: {potential_table.hex()}")
                except: pass

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    extract_durex_table()
