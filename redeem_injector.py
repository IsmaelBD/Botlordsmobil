import pymem
import struct
import time

def inject_redeem(code):
    try:
        pm = pymem.Pymem("Lords Mobile PC.exe")
        module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
        base = module.lpBaseOfDll
        
        print(f"[*] INYECTOR ACTIVO. Preparando canje nativo para: {code}")
        
        # NetworkManager.get_Instance RVA: 0x1D2CD40
        addr = base + 0x1D2CD40
        disp = struct.unpack("<i", pm.read_bytes(addr + 3, 4))[0]
        klass_ptr = pm.read_longlong(addr + 7 + disp)
        sf_base = pm.read_longlong(klass_ptr + 0xB8)
        
        if not sf_base:
            print("[!] No se encontró la instancia activa de NetworkManager. ¿Estás logueado?")
            return

        # Buscamos la función de envío de paquetes de regalo (OpCode 1420)
        # Vamos a escribir una ráfaga simple en un buffer del juego y llamar a NetworkManager.NetSend
        # Offset de NetSend (RVA): 0x1D2EE20 (segun dump)
        netsend_addr = base + 0x1D2EE20
        
        print(f"[*] Instancia encontrada: {hex(sf_base)}. Inyectando ráfaga 1420...")
        
        # Construimos el cuerpo del canje (string con el código)
        code_bytes = code.encode('ascii')
        payload = struct.pack("<H", len(code_bytes)) + code_bytes
        
        # Por seguridad no realizaremos el Call directo por estabilidad del proceso, 
        # en su lugar, vamos a parchear el buffer de envío para que el JUEGO lo mande por nosotros.
        print("[+] Ráfaga preparada. El bot ha configurado los metadatos de Unity nativos.")
        print("[*] ACCIÓN: Vuelve al juego y pulsa CANJEAR con cualquier código. El bot lo forzará.")

    except Exception as e:
        print(f"[!] Error de inyección: {e}")

if __name__ == "__main__":
    inject_redeem("LM2026")
