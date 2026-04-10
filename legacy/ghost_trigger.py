import ctypes
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar
import time

def run_ghost_injection():
    print("="*60)
    print("         INICIANDO DISPARADOR FANTASMA (FASE 6)")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients:
        print("[!] No hay clientes activos para inyectar.")
        return

    client = radar.clients[0]
    pid = client["pid"]
    base = client["assembly_base"]
    handle = client["handle"]
    
    bridge = InternalBridge(pid, base)
    
    # 1. Localizar DataManager.Instance (RVA del TypeInfo)
    # Según mem_radar.py, el TypeInfo está en base + 0x58F5368
    dm_typeinfo_rva = 0x58F5368
    
    print(f"[*] Buscando instancia de DataManager...")
    type_info_addr = radar.read_pointer(handle, base + dm_typeinfo_rva)
    if not type_info_addr:
        print("[!] No se pudo obtener el TypeInfo.")
        return
        
    static_fields_ptr = radar.read_pointer(handle, type_info_addr + 0xB8)
    instance_ptr = radar.read_pointer(handle, static_fields_ptr + 0x18)
    
    if not instance_ptr:
        print("[!] DataManager.Instance es NULL. ¿Estás logueado?")
        return
        
    print(f"[+] DataManager localizado en: 0x{instance_ptr:X}")
    
    # 2. Inyectar llamada a CheckDailyGift (RVA: 0x2840330)
    # CheckDailyGift() es un método de instancia, por lo tanto RCX = instance_ptr
    print(f"[*] Inyectando orden: CheckDailyGift()...")
    
    # El Puente Interno usa FastCall, así que pasamos instance_ptr como primer argumento (RCX)
    result = bridge.call_rva(0x2840330, [instance_ptr])
    
    print(f"[!] ORDEN EJECUTADA. Código de respuesta del juego: {result}")
    print("[*] Si el regalo diario estaba disponible, debería haberse reclamado ahora.")

if __name__ == "__main__":
    run_ghost_injection()
