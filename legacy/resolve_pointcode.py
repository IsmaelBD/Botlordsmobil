"""
==========================================================
  RESOLUCIÓN DE POINTCODE + INYECCIÓN DE MARCHA
==========================================================
"""
import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

TARGET_X = 68
TARGET_Y = 185
TARGET_MAP_ID = TARGET_Y * 512 + TARGET_X  # 94788

def resolve_and_inject():
    print("="*60)
    print("  RESOLVER POINTCODE + INYECTAR MARCHA")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    dm_ptr = bridge.call_rva(0x2914F50)
    map_mgr_ptr = bridge.call_rva(0x2915080)
    
    # Leer ServerNowKingdomID
    kingdom_id_data = bridge.read_memory(map_mgr_ptr + 0x1B4, "<H")
    kingdom_id = kingdom_id_data[0] if kingdom_id_data else 0
    print(f"[+] Kingdom ID: {kingdom_id}")
    
    # Usar la función estática:
    # PointCodeToMapID(ushort zoneID, byte pointID, ushort kingdomID) -> int
    # RVA: 0x5A5380
    # Y la inversa:
    # MapIDToPointCode(int mapID, out ushort zoneID, out byte pointID, ushort kingdomID)
    # RVA: 0x5A4C60
    
    # La marcha capturada tenía PointCode: zoneID=507 (0x01FB), pointID=59 (0x3B)
    # Verificar: PointCodeToMapID(507, 59, kingdomID) debería dar un MapID válido
    print(f"\n[Verificación] PointCodeToMapID(507, 59, {kingdom_id})...")
    verify_result = bridge.call_rva(0x5A5380, [507, 59, kingdom_id])
    verify_x = verify_result % 512
    verify_y = verify_result // 512
    print(f"    Resultado: MapID={verify_result} -> ({verify_x}, {verify_y})")
    
    # Ahora, necesitamos el PointCode para el MapID del mineral
    # Para llamar a MapIDToPointCode con out params, es más complicado.
    # En su lugar, calcularemos manualmente usando la fórmula inversa.
    
    # La fórmula de PointCodeToMapID es:
    # absX = WorldOX + (zoneID % zonesPerRow) * zoneW + (pointID % zoneW)
    # absY = WorldOY + (zoneID / zonesPerRow) * zoneH + (pointID / zoneW)
    # mapID = absY * mapWidth + absX
    
    # Pero no conocemos zonesPerRow ni zoneW/zoneH exactos.
    # Podemos deducirlos de la verificación:
    # Si PointCode(507, 59) -> MapID = verify_result
    
    world_ox = bridge.read_memory(map_mgr_ptr + 0x1B6, "<H")[0]
    world_oy = bridge.read_memory(map_mgr_ptr + 0x1B8, "<H")[0]
    
    print(f"[+] WorldOX={world_ox}, WorldOY={world_oy}")
    
    # Probar diferentes tamaños de zona para encontrar el correcto
    print("\n[*] Deduciendo tamaño de zona...")
    
    # Probar con zoneW=8 (el más común en Lords Mobile)
    for zw in [6, 7, 8, 9, 10]:
        zh = zw  # Asumimos cuadrado
        zones_per_row = 512 // zw  # Ajustar si es necesario
        
        # De PointCode(507, 59):
        test_zone_x = 507 % zones_per_row
        test_zone_y = 507 // zones_per_row
        test_point_x = 59 % zw
        test_point_y = 59 // zw
        
        calc_x = test_zone_x * zw + test_point_x  # relativo 
        calc_y = test_zone_y * zh + test_point_y
        
        calc_map_id = calc_y * 512 + calc_x
        
        if calc_map_id == verify_result:
            print(f"  ✓ zoneW={zw} COINCIDE! Zone({test_zone_x},{test_zone_y})")
            print(f"    Coords calculadas: ({calc_x}, {calc_y})")
            
            # Ahora calcular PointCode para (68, 185)
            target_zone_x = TARGET_X // zw
            target_zone_y = TARGET_Y // zh
            target_point_x = TARGET_X % zw
            target_point_y = TARGET_Y % zh
            target_zone_id = target_zone_y * zones_per_row + target_zone_x
            target_point_id = target_point_y * zw + target_point_x
            
            print(f"\n  [RESULTADO] PointCode para ({TARGET_X}, {TARGET_Y}):")
            print(f"    ZoneID = {target_zone_id} (0x{target_zone_id:04X})")
            print(f"    PointID = {target_point_id} (0x{target_point_id:02X})")
            
            # Verificar reversa
            rev_x = (target_zone_id % zones_per_row) * zw + (target_point_id % zw)
            rev_y = (target_zone_id // zones_per_row) * zh + (target_point_id // zw)
            print(f"    Verificación reversa: ({rev_x}, {rev_y})")
            
            # Guardar para la inyección
            with open("pointcode_result.txt", "w") as f:
                f.write(f"zone_id={target_zone_id}\n")
                f.write(f"point_id={target_point_id}\n")
                f.write(f"zone_w={zw}\n")
                f.write(f"zones_per_row={zones_per_row}\n")
            
            return target_zone_id, target_point_id
        else:
            # Probar con zonesPerRow basado en WorldMaxX
            world_max_x = bridge.read_memory(map_mgr_ptr + 0x1BA, "<H")[0]
            total_cols = world_max_x - world_ox
            zpr2 = total_cols // zw
            
            test_zone_x2 = 507 % zpr2
            test_zone_y2 = 507 // zpr2
            
            calc_x2 = test_zone_x2 * zw + test_point_x
            calc_y2 = test_zone_y2 * zh + test_point_y
            calc_map_id2 = calc_y2 * 512 + calc_x2
            
            if calc_map_id2 == verify_result:
                print(f"  ✓ zoneW={zw}, zonesPerRow={zpr2} COINCIDE!")
                print(f"    Coords: ({calc_x2}, {calc_y2})")
                
                target_zone_x = TARGET_X // zw
                target_zone_y = TARGET_Y // zh
                target_point_x = TARGET_X % zw
                target_point_y = TARGET_Y % zh
                target_zone_id = target_zone_y * zpr2 + target_zone_x
                target_point_id = target_point_y * zw + target_point_x
                
                print(f"\n  [RESULTADO] PointCode para ({TARGET_X}, {TARGET_Y}):")
                print(f"    ZoneID = {target_zone_id}")
                print(f"    PointID = {target_point_id}")
                return target_zone_id, target_point_id
    
    print("[!] No se pudo deducir el tamaño de zona.")
    return None, None

if __name__ == "__main__":
    resolve_and_inject()
