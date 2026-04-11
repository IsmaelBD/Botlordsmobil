import ctypes
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar
import time

def verify_injection_effect():
    print("="*60)
    print("      VERIFICADOR DE TELEMETRÍA FANTASMA (FASE 6)")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients:
        print("[!] No hay clientes activos.")
        return

    client = radar.clients[0]
    pid = client["pid"]
    base = client["assembly_base"]
    handle = client["handle"]
    
    bridge = InternalBridge(pid, base)
    
    # 1. Localizar DataManager.Instance
    dm_typeinfo_rva = 0x58F5368
    type_info_addr = radar.read_pointer(handle, base + dm_typeinfo_rva)
    static_fields_ptr = radar.read_pointer(handle, type_info_addr + 0xB8)
    instance_ptr = radar.read_pointer(handle, static_fields_ptr + 0x18)
    
    if not instance_ptr:
        print("[!] Error localizando instancia.")
        return
        
    # 2. Leer estado ANTES de inyectar
    # Offset de SPLastGetDailyGiftTime: 0xD10 (según dump.cs)
    # Es un long (8 bytes)
    time_before = radar.read_uint64(handle, instance_ptr + 0xD10)
    print(f"[*] Marca de tiempo ANTES: {time_before}")
    
    # 3. Inyectar llamada a CheckDailyGift() (RVA: 0x2840330)
    print("[*] Ejecutando orden interna CheckDailyGift()...")
    bridge.call_rva(0x2840330, [instance_ptr])
    
    # Esperamos un momento para que el servidor responda y la memoria se actualice
    time.sleep(2)
    
    # 4. Leer estado DESPUÉS de inyectar
    time_after = radar.read_uint64(handle, instance_ptr + 0xD10)
    print(f"[*] Marca de tiempo DESPUÉS: {time_after}")
    
    if time_after != time_before:
        print("\n" + "!"*40)
        print("   ✅ ¡PRUEBA DE VIDA EXITOSA!")
        print(f"   El valor cambió de {time_before} a {time_after}")
        print("   Esto demuestra que el servidor respondió a nuestro bot.")
        print("!"*40)
    else:
        print("\n" + "?"*40)
        print("   [-] El valor no cambió.")
        print("   Esto puede pasar si el regalo ya fue reclamado hoy.")
        print("   O si Windows Defender bloqueó el hilo de ejecución.")
        print("?"*40)

if __name__ == "__main__":
    verify_injection_effect()
