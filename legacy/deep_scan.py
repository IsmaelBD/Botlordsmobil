import pymem
import pymem.process
import re

def deep_scan():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        print("[*] Iniciando escaneo profundo de memoria (v2)...")
        
        results = set()
        # Forma correcta de listar regiones en Pymem moderno
        for section in pymem.process.list_memory_regions(pm.process_handle):
            try:
                # Comprobar si la región está confirmada (State 0x1000)
                # y no es una región de sistema protegida
                data = pm.read_bytes(section.BaseAddress, section.RegionSize)
                matches = re.findall(b"[a-f0-9]{32}", data)
                for m in matches:
                    results.add(m.decode())
            except:
                continue
                
        if results:
            print(f"[+] Se han encontrado {len(results)} llaves potenciales:")
            for r in results:
                # Evitamos mostrar llaves genéricas de sistema si las hay
                print(f"  > {r}")
        else:
            print("[!] No se han encontrado llaves hexadecimales de 32 caracteres.")
            
    except Exception as e:
        print(f"[!] Error crítico: {e}")

if __name__ == "__main__":
    deep_scan()
