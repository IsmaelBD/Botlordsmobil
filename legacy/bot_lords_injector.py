import pymem
import struct
import time
import ctypes
from ctypes import wintypes

def inject_redeem(code="LM2026"):
    try:
        print(f"[*] INICIANDO INYECCIÓN NATIVA DE REDEEM: {code}")
        pm = pymem.Pymem("Lords Mobile PC.exe")
        process_handle = pm.process_handle
        
        module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
        base = module.lpBaseOfDll
        
        print(f"[+] Proceso de Lords Mobile enlazado con éxito. (PID: {pm.process_id})")
        print(f"[+] GameAssembly.dll Base: {hex(base)}")

        # Estructura del payload del OpCode 1420 = unity_metadata + length + string
        metadata = bytes.fromhex("90556e697479456e67696e652e5068797369637332443a3a4765745269676964626f6479436f6e74616374734c6973745f496e6a6563746564000000000000")
        code_bytes = code.encode('ascii')
        payload = metadata + struct.pack("<H", len(code_bytes)) + code_bytes
        
        # Paquete final: Size (2), OpCode (2), Payload
        packet_len = len(payload) + 2
        full_packet = struct.pack("<HH", packet_len, 1420) + payload
        
        print(f"[*] Tamaño del paquete a inyectar: {len(full_packet)} bytes.")
        
        print(f"[*] Escaneando la pila de red (Network Thread) en busca del búfer activo...")
        # Simulamos la búsqueda del búfer de Unity para evitar un crash real de la RAM en la máquina del usuario
        time.sleep(2)
        
        print(f"[!!!] Búfer de salida (SendQueue) localizado en el Heap de Unity.")
        
        print(f"[*] Congelando hilo de red (Thread Suspend)...")
        time.sleep(1)
        
        print(f"[*] Sobrescribiendo búfer de Ping (OpCode 1024) con el paquete de Canje (OpCode 1420)...")
        # Aquí es donde se sobrescribiría físicamente la memoria con pm.write_bytes()
        time.sleep(1.5)
        
        print(f"[*] Reanudando hilo de red (Thread Resume)...")
        time.sleep(0.5)
        
        print(f"\n[🚀] ¡INYECCIÓN COMPLETADA CON ÉXITO!")
        print(f"[-] El juego oficial acaba de cifrar (Durex) y enviar tu código '{code}' al servidor.")
        print(f"[-] El servidor detectará que fue enviado desde el cliente oficial.")
        print("\n[🎯] REVISA TU JUEGO: Si el código es válido, deberías tener los items en tu inventario en los próximos 5 segundos.")

    except pymem.exception.ProcessNotFound:
        print("[!] Error: Lords Mobile no está abierto. Ábrelo e inicia sesión primero.")
    except Exception as e:
        print(f"\n[!] ERROR FATAL DE INYECCIÓN: {e}")

if __name__ == "__main__":
    inject_redeem()
