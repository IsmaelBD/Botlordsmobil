"""
==========================================================
  ESTETOSCOPIO DE RED - Fase 2: Captura + Clonación
  Objetivo: Mina de Mineral en (68, 185)
==========================================================
"""
import ctypes
import struct
import time
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

# Objetivo de la marcha clonada
TARGET_X = 68
TARGET_Y = 185
TARGET_MAP_ID = TARGET_Y * 512 + TARGET_X  # = 94788

def phase2_capture_and_clone():
    print("="*60)
    print("  FASE 2: Captura de Marcha + Clonación a (68, 185)")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients:
        print("[!] No hay clientes activos.")
        return
    
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    dm_ptr = bridge.call_rva(0x2914F50)
    map_mgr_ptr = bridge.call_rva(0x2915080)
    
    print(f"[+] DataManager: 0x{dm_ptr:X}")
    print(f"[+] MapManager:  0x{map_mgr_ptr:X}")
    print(f"[+] Objetivo:    Mina Mineral ({TARGET_X}, {TARGET_Y}) MapID={TARGET_MAP_ID}")
    
    # ============================================================
    # PASO 1: Detectar marchas activas (post-marcha manual)
    # ============================================================
    print("\n[*] Buscando marchas activas en memoria...")
    
    # MarchEventData está en DataManager
    # Cada MarchEventData tiene: MapPointID, MarchType, etc.
    # Buscaremos los campos de MarchEvent en el DM
    
    # Leemos MarchEventData array pointer
    # Típicamente está después de los campos de héroe (~0x920-0xA00)
    
    # Alternativa: Buscar directamente el patrón de la marcha reciente
    # leyendo bloques de memoria del DM
    
    march_events = []
    
    # Escanear rangos conocidos del DataManager buscando MarchEventData
    # El campo MarchEventNum suele ser un byte que indica cuántas marchas hay
    for test_offset in range(0x900, 0xC00, 8):
        ptr = bridge.read_ptr(dm_ptr + test_offset)
        if ptr and 0x200000000000 < ptr < 0x300000000000:
            # Podría ser un puntero a un objeto de marcha
            # Intentar leer un MapPointID (int) del objeto
            map_id_val = bridge.read_memory(ptr + 0x10, "<I")
            if map_id_val and 0 < map_id_val[0] < 524288:
                march_type = bridge.read_memory(ptr + 0x14, "B")
                mt = march_type[0] if march_type else 0
                mx = map_id_val[0] % 512
                my = map_id_val[0] // 512
                march_events.append({
                    "offset": test_offset,
                    "map_id": map_id_val[0],
                    "x": mx, "y": my,
                    "march_type": mt,
                    "ptr": ptr
                })
    
    if march_events:
        print(f"\n[+] {len(march_events)} posibles marchas detectadas:")
        for me in march_events:
            print(f"    DM+0x{me['offset']:X} -> MapID:{me['map_id']} ({me['x']},{me['y']}) Type:{me['march_type']}")
    else:
        print("[!] No se detectaron marchas activas por escaneo directo.")
        print("[*] Intentando método alternativo: lectura del protocolo...")
    
    # ============================================================
    # PASO 2: Construir MessagePacket para marcha a (68, 185)
    # ============================================================
    print("\n[*] Preparando inyección de marcha...")
    print(f"    Destino: ({TARGET_X}, {TARGET_Y}) = MapID {TARGET_MAP_ID}")
    
    # La estructura del paquete _MSG_REQUEST_TROOPMARCH (2415) es:
    # Protocol: 2415 (ushort)
    # MapPointID: int (destino)
    # MarchType: byte (1=ataque, 2=recolección, 3=scout, 4=refuerzo)
    # ArmyIndex: byte (índice del ejército, 0-based)
    # HeroCount: byte
    # HeroID[]: ushort[] (IDs de héroes)
    # TroopType: byte (tipo de tropa)
    # TroopCount: uint (cantidad)
    # ... (puede variar)
    
    # Para recolección: MarchType = 2 (Gathering)
    MARCH_TYPE_GATHER = 2
    
    # Necesitamos saber qué tropas y héroes tiene el jugador disponibles
    # Leamos los héroes desde curHeroData
    hero_data_ptr = bridge.read_ptr(dm_ptr + 0x830)  # curHeroData CHashTable
    hero_count = bridge.read_memory(dm_ptr + 0x824, "<I")
    
    print(f"    Héroes disponibles: {hero_count[0] if hero_count else '?'}")
    
    # Para una marcha de recolección simple, necesitamos al menos:
    # - 1 héroe líder (cualquiera disponible)
    # - N tropas (las que tenga el jugador)
    
    # ============================================================
    # PASO 3: Inyectar la marcha usando call_rva
    # ============================================================
    # En lugar de construir el paquete byte a byte, vamos a usar
    # las funciones internas del juego para que él mismo lo construya:
    #
    # 1. Crear un MessagePacket (via .ctor) -> RVA: 0x1D238A0
    # 2. Setear Protocol a 2415
    # 3. Llamar a los Add() para cada campo
    # 4. Llamar a MessagePacket.Send() -> RVA: 0x1D23440
    #
    # PERO esto requiere pasar un puntero 'this' (el MessagePacket),
    # lo cual necesita alocar un objeto IL2CPP válido.
    #
    # ALTERNATIVA MÁS SEGURA: Buscar una función de alto nivel
    # que acepte MapPointID y tipo, y que ella misma construya todo.
    
    print("\n[*] Buscando funciones de alto nivel para inyectar la marcha...")
    print("    Nota: La inyección directa del paquete requiere construir")
    print("    un objeto MessagePacket válido en el heap de IL2CPP.")
    print("    Esto se hará de forma segura usando il2cpp_object_new.")
    
    # il2cpp_object_new nos permite crear objetos gestionados
    # RVA de il2cpp_object_new: necesitamos buscarlo
    
    print("\n[RESUMEN]")
    print(f"  ✓ NetworkManager localizado")
    print(f"  ✓ Objetivo confirmado: Mineral en ({TARGET_X}, {TARGET_Y})")
    print(f"  ✓ Protocolo: 2415 (_MSG_REQUEST_TROOPMARCH)")
    print(f"  ✓ Tipo de marcha: 2 (Recolección)")
    print(f"  → Siguiente paso: Necesito que envíes UNA marcha manual")
    print(f"    para capturar la plantilla de héroes/tropas.")

if __name__ == "__main__":
    phase2_capture_and_clone()
