"""
DEBUG: Verificar si el paquete se construye y se envía correctamente
"""
import ctypes, struct
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def read_remote(h, a, s):
    b = ctypes.create_string_buffer(s)
    kernel32.ReadProcessMemory(h, ctypes.c_void_p(a), b, s, None)
    return b.raw

def resolve_export(h, base, name):
    dos = read_remote(h, base, 64)
    elf = struct.unpack_from("<I", dos, 0x3C)[0]
    pe = read_remote(h, base+elf, 264)
    erva = struct.unpack_from("<I", pe, 24+112)[0]
    if not erva: return 0
    ed = read_remote(h, base+erva, 40)
    nf,nn = struct.unpack_from("<II", ed, 20)
    at,nt,ot = struct.unpack_from("<III", ed, 28)
    nps = read_remote(h, base+nt, nn*4)
    ords = read_remote(h, base+ot, nn*2)
    addrs = read_remote(h, base+at, nf*4)
    t = name.encode("ascii")
    for i in range(nn):
        nr = struct.unpack_from("<I", nps, i*4)[0]
        nb = read_remote(h, base+nr, 128).split(b"\x00")[0]
        if nb == t:
            o = struct.unpack_from("<H", ords, i*2)[0]
            return base + struct.unpack_from("<I", addrs, o*4)[0]
    return 0

