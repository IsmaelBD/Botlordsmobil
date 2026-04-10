"""
==========================================================
  INTERCEPTOR DE MARCHA v3 - Resolución IL2CPP Correcta
  
  Estrategia: 
  1. Resolver il2cpp_object_new via PE exports de GameAssembly.dll
  2. Crear un MessagePacket real del canal de juego
  3. Construir paquete 2415 con formato correcto
  4. Enviar via MessagePacket.Send()
==========================================================
"""
import ctypes
import struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

TARGET_ZONE_ID = 372
TARGET_POINT_ID = 36

def read_remote(handle, addr, size):
    """Lee bytes del proceso remoto."""
    buf = ctypes.create_string_buffer(size)
    kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, size, None)
    return buf.raw

def resolve_export(handle, dll_base, func_name):
    """Resuelve una función exportada parseando el PE header remoto."""
    # Leer DOS header
    dos = read_remote(handle, dll_base, 64)
    e_lfanew = struct.unpack_from("<I", dos, 0x3C)[0]
    
    # Leer PE header
    pe = read_remote(handle, dll_base + e_lfanew, 264)
    # Optional header offset: 24 bytes after PE signature
    # Export directory RVA is at optional_header + 112 (for PE32+)
    export_rva = struct.unpack_from("<I", pe, 24 + 112)[0]
    export_size = struct.unpack_from("<I", pe, 24 + 116)[0]
    
    if export_rva == 0:
        return 0
    
    # Leer export directory
    export_dir = read_remote(handle, dll_base + export_rva, 40)
    num_functions = struct.unpack_from("<I", export_dir, 20)[0]
    num_names = struct.unpack_from("<I", export_dir, 24)[0]
    addr_table_rva = struct.unpack_from("<I", export_dir, 28)[0]
    name_table_rva = struct.unpack_from("<I", export_dir, 32)[0]
    ordinal_table_rva = struct.unpack_from("<I", export_dir, 36)[0]
    
    # Leer tablas
    name_ptrs = read_remote(handle, dll_base + name_table_rva, num_names * 4)
    ordinals = read_remote(handle, dll_base + ordinal_table_rva, num_names * 2)
    addrs = read_remote(handle, dll_base + addr_table_rva, num_functions * 4)
    
    target = func_name.encode("ascii")
    
    for i in range(num_names):
        name_rva = struct.unpack_from("<I", name_ptrs, i * 4)[0]
        name_bytes = read_remote(handle, dll_base + name_rva, 128)
        name = name_bytes.split(b"\x00")[0]
        
        if name == target:
            ordinal = struct.unpack_from("<H", ordinals, i * 2)[0]
            func_rva = struct.unpack_from("<I", addrs, ordinal * 4)[0]
            return dll_base + func_rva
    
    return 0

