"""
==========================================================
  INYECTOR v4 - Shellcode Monolítico (Todo en 1 hilo)
  
  PROBLEMA ANTERIOR: Cada call_rva usa CreateRemoteThread 
  separado, lo que puede corromper el estado del MessagePacket.
  
  SOLUCIÓN: Un único shellcode que construye y envía todo
  el paquete en una sola ejecución atómica.
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
    buf = ctypes.create_string_buffer(size)
    kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, size, None)
    return buf.raw

def resolve_export(handle, dll_base, func_name):
    dos = read_remote(handle, dll_base, 64)
    e_lfanew = struct.unpack_from("<I", dos, 0x3C)[0]
    pe = read_remote(handle, dll_base + e_lfanew, 264)
    export_rva = struct.unpack_from("<I", pe, 24 + 112)[0]
    if export_rva == 0: return 0
    export_dir = read_remote(handle, dll_base + export_rva, 40)
    num_functions = struct.unpack_from("<I", export_dir, 20)[0]
    num_names = struct.unpack_from("<I", export_dir, 24)[0]
    addr_table_rva = struct.unpack_from("<I", export_dir, 28)[0]
    name_table_rva = struct.unpack_from("<I", export_dir, 32)[0]
    ordinal_table_rva = struct.unpack_from("<I", export_dir, 36)[0]
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

def emit_call_abs(sc, addr):
    """Emite: mov rax, addr; call rax"""
    sc += b"\x48\xB8" + struct.pack("<Q", addr)
    sc += b"\xFF\xD0"
    return sc

def main():
    print("="*60)
    print("  INYECTOR v4 - Shellcode Monolítico")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    client = radar.clients[0]
    bridge = InternalBridge(client["pid"], client["assembly_base"])
    
    dm_ptr = bridge.call_rva(0x2914F50)
    base = bridge.base
    print(f"[+] DataManager: 0x{dm_ptr:X}")
    print(f"[+] Base: 0x{base:X}")
    
    # Resolver il2cpp_object_new
    il2cpp_object_new = resolve_export(bridge.handle, base, "il2cpp_object_new")
    print(f"[+] il2cpp_object_new: 0x{il2cpp_object_new:X}")
    
    # Obtener klass de MessagePacket
    guest_mp = bridge.call_rva(0x1D22900)
    mp_klass = bridge.read_ptr(guest_mp)
    print(f"[+] MP Klass: 0x{mp_klass:X}")
    
    # Leer marcha activa para clonar héroes
    march_array_ptr = bridge.read_ptr(dm_ptr + 0x1078)
    array_len_data = bridge.read_memory(march_array_ptr + 0x18, "<I")
    array_len = array_len_data[0] if array_len_data else 0
    items_base = march_array_ptr + 0x20
    
    heroes = []
    for i in range(min(array_len, 8)):
        mb = items_base + (i * 0x50)
        mt = bridge.read_memory(mb, "<I")
        if mt and mt[0] > 0:
            hero_arr = bridge.read_ptr(mb + 0x08)
            if hero_arr:
                hc = bridge.read_memory(hero_arr + 0x18, "<I")[0]
                for h in range(min(hc, 5)):
                    hid = bridge.read_memory(hero_arr + 0x20 + (h*2), "<H")
                    if hid and hid[0] > 0: heroes.append(hid[0])
            break
    
    print(f"[+] Héroes detectados: {heroes}")
    
    # Direcciones de funciones
    fn = {
        "obj_new":    il2cpp_object_new,
        "ctor":       base + 0x1D238A0,
        "add_seq":    base + 0x1D22110,
        "add_byte":   base + 0x1D22860,
        "add_ushort": base + 0x1D224A0,
        "add_uint":   base + 0x1D22430,
        "send":       base + 0x1D23440,
    }
    
    # Alocar memoria remota
    remote_mem = kernel32.VirtualAllocEx(bridge.handle, 0, 8192, 0x3000, 0x40)
    result_addr = remote_mem + 4096
    print(f"[+] Shellcode mem: 0x{remote_mem:X}")
    
    # ============================================================
    # CONSTRUIR SHELLCODE MONOLÍTICO
    # ============================================================
    # Convención: r12 = MessagePacket*, r13 = saved
    # Todas las funciones IL2CPP usan fastcall: rcx=this/arg1, rdx=arg2
    
    sc = bytearray()
    
    # Prologue - guardar registros no-volátiles
    sc += b"\x48\x83\xEC\x68"     # sub rsp, 0x68 (alineado a 16)
    sc += b"\x41\x54"              # push r12
    sc += b"\x41\x55"              # push r13
    
    # ---- PASO 1: il2cpp_object_new(mp_klass) ----
    sc += b"\x48\xB9" + struct.pack("<Q", mp_klass)  # mov rcx, mp_klass
    sc = emit_call_abs(sc, fn["obj_new"])
    sc += b"\x49\x89\xC4"         # mov r12, rax (guardar MP ptr)
    
    # ---- PASO 2: .ctor(this=MP, Max=1024) ----
    sc += b"\x4C\x89\xE1"         # mov rcx, r12
    sc += b"\xBA\x00\x04\x00\x00" # mov edx, 1024
    sc = emit_call_abs(sc, fn["ctor"])
    
    # ---- PASO 3: Escribir Channel = 1 en MP+0x1C ----
    sc += b"\x41\xC6\x44\x24\x1C\x01"  # mov byte [r12+0x1C], 1
    
    # ---- PASO 4: Escribir Protocol = 2415 en MP+0x30 ----
    sc += b"\x66\x41\xC7\x44\x24\x30"  # mov word [r12+0x30], 2415
    sc += struct.pack("<H", 2415)
    
    # (AddSeqId REMOVIDO - Send() lo hace internamente)
    
    # ---- PASO 5: Add(ushort zoneID) ----
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA" + struct.pack("<H", TARGET_ZONE_ID)
    sc = emit_call_abs(sc, fn["add_ushort"])
    
    # ---- PASO 7: Add(byte pointID) ----
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", TARGET_POINT_ID)
    sc = emit_call_abs(sc, fn["add_byte"])
    
    # ---- PASO 8: Add(byte heroCount) ----
    hero_count = min(len(heroes), 5)
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2" + struct.pack("B", hero_count)
    sc = emit_call_abs(sc, fn["add_byte"])
    
    # ---- PASO 9: Add each heroID (ushort) ----
    for hid in heroes[:5]:
        sc += b"\x4C\x89\xE1"
        sc += b"\x66\xBA" + struct.pack("<H", hid)
        sc = emit_call_abs(sc, fn["add_ushort"])
    
    # ---- PASO 10: Add(byte tierCount = 4) ----
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x04"              # 4 tiers
    sc = emit_call_abs(sc, fn["add_byte"])
    
    # ---- PASO 11: TroopData - 4 tiers x 4 tipos ----
    # Tier 0 (T1): [1, 0, 0, 0] - 1 infantería de prueba
    for count in [1, 0, 0, 0]:
        sc += b"\x4C\x89\xE1"
        sc += b"\xBA" + struct.pack("<I", count)
        sc = emit_call_abs(sc, fn["add_uint"])
    
    # Tiers 1-3 (T2-T4): [0, 0, 0, 0]
    for tier in range(3):
        for count in [0, 0, 0, 0]:
            sc += b"\x4C\x89\xE1"
            sc += b"\xBA\x00\x00\x00\x00"
            sc = emit_call_abs(sc, fn["add_uint"])
    
    # ---- PASO 12: Add(byte petCount = 0) ----
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x00"
    sc = emit_call_abs(sc, fn["add_byte"])
    
    # ---- PASO 13: MessagePacket.Send(false) ----
    sc += b"\x4C\x89\xE1"         # mov rcx, r12 (this=MP)
    sc += b"\x31\xD2"              # xor edx, edx (Force=false)
    sc = emit_call_abs(sc, fn["send"])
    
    # Guardar resultado
    sc += b"\x49\x89\xC5"         # mov r13, rax
    sc += b"\x48\xBB" + struct.pack("<Q", result_addr)
    sc += b"\x4C\x89\x2B"         # mov [rbx], r13
    
    # Epilogue
    sc += b"\x41\x5D"              # pop r13
    sc += b"\x41\x5C"              # pop r12
    sc += b"\x48\x83\xC4\x68"     # add rsp, 0x68
    sc += b"\xC3"                  # ret
    
    print(f"[+] Shellcode total: {len(sc)} bytes")
    
    # Escribir shellcode
    kernel32.WriteProcessMemory(bridge.handle, remote_mem, bytes(sc), len(sc), None)
    
    print(f"\n{'='*60}")
    print(f"  ⚠️  SHELLCODE MONOLÍTICO LISTO")
    print(f"  Destino: Mineral (68, 185)")
    print(f"  Zone={TARGET_ZONE_ID}, Point={TARGET_POINT_ID}")
    print(f"  Héroes: {heroes[:5]}")
    print(f"  Tropas: 1 infantería T1")
    print(f"  Channel: 1 (juego)")
    print(f"  Protocol: 2415")
    print(f"  Todo en 1 hilo atómico")
    print(f"{'='*60}")
    
    confirm = input("\n¿Ejecutar? (s/n): ").strip().lower()
    if confirm != 's':
        print("[*] Cancelado.")
        return
    
    print("[*] Ejecutando shellcode...")
    thread = kernel32.CreateRemoteThread(bridge.handle, None, 0, remote_mem, None, 0, None)
    if not thread:
        print(f"[!] CreateRemoteThread falló: {kernel32.GetLastError()}")
        return
    
    kernel32.WaitForSingleObject(thread, 15000)
    
    ret = ctypes.c_ulonglong()
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(result_addr), ctypes.byref(ret), 8, None)
    kernel32.CloseHandle(thread)
    
    print(f"[+] Send() retornó: 0x{ret.value:X}")
    print(f"\n🎯 Verifica en el juego.")

if __name__ == "__main__":
    main()
