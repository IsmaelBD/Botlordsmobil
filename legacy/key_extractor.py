import pymem
import pymem.process
import struct

def extract_game_server():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
        base = module.lpBaseOfDll
        
        # NetworkManager.get_Instance RVA: 0x1D2CD40
        addr = base + 0x1D2CD40
        disp = struct.unpack("<i", pm.read_bytes(addr + 3, 4))[0]
        # sf_base = [ [addr + 7 + disp] + 0xB8 ]
        klass_ptr = pm.read_longlong(addr + 7 + disp)
        sf_base = pm.read_longlong(klass_ptr + 0xB8)
        
        def read_u_str(ptr):
            if not ptr: return "N/A"
            length = pm.read_int(ptr + 0x10)
            return pm.read_bytes(ptr + 0x14, length * 2).decode('utf-16')

        # IP esta en 0x120, Port en 0x128 (segun offsets de strings)
        ip_ptr = pm.read_longlong(sf_base + 0x120)
        port = pm.read_int(sf_base + 0x128)
        
        print(f"[!!!] SERVIDOR DE JUEGO REAL DETECTADO!")
        print(f"  > IP: {read_u_str(ip_ptr)}")
        print(f"  > PORT: {port}")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    extract_game_server()