def main():
    print("="*60)
    print("  INTERCEPTOR v3 - Resolución IL2CPP + Inyección")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    dm_ptr = bridge.call_rva(0x2914F50)
    print(f"[+] DataManager: 0x{dm_ptr:X}")
    
    # ============================================================
    # PASO 1: Resolver exportaciones IL2CPP
    # ============================================================
    print("\n[*] Resolviendo exportaciones de GameAssembly.dll...")
    
    il2cpp_object_new = resolve_export(bridge.handle, bridge.base, "il2cpp_object_new")
    il2cpp_class_from_name = resolve_export(bridge.handle, bridge.base, "il2cpp_class_from_name")
    il2cpp_domain_get = resolve_export(bridge.handle, bridge.base, "il2cpp_domain_get")
    il2cpp_domain_get_assemblies = resolve_export(bridge.handle, bridge.base, "il2cpp_domain_get_assemblies")
    
    print(f"    il2cpp_object_new:        0x{il2cpp_object_new:X}")
    print(f"    il2cpp_class_from_name:   0x{il2cpp_class_from_name:X}")
    print(f"    il2cpp_domain_get:        0x{il2cpp_domain_get:X}")
    
    if not il2cpp_object_new:
        print("[!] No se pudo resolver il2cpp_object_new")
        return
    
    # ============================================================
    # PASO 2: Obtener la klass de MessagePacket
    # ============================================================
    # Alternativa más simple: leer la klass desde un MP existente
    # GetGuestMessagePack retorna un MP válido - su klass es la misma
    print("\n[*] Obteniendo klass de MessagePacket...")
    
    guest_mp = bridge.call_rva(0x1D22900)  # GetGuestMessagePack
    if not guest_mp:
        print("[!] GetGuestMessagePack falló")
        return
    
    # En IL2CPP, el primer campo del objeto (offset 0x0) es el puntero a la klass
    mp_klass = bridge.read_ptr(guest_mp)
    print(f"    Guest MP: 0x{guest_mp:X}")
    print(f"    MP Klass: 0x{mp_klass:X}")
    
    # ============================================================
    # PASO 3: Crear un MessagePacket nuevo y limpio
    # ============================================================
    print("\n[*] Creando MessagePacket nuevo via il2cpp_object_new...")
    
    # Llamar il2cpp_object_new(klass) -> retorna puntero a nuevo objeto
    new_mp = bridge.call_rva(
        il2cpp_object_new - bridge.base,  # Convertir a RVA
        [mp_klass]
    )
    
    if not new_mp:
        print("[!] il2cpp_object_new falló")
        return
    
    print(f"    Nuevo MP: 0x{new_mp:X}")
    
    # Llamar .ctor(ushort Max = 1024)
    # RVA: 0x1D238A0
    # this = new_mp (rcx), Max = 1024 (rdx)
    bridge.call_rva(0x1D238A0, [new_mp, 1024])
    print(f"    .ctor(1024) llamado ✓")
    
    # Verificar Channel del nuevo MP vs guest
    guest_channel = bridge.read_memory(guest_mp + 0x1C, "B")
    new_channel = bridge.read_memory(new_mp + 0x1C, "B")
    print(f"    Guest Channel: {guest_channel[0] if guest_channel else '?'}")
    print(f"    New MP Channel (antes): {new_channel[0] if new_channel else '?'}")
    
    # CORRECCIÓN CRÍTICA: Setear Channel = 1 (canal de juego activo)
    import ctypes as ct
    channel_val = ct.c_byte(1)
    kernel32.WriteProcessMemory(
        bridge.handle, ct.c_void_p(new_mp + 0x1C),
        ct.byref(channel_val), 1, None
    )
    print(f"    Channel corregido a 1 ✓")
    
    # ============================================================
    # PASO 4: Construir el paquete de marcha (Protocolo 2415)
    # ============================================================
    print(f"\n[*] Construyendo paquete de marcha...")
    print(f"    Destino: Zone={TARGET_ZONE_ID}, Point={TARGET_POINT_ID}")
    
    # Setear Protocol = 2415 en MP+0x30
    # Protocol es un ushort en offset 0x30
    import ctypes as ct
    protocol_val = ct.c_ushort(2415)
    kernel32.WriteProcessMemory(
        bridge.handle, ct.c_void_p(new_mp + 0x30),
        ct.byref(protocol_val), 2, None
    )
    
    # Llamar AddSeqId() - RVA: 0x1D22110
    bridge.call_rva(0x1D22110, [new_mp])
    
    # Añadir PointCode: zoneID (ushort) + pointID (byte)
    bridge.call_rva(0x1D224A0, [new_mp, TARGET_ZONE_ID])  # Add(ushort zoneID)
    bridge.call_rva(0x1D22860, [new_mp, TARGET_POINT_ID])  # Add(byte pointID)
    
    # Ahora necesitamos leer qué héroes y tropas tiene el jugador
    # Leeremos de la marcha activa (la que el usuario acaba de enviar)
    march_array_ptr = bridge.read_ptr(dm_ptr + 0x1078)
    array_len = bridge.read_memory(march_array_ptr + 0x18, "<I")[0]
    items_base = march_array_ptr + 0x20
    
    # Buscar la primera marcha activa para clonar sus datos
    STRIDE = 0x50
    cloned = False
    
    for i in range(min(array_len, 8)):
        base = items_base + (i * STRIDE)
        type_data = bridge.read_memory(base + 0x0, "<I")
        march_type = type_data[0] if type_data else 0
        if march_type == 0: continue
        
        print(f"\n[*] Clonando datos de Marcha #{i} (Type={march_type})...")
        
        # Leer héroes
        hero_arr_ptr = bridge.read_ptr(base + 0x08)
        heroes = []
        if hero_arr_ptr:
            hero_count = bridge.read_memory(hero_arr_ptr + 0x18, "<I")[0]
            for h in range(min(hero_count, 5)):
                hid = bridge.read_memory(hero_arr_ptr + 0x20 + (h * 2), "<H")
                if hid: heroes.append(hid[0])
        
        # Filtrar héroes válidos (>0)
        active_heroes = [h for h in heroes if h > 0]
        print(f"    Héroes a clonar: {active_heroes}")
        
        # Añadir heroCount
        bridge.call_rva(0x1D22860, [new_mp, len(active_heroes)])
        # Añadir cada heroID
        for hid in active_heroes:
            bridge.call_rva(0x1D224A0, [new_mp, hid])
        
        # Leer tropas
        troop_arr_ptr = bridge.read_ptr(base + 0x10)
        if troop_arr_ptr:
            troop_tiers = bridge.read_memory(troop_arr_ptr + 0x18, "<I")[0]
            
            # Solo enviar T1-T4 (los primeros 4 tiers, 1 tropa para test)
            send_tiers = min(troop_tiers, 4)
            bridge.call_rva(0x1D22860, [new_mp, send_tiers])  # tierCount
            
            for t in range(send_tiers):
                inner_ptr = bridge.read_ptr(troop_arr_ptr + 0x20 + (t * 8))
                if inner_ptr:
                    inner_len = bridge.read_memory(inner_ptr + 0x18, "<I")[0]
                    for s in range(min(inner_len, 4)):
                        val = bridge.read_memory(inner_ptr + 0x20 + (s * 4), "<I")
                        v = val[0] if val else 0
                        # Para test: solo 1 tropa del primer tipo
                        if t == 0 and s == 0:
                            v = 1  # 1 tropa de prueba
                        else:
                            v = 0
                        bridge.call_rva(0x1D22430, [new_mp, v])
                        
            print(f"    Tropas: {send_tiers} tiers, 1 unidad de prueba")
        
        # Añadir petCount = 0
        bridge.call_rva(0x1D22860, [new_mp, 0])
        
        cloned = True
        break
    
    if not cloned:
        print("[!] No hay marcha activa. Usando formato mínimo...")
        # Enviar sin héroe, 1 tier, 1 tropa
        bridge.call_rva(0x1D22860, [new_mp, 0])  # heroCount = 0
        bridge.call_rva(0x1D22860, [new_mp, 1])  # tierCount = 1  
        bridge.call_rva(0x1D22430, [new_mp, 1])  # Infantry = 1
        bridge.call_rva(0x1D22430, [new_mp, 0])  # Ranged = 0
        bridge.call_rva(0x1D22430, [new_mp, 0])  # Cavalry = 0
        bridge.call_rva(0x1D22430, [new_mp, 0])  # Siege = 0
        bridge.call_rva(0x1D22860, [new_mp, 0])  # petCount = 0
        print("    Formato mínimo: 0 hero, 1 infantry")
    
    # ============================================================
    # PASO 5: Enviar el paquete
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  ⚠️  PAQUETE LISTO PARA ENVIAR")
    print(f"  Destino: Mineral (68, 185)")
    print(f"  Héroes clonados de marcha activa")
    print(f"  Tropas: 1 unidad de prueba")
    print(f"{'='*60}")
    
    confirm = input("\n¿Enviar? (s/n): ").strip().lower()
    if confirm != 's':
        print("[*] Cancelado.")
        return
    
    # Llamar MessagePacket.Send(false) - RVA: 0x1D23440
    result = bridge.call_rva(0x1D23440, [new_mp, 0])
    
    print(f"[+] Send() resultado: {result}")
    print(f"\n🎯 Paquete enviado. Verifica en el juego.")

if __name__ == "__main__":
    main()
