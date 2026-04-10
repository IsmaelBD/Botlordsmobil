"""
TEST MÍNIMO: Verificar si Add() funciona correctamente
dentro del shellcode (un solo hilo).
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
    print("="*55)
    print("  TEST: Verificar Add() en shellcode")
    print("="*55)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    fn_get_mp = base + 0x1D22900
    fn_add_byte = base + 0x1D22860
    fn_add_ushort = base + 0x1D224A0
    fn_send = base + 0x1D23440
    
    rmem = kernel32.VirtualAllocEx(bridge.handle, 0, 4096, 0x3000, 0x40)
    result_buf = rmem + 2048  # Buffer para guardar resultados
    
    # Shellcode que:
    # 1. GetGuestMessagePack() -> r12
    # 2. Lee Offset antes (MP+0x10) -> guarda en result_buf
    # 3. Setea Protocol = 2415
    # 4. Llama Add(byte, 0x42)
    # 5. Llama Add(ushort, 0x1234)
    # 6. Lee Offset después -> guarda en result_buf+8
    # 7. Lee Channel -> result_buf+16
    # 8. Llama Send(false) -> result_buf+24
    
    sc = bytearray()
    sc += b"\x48\x83\xEC\x48"
    sc += b"\x41\x54"
    sc += b"\x41\x55"
    
    # Guardar result_buf en r13
    sc += b"\x49\xBD" + struct.pack("<Q", result_buf)
    
    # 1. GetGuestMessagePack
    sc = emit_call(sc, fn_get_mp)
    sc += b"\x49\x89\xC4"  # r12 = MP
    
    # 2. Guardar MP ptr en result_buf[0]
    sc += b"\x4D\x89\x65\x00"  # mov [r13], r12
    
    # 3. Guardar Offset ANTES en result_buf[8]
    sc += b"\x41\x8B\x44\x24\x10"  # mov eax, [r12+0x10] (Offset)
    sc += b"\x41\x89\x45\x08"      # mov [r13+8], eax
    
    # 4. Setear Protocol = 2415
    sc += b"\x66\x41\xC7\x44\x24\x30"
    sc += struct.pack("<H", 2415)
    
    # 5. Add(byte 0x42) - rcx=MP, dl=0x42
    sc += b"\x4C\x89\xE1"
    sc += b"\xB2\x42"
    sc = emit_call(sc, fn_add_byte)
    
    # 6. Guardar retorno de Add en result_buf[16]
    sc += b"\x41\x89\x45\x10"
    
    # 7. Add(ushort 0x1234) 
    sc += b"\x4C\x89\xE1"
    sc += b"\x66\xBA\x34\x12"
    sc = emit_call(sc, fn_add_ushort)
    
    # 8. Guardar Offset DESPUÉS en result_buf[24]
    sc += b"\x41\x8B\x44\x24\x10"
    sc += b"\x41\x89\x45\x18"
    
    # 9. Guardar Length en result_buf[32]
    sc += b"\x41\x8B\x44\x24\x18"  # Length at MP+0x18
    sc += b"\x41\x89\x45\x20"
    
    # 10. Guardar Channel en result_buf[40]
    sc += b"\x41\x0F\xB6\x44\x24\x1C"  # movzx eax, byte [r12+0x1C]
    sc += b"\x41\x89\x45\x28"
    
    # 11. Guardar Delimiter en result_buf[48]
    sc += b"\x41\x8B\x44\x24\x20"
    sc += b"\x41\x89\x45\x30"
    
    # 12. Llamar Send(false) y guardar resultado
    sc += b"\x4C\x89\xE1"  # rcx = MP
    sc += b"\x31\xD2"       # edx = 0 (false)
    sc = emit_call(sc, fn_send)
    sc += b"\x41\x89\x45\x38"  # result_buf[56] = send result
    
    # 13. Guardar Offset POST-SEND en result_buf[64]
    sc += b"\x41\x8B\x44\x24\x10"
    sc += b"\x41\x89\x45\x40"
    
    sc += b"\x41\x5D"
    sc += b"\x41\x5C"
    sc += b"\x48\x83\xC4\x48"
    sc += b"\xC3"
    
    kernel32.WriteProcessMemory(bridge.handle, rmem, bytes(sc), len(sc), None)
    
    print(f"[+] Shellcode: {len(sc)} bytes")
    print("[*] Ejecutando test...")
    
    t = kernel32.CreateRemoteThread(bridge.handle, None, 0, rmem, None, 0, None)
    kernel32.WaitForSingleObject(t, 15000)
    kernel32.CloseHandle(t)
    
    # Leer resultados
    results = ctypes.create_string_buffer(128)
    kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(result_buf), results, 128, None)
    raw = results.raw
    
    mp_ptr = struct.unpack_from("<Q", raw, 0)[0]
    offset_before = struct.unpack_from("<I", raw, 8)[0]
    add_ret = struct.unpack_from("<I", raw, 16)[0]
    offset_after = struct.unpack_from("<I", raw, 24)[0]
    length_val = struct.unpack_from("<I", raw, 32)[0]
    channel = struct.unpack_from("<I", raw, 40)[0]
    delimiter = struct.unpack_from("<I", raw, 48)[0]
    send_ret = struct.unpack_from("<I", raw, 56)[0]
    offset_post_send = struct.unpack_from("<I", raw, 64)[0]
    
    print(f"\n  MP ptr:          0x{mp_ptr:X}")
    print(f"  Offset ANTES:    {offset_before}")
    print(f"  Add() retorno:   {add_ret}")
    print(f"  Offset DESPUÉS:  {offset_after}")
    print(f"  Length:          {length_val}")
    print(f"  Channel:         {channel}")
    print(f"  Delimiter:       {delimiter}")
    print(f"  Send() retorno:  {send_ret} (1=OK, 0=FAIL)")
    print(f"  Offset POST-SEND:{offset_post_send}")
    
    if offset_after > offset_before:
        print(f"\n  ✅ Add() FUNCIONA (escribió {offset_after - offset_before} bytes)")
    else:
        print(f"\n  ❌ Add() NO ESCRIBIÓ NADA")
    
    if send_ret == 1:
        print(f"  ✅ Send() retornó TRUE")
    else:
        print(f"  ❌ Send() retornó FALSE - paquete NO enviado")

if __name__ == "__main__":
    main()
