import pymem
import pymem.process
import struct

def find_sequence():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
        base = module.lpBaseOfDll
        
        # RVA de NetworkManager.get_Instance
        addr = base + 0x1D2CD40
        code = pm.read_bytes(addr, 64)
        idx = code.find(b"\x48\x8b\x0d")
        if idx == -1:
            print("[!] Motor de red no localizado. ¿Está el juego abierto?")
            return

        disp = struct.unpack("<i", code[idx+3:idx+7])[0]
        klass_ptr = addr + idx + 7 + disp
        
        klass = pm.read_longlong(klass_ptr)
        # static_fields pointer suele estar en +0xB0 o +0xB8 en IL2CPP 
        static_fields = pm.read_longlong(klass + 0xB8)
        
        if not static_fields:
            # Reintentar con offset 0xB0 si falló
            static_fields = pm.read_longlong(klass + 0xB0)

        if static_fields:
            # Sequence (int) @ 0x11C
            seq = pm.read_int(static_fields + 0x11C)
            print(f"[+] SINCRONIZADO!")
            print(f"[+] Secuencia de Red Actual: {seq}")
            
            # Intentamos leer la IP del servidor (string) @ 0x120 o 0xD8
            ip_ptr = pm.read_longlong(static_fields + 0x120)
            if ip_ptr:
                try:
                    length = pm.read_int(ip_ptr + 0x10)
                    ip_str = pm.read_bytes(ip_ptr + 0x14, length * 2).decode('utf-16')
                    print(f"[+] IP Servidor: {ip_str}")
                except: pass
        else:
            print("[!] No se pudo encontrar el bloque de variables de red.")

    except Exception as e:
        print(f"[!] Error de acceso: {e}")

if __name__ == "__main__":
    find_sequence()
