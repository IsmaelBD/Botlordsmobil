"""
CALIBRADOR DE COORDENADAS v12
Llama a DataManager.get_CommanderLocation() para leer tus coordenadas internas.
Esto nos dará la clave para calcular el destino exacto (Zone/Point).
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def emit_call(sc, addr):
    sc += b"\x48\xB8" + struct.pack("<Q", addr)
    sc += b"\xFF\xD0"
    return sc

def main():
    print("="*60)
    print("  CALIBRADOR v12 - Localizando tu Castillo")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    # RVAs
    fn_get_instance = base + 0x2914F50
    fn_get_location = base + 0xD45A80
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    res_buf = rmem + 2048
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54\x41\x55"
    sc += b"\x49\xBD" + struct.pack("<Q", res_buf) # r13 = result_buf
    
    # 1. Obtener Instancia de DataManager
    sc = emit_call(sc, fn_get_instance)
    sc += b"\x48\x89\xC1" # rcx = DataManager Instance
    
    # 2. Llamar get_CommanderLocation()
    sc = emit_call(sc, fn_get_location)
    # rax contiene el PointCode (3 bytes útiles)
    sc += b"\x49\x89\x45\x00" # Guardar en result_buf
    
    sc += b"\x41\x5D\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 5000)
    kernel32.CloseHandle(t)
    
    # Leer el PointCode de la memoria
    r = ctypes.create_string_buffer(8)
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(res_buf), r, 8, None)
    
    # PointCode: ZoneID (ushort, 2 bytes), PointID (byte, 1 byte)
    zone, point = struct.unpack_from("<HB", r.raw, 0)
    print(f"\n[🏠] ¡CASTILLO LOCALIZADO EN MEMORIA!")
    print(f"    Coordenadas Internas -> ZoneID: {zone}, PointID: {point}")
    print(f"    Coordenadas Humanas  -> X:370, Y:492")
    
    # Guardar para el siguiente paso
    with open("d:\\BotLordsMobile\\castle_calibration.txt", "w") as f:
        f.write(f"{zone},{point}")
        
    print("\nCalculando desviación...")
    # Fórmula clásica: Zone = X//16 + (Y//16)*32. Point = X%16 + (Y%16)*16
    calc_zone = (370 // 16) + (492 // 16) * 32
    calc_point = (370 % 16) + (492 % 16) * 16
    print(f"    Zone v11 (esperada): {calc_zone}")
    print(f"    Point v11 (esperada): {calc_point}")
    
    if zone == calc_zone and point == calc_point:
        print("[!] ¡LA FÓRMULA v11 ES CORRECTA! El problema fue otro (¿AddSeqId? ¿Protocolo?).")
    else:
        print(f"[!] ¡DESVIACIÓN DETECTADA! Diferencia Zone: {zone - calc_zone}")
        print(f"    Usaremos Zone: {zone + 1015 - calc_zone} para la mina.")

if __name__ == "__main__":
    main()