def main():
    print("="*55)
    print("  DEBUG: Construir MP y leer su contenido")
    print("="*55)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    il2cpp_new = resolve_export(bridge.handle, base, "il2cpp_object_new")
    guest = bridge.call_rva(0x1D22900)
    klass = bridge.read_ptr(guest)
    
    # Crear nuevo MP
    new_mp = bridge.call_rva(il2cpp_new - base, [klass])
    bridge.call_rva(0x1D238A0, [new_mp, 1024])  # .ctor
    
    print(f"[+] Nuevo MP: 0x{new_mp:X}")
    
    # Leer estructura completa del MP
    print("\n[DEBUG] Campos del MessagePacket:")
    offset_val = bridge.read_memory(new_mp + 0x10, "<I")
    save_offset = bridge.read_memory(new_mp + 0x14, "<I")
    length_val = bridge.read_memory(new_mp + 0x18, "<I")
    channel = bridge.read_memory(new_mp + 0x1C, "B")
    delimiter = bridge.read_memory(new_mp + 0x20, "<I")
    max_size = bridge.read_memory(new_mp + 0x24, "<I")
    data_ptr = bridge.read_ptr(new_mp + 0x28)
    protocol = bridge.read_memory(new_mp + 0x30, "<H")
    
    print(f"  Offset:     {offset_val[0] if offset_val else '?'}")
    print(f"  SaveOffset: {save_offset[0] if save_offset else '?'}")
    print(f"  Length:     {length_val[0] if length_val else '?'}")
    print(f"  Channel:   {channel[0] if channel else '?'}")
    print(f"  Delimiter: {delimiter[0] if delimiter else '?'}")
    print(f"  MaxSize:   {max_size[0] if max_size else '?'}")
    print(f"  Data ptr:  0x{data_ptr:X}")
    print(f"  Protocol:  {protocol[0] if protocol else '?'}")
    
    # Ahora leer el GUEST MP para comparar
    print("\n[DEBUG] Campos del GUEST MessagePacket:")
    g_offset = bridge.read_memory(guest + 0x10, "<I")
    g_channel = bridge.read_memory(guest + 0x1C, "B")
    g_delimiter = bridge.read_memory(guest + 0x20, "<I")
    g_max = bridge.read_memory(guest + 0x24, "<I")
    g_data = bridge.read_ptr(guest + 0x28)
    g_proto = bridge.read_memory(guest + 0x30, "<H")
    
    print(f"  Offset:     {g_offset[0] if g_offset else '?'}")
    print(f"  Channel:   {g_channel[0] if g_channel else '?'}")
    print(f"  Delimiter: {g_delimiter[0] if g_delimiter else '?'}")
    print(f"  MaxSize:   {g_max[0] if g_max else '?'}")
    print(f"  Data ptr:  0x{g_data:X}")
    print(f"  Protocol:  {g_proto[0] if g_proto else '?'}")
    
    # El dato clave: ¿existen MÁS MessagePackets en el sistema?
    # Tal vez el juego usa un pool fijo de MessagePackets
    # y yo necesito usar UNO del pool, no crear uno nuevo.
    
    # Verificar si hay un Singleton/Pool de MPs
    # NetworkManager tiene SendBuff (Queue) en static offset 0x80
    nm_klass_ptr = bridge.call_rva(0x1D2CD40)
    nm_klass = bridge.read_ptr(nm_klass_ptr)
    sf_ptr = bridge.read_ptr(nm_klass + 0xB8)
    
    print(f"\n[DEBUG] NetworkManager static fields: 0x{sf_ptr:X}")
    
    # SendBuff = Queue at offset 0x80
    send_buff = bridge.read_ptr(sf_ptr + 0x80)
    # Sending = bool at 0x90
    sending = bridge.read_memory(sf_ptr + 0x90, "B")
    # Sequence = int at 0x11C (pero esto es del NM instance)
    sequence = bridge.read_memory(sf_ptr + 0x11C, "<I")
    
    print(f"  SendBuff Queue: 0x{send_buff:X}")
    print(f"  Sending: {sending[0] if sending else '?'}")
    
    # Probar: ¿Qué pasa si seteo Protocol ANTES del .ctor?
    # Quizás .ctor lo resetea
    
    # Setear protocol
    import ctypes as ct
    pv = ct.c_ushort(2415)
    kernel32.WriteProcessMemory(bridge.handle, ct.c_void_p(new_mp + 0x30), ct.byref(pv), 2, None)
    
    # Verificar que se escribió
    proto_check = bridge.read_memory(new_mp + 0x30, "<H")
    print(f"\n[CHECK] Protocol después de escribir: {proto_check[0] if proto_check else '?'}")
    
    # Agregar datos via Add
    bridge.call_rva(0x1D224A0, [new_mp, 372])  # zoneID
    bridge.call_rva(0x1D22860, [new_mp, 36])   # pointID
    bridge.call_rva(0x1D22860, [new_mp, 0])    # heroCount=0
    bridge.call_rva(0x1D22860, [new_mp, 1])    # tierCount=1
    for v in [1, 0, 0, 0]: 
        bridge.call_rva(0x1D22430, [new_mp, v])
    bridge.call_rva(0x1D22860, [new_mp, 0])    # petCount=0
    
    # Leer el contenido del buffer después de Add
    new_offset = bridge.read_memory(new_mp + 0x10, "<I")
    data_buf = bridge.read_ptr(new_mp + 0x28) 
    
    print(f"\n[DEBUG] Después de Add:")
    print(f"  Offset (bytes escritos): {new_offset[0] if new_offset else '?'}")
    print(f"  Protocol: {bridge.read_memory(new_mp + 0x30, '<H')[0]}")
    
    if data_buf and new_offset:
        # Buffer<byte> tiene: offset(4) + count(4) + outlaw(1) + Data(ptr)
        # En x64 con alineación: offset=0x10, count=0x14, outlaw=0x18, Data=0x20
        inner_data = bridge.read_ptr(data_buf + 0x10)
        if inner_data:
            raw = read_remote(bridge.handle, inner_data + 0x20, new_offset[0])
            print(f"  Datos raw ({new_offset[0]} bytes):")
            hex_str = " ".join(f"{b:02X}" for b in raw)
            print(f"    {hex_str}")
    
    # También intentar leer el Data directamente desde el Buffer<byte>
    # Buffer<byte> fields: readonly int offset(0x10), readonly int count(0x14), 
    # readonly bool outlaw(0x18), T[] Data(0x20 en x64?)
    # Actually for a class, fields start at 0x10:
    # 0x10: offset (int)
    # 0x14: count (int)
    # 0x18: outlaw (bool)
    # 0x20: Data (T[] array pointer)
    
    buf_offset = bridge.read_memory(data_buf + 0x10, "<I")
    buf_count = bridge.read_memory(data_buf + 0x14, "<I") 
    buf_outlaw = bridge.read_memory(data_buf + 0x18, "B")
    buf_arr = bridge.read_ptr(data_buf + 0x20)
    
    print(f"\n  Buffer<byte>:")
    print(f"    offset: {buf_offset[0] if buf_offset else '?'}")
    print(f"    count: {buf_count[0] if buf_count else '?'}")
    print(f"    outlaw: {buf_outlaw[0] if buf_outlaw else '?'}")
    print(f"    Data[]: 0x{buf_arr:X}")
    
    if buf_arr:
        arr_len = bridge.read_memory(buf_arr + 0x18, "<I")
        print(f"    Data[] len: {arr_len[0] if arr_len else '?'}")
        raw2 = read_remote(bridge.handle, buf_arr + 0x20, min(64, new_offset[0] if new_offset else 32))
        print(f"    Raw: {' '.join(f'{b:02X}' for b in raw2)}")

if __name__ == "__main__":
    main()
