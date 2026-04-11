"""
==========================================================
  FASE 3: Lectura de Marcha Activa + Clonación
  Objetivo: Capturar plantilla y enviar a (68, 185)
==========================================================
"""
import ctypes
import struct
import time
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

TARGET_X = 68
TARGET_Y = 185
TARGET_MAP_ID = TARGET_Y * 512 + TARGET_X  # 94788

def read_active_march():
    print("="*60)
    print("  FASE 3: Lectura de Marcha Activa")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    dm_ptr = bridge.call_rva(0x2914F50)
    print(f"[+] DataManager: 0x{dm_ptr:X}")
    
    # MaxMarchEventNum en DM + 0x1074
    max_march = bridge.read_memory(dm_ptr + 0x1074, "B")
    max_march_num = max_march[0] if max_march else 0
    print(f"[+] Max March Slots: {max_march_num}")
    
    # MarchEventData[] en DM + 0x1078 (puntero a array de structs)
    march_array_ptr = bridge.read_ptr(dm_ptr + 0x1078)
    print(f"[+] MarchEventData[]: 0x{march_array_ptr:X}")
    
    if not march_array_ptr:
        print("[!] No hay datos de marchas en memoria.")
        return
    
    # MarchEventDataType es un struct de ~0x50 bytes
    # Pero en IL2CPP, un array de structs tiene un header
    # Header: 8 bytes (klass) + 8 bytes (monitor) + 4 bytes (bounds) + 4 bytes (max_length)
    # = 0x20 bytes de header (en x64 alineado)
    
    # Leer length del array
    array_len_data = bridge.read_memory(march_array_ptr + 0x18, "<I")
    array_len = array_len_data[0] if array_len_data else 0
    print(f"[+] Array length: {array_len}")
    
    items_base = march_array_ptr + 0x20
    
    # MarchEventDataType struct layout:
    # 0x00: EMarchEventType Type (int, 4 bytes)
    # 0x08: ushort[] HeroID (ptr, 8 bytes)
    # 0x10: uint[][] TroopData (ptr, 8 bytes)
    # 0x18: PointCode Point (struct)
    # 0x20: uint[] ResourceGetCount (ptr)
    # 0x28: uint Crystal
    # 0x2C: uint MaxOverLoad
    # 0x30: POINT_KIND PointKind (byte)
    # 0x32: ushort DesPointLevel
    
    STRIDE = 0x50  # Tamaño del struct alineado
    
    found_active = False
    template = None
    
    for i in range(min(array_len, 8)):
        base = items_base + (i * STRIDE)
        
        # Leer Type (EMarchEventType) - 4 bytes
        type_data = bridge.read_memory(base + 0x0, "<I")
        march_type = type_data[0] if type_data else 0
        
        if march_type == 0:
            continue  # Slot vacío
        
        found_active = True
        print(f"\n[MARCHA #{i}] Tipo: {march_type}")
        
        # Leer HeroID[] pointer
        hero_arr_ptr = bridge.read_ptr(base + 0x08)
        if hero_arr_ptr:
            hero_len = bridge.read_memory(hero_arr_ptr + 0x18, "<I")
            hero_count = hero_len[0] if hero_len else 0
            heroes = []
            for h in range(min(hero_count, 5)):
                hid = bridge.read_memory(hero_arr_ptr + 0x20 + (h * 2), "<H")
                if hid:
                    heroes.append(hid[0])
            print(f"    Héroes ({hero_count}): {heroes}")
        
        # Leer TroopData[][] pointer
        troop_arr_ptr = bridge.read_ptr(base + 0x10)
        if troop_arr_ptr:
            troop_outer_len = bridge.read_memory(troop_arr_ptr + 0x18, "<I")
            troop_tiers = troop_outer_len[0] if troop_outer_len else 0
            print(f"    Tropas (Tiers: {troop_tiers}):")
            
            all_troops = []
            for t in range(min(troop_tiers, 5)):
                inner_ptr = bridge.read_ptr(troop_arr_ptr + 0x20 + (t * 8))
                if inner_ptr:
                    inner_len = bridge.read_memory(inner_ptr + 0x18, "<I")
                    count = inner_len[0] if inner_len else 0
                    tier_data = []
                    for s in range(min(count, 4)):
                        val = bridge.read_memory(inner_ptr + 0x20 + (s * 4), "<I")
                        tier_data.append(val[0] if val else 0)
                    all_troops.append(tier_data)
                    if any(v > 0 for v in tier_data):
                        print(f"      Tier {t}: {tier_data}")
        
        # Leer PointCode (ushort KingdomID + byte InstanceID + PointCode coords)
        # PointCode suele ser: ushort Zone, byte Point
        point_data = bridge.read_memory(base + 0x18, "8B")
        if point_data:
            hex_str = " ".join([f"{b:02X}" for b in point_data])
            print(f"    PointCode (raw): {hex_str}")
        
        # PointKind
        point_kind = bridge.read_memory(base + 0x30, "B")
        pk = point_kind[0] if point_kind else 0
        print(f"    PointKind: {pk}")
        
        # DesPointLevel
        des_level = bridge.read_memory(base + 0x32, "<H")
        dl = des_level[0] if des_level else 0
        print(f"    DesPointLevel: {dl}")
        
        # Guardar como plantilla
        if not template:
            template = {
                "type": march_type,
                "heroes": heroes if hero_arr_ptr else [],
                "troops": all_troops if troop_arr_ptr else [],
                "point_kind": pk,
                "level": dl,
                "slot": i
            }
    
    if not found_active:
        print("\n[!] No se detectó ninguna marcha activa.")
        print("    ¿Enviaste la marcha manual? Intenta de nuevo.")
        return
    
    print("\n" + "="*60)
    print("  PLANTILLA CAPTURADA")
    print("="*60)
    if template:
        print(f"  Tipo:     {template['type']}")
        print(f"  Héroes:   {template['heroes']}")
        print(f"  Tropas:   {template['troops']}")
        print(f"  Slot:     {template['slot']}")
        print(f"\n  → LISTO para clonar hacia ({TARGET_X}, {TARGET_Y})")
        
        # Guardar plantilla
        with open("march_template.txt", "w") as f:
            f.write(f"type={template['type']}\n")
            f.write(f"heroes={template['heroes']}\n")
            f.write(f"troops={template['troops']}\n")
            f.write(f"slot={template['slot']}\n")
        print(f"  [✓] Plantilla guardada en march_template.txt")

if __name__ == "__main__":
    read_active_march()
