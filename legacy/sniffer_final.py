import pymem
import struct
import time
import ctypes
from ctypes import wintypes
import os

def final_protocol_sniff():
    print("[*] Buscando proceso de Lords Mobile...")
    
    try:
        # Intentamos los nombres comunes
        target = "Lords Mobile PC.exe"
        pm = pymem.Pymem(target)
        print(f"[+] Proceso detectado: {target}")
    except:
        print("[!] No se encontró por nombre directo. Reintentando...")
        return

    try:
        print("[*] SNIFFER MAESTRO ACTIVO. Capturando ráfagas...")
        process_handle = pm.process_handle
        opcodes_to_find = [13000, 1024, 1043, 1420]
        captured_data = {}

        mbi = MEMORY_BASIC_INFORMATION = type('MEMORY_BASIC_INFORMATION', (ctypes.Structure,), {
            '_fields_': [
                ('BaseAddress', ctypes.c_void_p),
                ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wintypes.DWORD),
                ('RegionSize', ctypes.c_size_t),
                ('State', wintypes.DWORD),
                ('Protect', wintypes.DWORD),
                ('Type', wintypes.DWORD),
            ]
        })()
        
        start_time = time.time()
        while time.time() - start_time < 30:
            address = 0
            while ctypes.windll.kernel32.VirtualQueryEx(process_handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                if mbi.State == 0x1000 and mbi.Protect == 0x04:
                    try:
                        chunk = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                        for op in opcodes_to_find:
                            op_bytes = struct.pack("<H", op)
                            idx = chunk.find(op_bytes)
                            if idx >= 2:
                                size = struct.unpack("<H", chunk[idx-2:idx])[0]
                                if size > 10 and size < 500:
                                    packet = chunk[idx-2 : idx-2+size]
                                    if op not in captured_data:
                                        captured_data[op] = packet
                                        print(f"[+] CAPTURADO OpCode {op} | Tamaño: {size}")
                    except: pass
                address += mbi.RegionSize
            
            if len(captured_data) == len(opcodes_to_find): break
            time.sleep(1)

        print("\n--- VOLCADO DE PROTOCOLO REAL ---")
        for op, data in captured_data.items():
            print(f"OpCode {op}: {data.hex()}")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    final_protocol_sniff()
