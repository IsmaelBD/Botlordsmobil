import pymem
import pymem.process
import struct
import time
import ctypes

def robust_sniff():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        print("[*] Iniciando sniffer robusto. Esperando actividad de red...")
        
        # Buscamos ráfagas que empiecen por el tamaño del paquete [H] y el OpCode [H]
        # Un paquete de login suele tener un tamaño de ráfaga predecible.
        
        captured_opcodes = set()
        start_time = time.time()
        
        while time.time() - start_time < 60:
            try:
                # Buscamos en las regiones MEM_COMMIT
                for region in pm.list_memory_regions():
                    if region.State == 0x1000 and region.Protect == 0x04:
                        data = pm.read_bytes(region.BaseAddress, region.RegionSize)
                        # Buscamos firmas de paquetes Lords Mobile
                        # Los paquetes siempre empiezan con su tamaño en los primeros 2 bytes
                        # y el opcode en los siguientes 2.
                        for i in range(0, len(data) - 4, 2):
                            size = struct.unpack("<H", data[i:i+2])[0]
                            opcode = struct.unpack("<H", data[i+2:i+4])[0]
                            
                            if size > 10 and size < 1024 and opcode in [1024, 1043, 13000, 1420]:
                                if opcode not in captured_opcodes:
                                    print(f"[CAPTURA] OpCode: {opcode} encontrado en {hex(region.BaseAddress + i)} | Tamaño: {size}")
                                    captured_opcodes.add(opcode)
                                    # Muestreamos el cuerpo
                                    body = data[i+8 : i+size]
                                    print(f"  > Cuerpo Hex: {body.hex()[:60]}...")
            except:
                continue
            time.sleep(1)

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    robust_sniff()
