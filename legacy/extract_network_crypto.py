import pymem
import pymem.process
import struct

def dump_static_fields():
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
        base = module.lpBaseOfDll
        
        # Dirección calculada en el paso anterior
        # Static Fields Ptr Addr: 0x7ffc12abd448
        static_fields_ptr_addr = 0x7ffc12abd448
        static_fields_addr = pm.read_longlong(static_fields_ptr_addr)
        
        if not static_fields_addr:
            print("[!] Static Fields no inicializados.")
            return
            
        print(f"[*] Static Fields Base: {hex(static_fields_addr)}")
        
        # Volcar los primeros 512 bytes para buscar punteros
        print("[*] Volcando memoria (offsets 0x0 a 0x200):")
        for offset in range(0, 0x200, 8):
            val = pm.read_longlong(static_fields_addr + offset)
            # Marcar si parece un puntero válido en el espacio de usuario
            tag = " [PTR?]" if 0x10000000000 <= val <= 0x7FFFFFFFFFF else ""
            print(f"  Offset {hex(offset)}: {hex(val)}{tag}")
            
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    dump_static_fields()
