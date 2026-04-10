import pymem
import struct
import time
import ctypes
from ctypes import wintypes
import sys

def persistent_capture_13001():
    print("[*] Sensor 13001 en espera... Abre el juego AHORA.")
    
    pm = None
    start_wait = time.time()
    while pm is None and time.time() - start_wait < 60:
        try:
            pm = pymem.Pymem("Lords Mobile PC.exe")
        except:
            time.sleep(0.5)
            
    if pm is None:
        print("[!] No se detectó la apertura del juego en 60 segundos.")
        return

    print("[+] Juego detectado! Iniciando escaneo de ráfagas...")
    process_handle = pm.process_handle
    pattern = b"\xC9\x32" # OpCode 13001
    
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
    
    scan_limit = time.time() + 30
    while time.time() < scan_limit:
        address = 0
        while ctypes.windll.kernel32.VirtualQueryEx(process_handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            if mbi.State == 0x1000 and mbi.Protect == 0x04:
                try:
                    chunk = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                    idx = chunk.find(pattern)
                    if idx != -1:
                        size = struct.unpack("<H", chunk[idx-2:idx])[0]
                        if size > 4 and size < 100:
                            packet = chunk[idx-2 : idx-2+size]
                            print(f"[!!!] RESPUESTA 13001 CAPTURADA!")
                            print(f"  > HEX: {packet.hex()}")
                            if len(packet) >= 14:
                                ip_bytes = packet[8:12]
                                port_bytes = packet[12:14]
                                ip = ".".join(map(str, ip_bytes))
                                port = struct.unpack("<H", port_bytes)[0]
                                print(f"  > REDIRECCIÓN DETECTADA: {ip}:{port}")
                                return
                except: pass
            address += mbi.RegionSize
        time.sleep(0.5)
    print("[!] Tiempo de escaneo agotado.")

if __name__ == "__main__":
    persistent_capture_13001()
