import pymem
import struct
import time
import ctypes
from ctypes import wintypes

def start_robust_spy():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        print("[*] MISIÓN DE ESPIONAJE ACTIVA (MODO ROBUSTO).")
        print("[*] TIENES 30 SEGUNDOS PARA PULSAR 'CANJEAR' EN EL JUEGO.")
        
        process_handle = pm.process_handle
        
        # MBI structure for VirtualQueryEx
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
                if mbi.State == 0x1000 and mbi.Protect == 0x04: # READWRITE
                    try:
                        chunk = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                        # Buscamos el OpCode 1420 (0x058C)
                        idx = chunk.find(b"\x8C\x05")
                        if idx >= 2:
                            size = struct.unpack("<H", chunk[idx-2:idx])[0]
                            if size > 10 and size < 500:
                                packet = chunk[idx-2 : idx-2+size]
                                print(f"[!!!] PAQUETE CAPTURADO!")
                                print(f"  > HEX: {packet.hex()}")
                                return
                    except: pass
                address += mbi.RegionSize
            
            time.sleep(0.1)
            
        print("[!] Fin del tiempo de espera. No se capturó ráfaga.")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    start_robust_spy()
