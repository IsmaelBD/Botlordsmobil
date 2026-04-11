"""
==========================================================
  ESTETOSCOPIO DE RED - Interceptor de Paquetes de Marcha
  Fase 1: Capturar una marcha manual del jugador
==========================================================

ESTRATEGIA:
  En lugar de hookear la función Send (muy complejo en x64),
  vamos a leer la cola de envío (SendList) del NetworkManager
  DESPUÉS de que el jugador envíe una marcha manual.
  
  Alternativa más segura: Leer los datos que la UI prepara
  para la marcha (héroes, tropas) y construir nosotros
  el MessagePacket con los RVAs conocidos.
"""
import ctypes
import struct
import time
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

def capture_march_data():
    print("="*60)
    print("  ESTETOSCOPIO DE RED - Captura de Marcha Manual")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients:
        print("[!] No hay clientes activos.")
        return
    
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    # Obtener DataManager
    dm_ptr = bridge.call_rva(0x2914F50)
    if not dm_ptr:
        print("[!] Error: No se pudo obtener DataManager.")
        return
    
    print(f"[+] DataManager: 0x{dm_ptr:X}")
    
    # ============================================================
    # PASO 1: Leer estado actual de marchas (MarchEventData)
    # ============================================================
    # MaxMarchEventNum está en DM + offset (buscaremos)
    # MarchEventData[] está después
    
    # Por ahora, leamos los datos que la UI de expedición prepara:
    # - RoleAttr está en DM + 0x470 (_ROLEINFO)
    # - Dentro de _ROLEINFO hay info de tropas
    
    role_attr_ptr = dm_ptr + 0x470
    
    # Leer cantidad de tropas disponibles
    # _ROLEINFO tiene campos como SoldierCount en varios offsets
    # Vamos a leer los primeros 512 bytes de _ROLEINFO para analizar
    print("\n[*] Leyendo datos de tu ejército (_ROLEINFO)...")
    
    # Leer nivel del castillo (suele estar al principio)
    castle_lv = bridge.read_memory(role_attr_ptr + 0x0, "B")
    print(f"    Nivel dato[0]: {castle_lv[0] if castle_lv else 'N/A'}")
    
    # ============================================================
    # PASO 2: Monitorear la cola de envío del NetworkManager
    # ============================================================
    nm_ptr = bridge.call_rva(0x1D2CD40)  # NetworkManager.get_Instance()
    if not nm_ptr:
        print("[!] Error: No se pudo obtener NetworkManager.")
        return
    
    print(f"[+] NetworkManager: 0x{nm_ptr:X}")
    
    # SendList es static, necesitamos leer desde la clase estática
    # SendList offset en los statics: 0x98
    # Sequence es static: 0x11C (en instancia)
    
    # Leer el Sequence actual (número de paquete)
    # El sequence está en los campos estáticos de la clase
    nm_class = bridge.read_ptr(nm_ptr)  # vtable -> class
    if nm_class:
        print(f"    NM VTable: 0x{nm_class:X}")
    
    # ============================================================
    # PASO 3: Snapshot de marchas activas
    # ============================================================
    print("\n[*] Leyendo marchas activas actuales...")
    
    # MarchEventData en DataManager
    # Busquemos el offset exacto leyendo alrededor de donde están las marchas
    # MaxMarchEventNum: offset 0x920 (aproximado)
    
    # Leamos un rango de bytes para buscar el patrón
    for offset in [0x918, 0x920, 0x928, 0x930, 0x938, 0x940]:
        val = bridge.read_memory(dm_ptr + offset, "B")
        if val and 0 < val[0] < 10:
            print(f"    DM+0x{offset:X} = {val[0]} (posible MaxMarchEvents)")
    
    print("\n" + "="*60)
    print("  INSTRUCCIONES PARA LA CAPTURA:")
    print("="*60)
    print("""
  1. Abre Lords Mobile y ve al mapa del reino
  2. Busca CUALQUIER mina cercana (no importa el tipo)
  3. Toca la mina y presiona "Recolectar"
  4. Selecciona tus tropas y héroes normalmente
  5. Presiona "MARCHAR" para enviar la recolección
  6. Vuelve aquí y ejecuta: python net_sniffer_phase2.py
  
  El bot capturará los datos de esa marcha y
  los usará como plantilla para futuras marchas automáticas.
    """)
    
    # ============================================================
    # PASO 4: Guardar snapshot del estado previo
    # ============================================================
    # Guardamos el Sequence actual para comparar después
    print("[*] Guardando snapshot del estado actual...")
    
    # Leer cuántas marchas hay activas ahora
    map_mgr_ptr = bridge.call_rva(0x2915080)
    
    # Guardar datos en archivo temporal
    snapshot = {
        "dm_ptr": dm_ptr,
        "nm_ptr": nm_ptr,
        "map_mgr_ptr": map_mgr_ptr,
        "timestamp": time.time()
    }
    
    with open("march_snapshot.txt", "w") as f:
        for k, v in snapshot.items():
            f.write(f"{k}={v}\n")
    
    print(f"[+] Snapshot guardado. Ahora envía una marcha manual.")
    print(f"[*] Después ejecuta: python net_sniffer_phase2.py")

if __name__ == "__main__":
    capture_march_data()
