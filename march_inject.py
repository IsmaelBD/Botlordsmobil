"""
==========================================================
  INYECTOR DE MARCHA v2 - Usando funciones internas del juego
  Objetivo: Mineral en (68, 185) con 1 tropa
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

def inject_march_v2():
    print("="*60)
    print("  INYECTOR DE MARCHA v2 - Mineral (68, 185)")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    dm_ptr = bridge.call_rva(0x2914F50)
    map_mgr_ptr = bridge.call_rva(0x2915080)
    
    print(f"[+] DataManager: 0x{dm_ptr:X}")
    print(f"[+] MapManager:  0x{map_mgr_ptr:X}")
    
    # ============================================================
    # PASO 1: PointCode resuelto por deduce_pointcode.py
    # ============================================================
    zone_id = 372
    point_id = 36
    
    print(f"\n[+] PointCode verificado para ({TARGET_X}, {TARGET_Y}):")
    print(f"    ZoneID = {zone_id}, PointID = {point_id}")
    
    # ============================================================
    # PASO 2: Construir y enviar el paquete de marcha
    # ============================================================
    # Vamos a construir shellcode completo que:
    # 1. Llama MessagePacket.GetGuestMessagePack() para obtener un MP válido
    #    RVA: 0x1D22900 (static, retorna MessagePacket*)
    # 2. Escribe Protocol = 2415 directamente en MP+0x30
    # 3. Llama MP.Add() para cada campo
    # 4. Llama MP.Send()
    
    print(f"\n[*] Construyendo shellcode de inyección de marcha...")
    
    base = bridge.base
    
    # Direcciones absolutas de las funciones
    addr_get_mp = base + 0x1D22900       # MessagePacket.GetGuestMessagePack() -> static
    addr_add_byte = base + 0x1D22860     # MP.Add(byte)
    addr_add_ushort = base + 0x1D224A0   # MP.Add(ushort)
    addr_add_uint = base + 0x1D22430     # MP.Add(uint)
    addr_mp_send = base + 0x1D23440      # MP.Send(bool Force=false)
    addr_add_seq = base + 0x1D22110      # MP.AddSeqId()
    
    # Alocar memoria remota para shellcode + buffer de retorno
    kernel32 = ctypes.windll.kernel32
    remote_mem = kernel32.VirtualAllocEx(
        bridge.handle, 0, 4096, 
        0x1000 | 0x2000,  # MEM_COMMIT | MEM_RESERVE
        0x40  # PAGE_EXECUTE_READWRITE
    )
    
    if not remote_mem:
        print("[!] Error al alocar memoria remota")
        return
    
    return_buf = remote_mem + 2048
    
    print(f"[+] Memoria remota: 0x{remote_mem:X}")
    
    # ============================================================
    # SHELLCODE x64 (FastCall convention)
    # ============================================================
    # El shellcode:
    # 1. sub rsp, 0x48 (shadow space + alignment)
    # 2. call GetGuestMessagePack() -> rax = MP*
    # 3. mov r12, rax (guardar MP)
    # 4. mov dword [r12+0x30], 2415 (Protocol = 2415)
    # 5. mov rcx, r12; mov dx, zoneID; call Add(ushort)
    # 6. mov rcx, r12; mov dl, pointID; call Add(byte) 
    # 7. mov rcx, r12; call AddSeqId()
    # 8. Añadir heroCount, heroes, troopData, etc.
    # 9. mov rcx, r12; xor edx, edx; call Send(false)
    # 10. add rsp, 0x48; ret
    
    sc = bytearray()
    
    # Prologue
    sc += b"\x48\x83\xEC\x48"         # sub rsp, 0x48
    sc += b"\x41\x54"                  # push r12
    
    # 1. Call GetGuestMessagePack (static)
    sc += b"\x48\xB8" + struct.pack("<Q", addr_get_mp)  # mov rax, addr
    sc += b"\xFF\xD0"                  # call rax
    sc += b"\x49\x89\xC4"             # mov r12, rax (save MP ptr)
    
    # 2. Write Protocol = 2415 at MP+0x30
    sc += b"\x41\xC7\x44\x24\x30"     # mov dword [r12+0x30], 2415
    sc += struct.pack("<I", 2415)
    
    # 3. Call AddSeqId(this=MP)
    sc += b"\x4C\x89\xE1"             # mov rcx, r12
    sc += b"\x48\xB8" + struct.pack("<Q", addr_add_seq)
    sc += b"\xFF\xD0"
    
    # 4. Add(ushort zoneID) - PointCode.zoneID
    sc += b"\x4C\x89\xE1"             # mov rcx, r12
    sc += b"\x66\xBA" + struct.pack("<H", zone_id)  # mov dx, zoneID
    sc += b"\x48\xB8" + struct.pack("<Q", addr_add_ushort)
    sc += b"\xFF\xD0"
    
    # 5. Add(byte pointID) - PointCode.pointID
    sc += b"\x4C\x89\xE1"             # mov rcx, r12
    sc += b"\xB2" + struct.pack("B", point_id)  # mov dl, pointID
    sc += b"\x48\xB8" + struct.pack("<Q", addr_add_byte)
    sc += b"\xFF\xD0"
    
    # 6. Add(byte heroCount = 0) - Sin héroe para test
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x00"                  # mov dl, 0
    sc += b"\x48\xB8" + struct.pack("<Q", addr_add_byte)
    sc += b"\xFF\xD0"
    
    # 7. Add(byte troopTierCount = 1) - Solo 1 tier
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x01"                  # mov dl, 1
    sc += b"\x48\xB8" + struct.pack("<Q", addr_add_byte)
    sc += b"\xFF\xD0"
    
    # 8. Add troopData para Tier 0: [1, 0, 0, 0] (1 infantería)
    for troop_count in [1, 0, 0, 0]:
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA" + struct.pack("<I", troop_count)  # mov edx, count
        sc += b"\x48\xB8" + struct.pack("<Q", addr_add_uint)
        sc += b"\xFF\xD0"
    
    # 9. Add(byte petCount = 0) - Sin mascotas
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x00"
    sc += b"\x48\xB8" + struct.pack("<Q", addr_add_byte)
    sc += b"\xFF\xD0"
    
    # 10. Call MP.Send(false)
    sc += b"\x4C\x89\xE1"             # mov rcx, r12 (this=MP)
    sc += b"\x31\xD2"                  # xor edx, edx (Force=false)
    sc += b"\x48\xB8" + struct.pack("<Q", addr_mp_send)
    sc += b"\xFF\xD0"
    
    # Guardar resultado en return_buf
    sc += b"\x48\xBB" + struct.pack("<Q", return_buf)
    sc += b"\x48\x89\x03"             # mov [rbx], rax
    
    # Epilogue
    sc += b"\x41\x5C"                  # pop r12
    sc += b"\x48\x83\xC4\x48"         # add rsp, 0x48
    sc += b"\xC3"                      # ret
    
    print(f"[+] Shellcode size: {len(sc)} bytes")
    
    # Escribir shellcode en memoria remota
    kernel32.WriteProcessMemory(
        bridge.handle, remote_mem, 
        bytes(sc), len(sc), None
    )
    
    print(f"\n{'='*60}")
    print(f"  ⚠️  LISTO PARA INYECTAR")
    print(f"  Destino: Mineral ({TARGET_X}, {TARGET_Y})")
    print(f"  PointCode: Zone={zone_id}, Point={point_id}")
    print(f"  Tropas: 1 infantería (test)")
    print(f"  Héroes: 0 (test mínimo)")
    print(f"{'='*60}")
    
    confirm = input("\n¿Ejecutar inyección? (s/n): ").strip().lower()
    if confirm != 's':
        print("[*] Inyección cancelada.")
        return
    
    # Ejecutar shellcode
    print("[*] Ejecutando inyección...")
    thread = kernel32.CreateRemoteThread(
        bridge.handle, None, 0, remote_mem, None, 0, None
    )
    
    if not thread:
        print("[!] Error al crear hilo remoto")
        return
    
    kernel32.WaitForSingleObject(thread, 10000)
    
    # Leer resultado
    ret_val = ctypes.c_ulonglong()
    kernel32.ReadProcessMemory(
        bridge.handle, ctypes.c_void_p(return_buf),
        ctypes.byref(ret_val), 8, None
    )
    
    kernel32.CloseHandle(thread)
    
    print(f"[+] Resultado: 0x{ret_val.value:X}")
    print(f"\n🎯 ¡Marcha inyectada! Verifica en el juego si las tropas se mueven.")

if __name__ == "__main__":
    inject_march_v2()
