import pymem
import struct
import time
import ctypes
from ctypes import wintypes

def sequence_delta_analyzer():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        print("[*] ANALIZADOR DE DELTA ACTIVO. Capturando ráfagas consecutivas...")
        
        process_handle = pm.process_handle
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
        
        sequences = []
        start_time = time.time()
        while len(sequences) < 3 and time.time() - start_time < 30:
            address = 0
            while ctypes.windll.kernel32.VirtualQueryEx(process_handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                if mbi.State == 0x1000 and mbi.Protect == 0x04:
                    try:
                        chunk = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                        idx = chunk.find(b"\xC8\x32") # OpCode 13000
                        if idx >= 2:
                            seq_bytes = chunk[idx+2 : idx+6]
                            seq_val = struct.unpack("<I", seq_bytes)[0]
                            if seq_val not in sequences:
                                sequences.append(seq_val)
                                print(f"[+] Secuencia capturada: {seq_val} (HEX: {seq_bytes.hex()})")
                                break
                    except: pass
                address += mbi.RegionSize
            time.sleep(1)

        if len(sequences) >= 2:
            delta = sequences[1] - sequences[0]
            print(f"\n--- ANÁLISIS DE DELTA ---")
            print(f"Secuencia 1: {sequences[0]}")
            print(f"Secuencia 2: {sequences[1]}")
            print(f"INCREMENTO (DELTA): {delta}")
            if delta > 1000:
                print("[!] El delta es grande: Probablemente sea un TIMESTAMP (milisegundos).")
            else:
                print("[!] El delta es pequeño: Es un CONTADOR de paquetes.")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    sequence_delta_analyzer()
