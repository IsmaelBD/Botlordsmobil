import ctypes
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar
import time

def execute_magic_silence():
    print("="*60)
    print("      DEMOSTRACIÓN DE CONTROL INTERNO: HECHIZO DE SILENCIO")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients:
        print("[!] No hay clientes activos.")
        return

    client = radar.clients[0]
    pid = client["pid"]
    base = client["assembly_base"]
    
    bridge = InternalBridge(pid, base)
    
    # 1. Obtener la instancia de AudioManager
    # RVA de get_Instance(): 0xF60C40
    print("[*] Localizando AudioManager...")
    audio_instance = bridge.call_rva(0xF60C40)
    
    if not audio_instance:
        print("[!] No se pudo localizar el AudioManager.")
        return
        
    print(f"[+] AudioManager encontrado en: 0x{audio_instance:X}")
    
    # RVAs de Interés:
    # SwitchMusic(bool TurnOn) -> 0xF5EAA0
    
    print("\n[!] PASO 1: APAGANDO MÚSICA EN 3... 2... 1...")
    # FastCall: RCX = Instance, RDX = TurnOn (0 = False)
    bridge.call_rva(0xF5EAA0, [audio_instance, 0])
    
    print("[*] Silencio total por 5 segundos...")
    time.sleep(5)
    
    print("\n[!] PASO 2: RESTAURANDO MÚSICA...")
    # FastCall: RCX = Instance, RDX = TurnOn (1 = True)
    bridge.call_rva(0xF5EAA0, [audio_instance, 1])
    
    print("\n" + "!"*40)
    print("   ✅ PRUEBA FINALIZADA.")
    print("   Si notaste el cambio de sonido, el bot es real.")
    print("!"*40)

if __name__ == "__main__":
    execute_magic_silence()
