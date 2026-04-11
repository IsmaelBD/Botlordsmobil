"""
PACKET HOOK - Interceptor Inline para MessagePacket.Send
Esto intercepta la llamada original, copia los paquetes 2415/6615 crudos,
y luego ejecuta el código original para que el juego no falle.
"""
import ctypes, struct, time
from internal_bridge import InternalBridge
from mem_radar import MemoryRadar

kernel32 = ctypes.windll.kernel32

def main():
    print("="*60)
    print("  PACKET HOOK - Interceptando MessagePacket.Send")
    print("="*60)
    
    radar = MemoryRadar()
    if not radar.clients: return
    c = radar.clients[0]
    bridge = InternalBridge(c["pid"], c["assembly_base"])
    base = bridge.base
    
    mp_send = base + 0x1D23440
    ret_addr = mp_send + 0x68
    
    # 1. Asignar memoria para Code Cave (RX) y Shared Buffer (RW)
    r_mem = kernel32.VirtualAllocEx(bridge.handle, 0, 8192, 0x3000, 0x40)
    shared_buf = r_mem + 4096
    
    print(f"[+] Hook Memory: 0x{r_mem:X}")
    print(f"[+] Shared Buffer: 0x{shared_buf:X}")
    
    # Escribir ceros al shared buffer por si acaso
    kernel32.WriteProcessMemory(bridge.handle, shared_buf, bytes(1024), 1024, None)
    
    # Construir Code Cave
    sc = bytearray()
    
    # cmp word [rcx+0x30], 2415
    sc += b"\x66\x81\x79\x30\x6F\x09"
    # je save_packet (+8)
    sc += b"\x74\x08"
    # cmp word [rcx+0x30], 6615
    sc += b"\x66\x81\x79\x30\xD7\x19"
    # jne execute_original (+42 = 0x2A)
    sc += b"\x75\x2A"
    
    # save_packet:
    sc += b"\x50\x56\x57\x51" # push rax, rsi, rdi, rcx
    
    # mov eax, [rcx+0x18]
    sc += b"\x8B\x41\x18"
    
    # mov rdi, SHARED_ADDR
    sc += b"\x48\xBF" + struct.pack("<Q", shared_buf)
    
    # mov [rdi], eax
    sc += b"\x89\x07"
    
    # cmp eax, 1000
    sc += b"\x3D\xE8\x03\x00\x00"
    # jle do_copy (+5)
    sc += b"\x7E\x05"
    # mov eax, 1000
    sc += b"\xB8\xE8\x03\x00\x00"
    
    # do_copy:
    # mov rsi, [rcx+0x28]
    sc += b"\x48\x8B\x71\x28"
    # add rsi, 0x20
    sc += b"\x48\x83\xC6\x20"
    # add rdi, 8
    sc += b"\x48\x83\xC7\x08"
    # mov ecx, eax
    sc += b"\x89\xC1"
    # rep movsb
    sc += b"\xF3\xA4"
    
    # pop rcx, rdi, rsi, rax
    sc += b"\x59\x5F\x5E\x58"
    
    # execute_original:
    sc += b"\x48\x89\x5C\x24\x20"  # mov [rsp+20h], rbx
    sc += b"\x57"                  # push rdi
    sc += b"\x48\x83\xEC\x30"      # sub rsp, 30h
    sc += b"\x48\x8B\xF9"          # mov rdi, rcx
    sc += b"\x0F\xB6\xDA"          # movzx ebx, dl
    
    # jmp RETURN_ADDR
    sc += b"\x48\xB8" + struct.pack("<Q", ret_addr)
    sc += b"\xFF\xE0"
    
    # Escribir Code Cave
    kernel32.WriteProcessMemory(bridge.handle, r_mem, bytes(sc), len(sc), None)
    
    # Construir Salto Original (Absolute JMP) = 14 bytes
    # FF 25 00 00 00 00 <8-bytes addr>
    jmp_sc = b"\xFF\x25\x00\x00\x00\x00" + struct.pack("<Q", r_mem)
    
    # ESCRIBIR JUMP HOOK
    kernel32.WriteProcessMemory(bridge.handle, mp_send, jmp_sc, len(jmp_sc), None)
    
    print("\n[+] HOOK INSTALADO! Envía la marcha en el juego...")
    
    # Bucle de escucha
    while True:
        try:
            r = ctypes.create_string_buffer(4)
            kernel32.ReadProcessMemory(bridge.handle, ctypes.c_void_p(shared_buf), r, 4, None)
            length = struct.unpack_from("<I", r.raw)[0]
            
            if length > 0:
                print(f"\n[🚀] ¡MÁGIA! Paquete atrapado. Length: {length} bytes")
                data_buf = read_remote(bridge.handle, shared_buf + 8, length)
                
                # Print hex
                hex_str = " ".join(f"{b:02X}" for b in data_buf)
                print(f"RAW HEX: \n{hex_str}")
                
                # Decodificar
                print("\n[Estructura Inferida]")
                pos = 0
                if length >= 2:
                    zone = struct.unpack_from("<H", data_buf, pos)[0]; pos += 2
                    print(f"ZoneID: {zone}")
                if length >= pos+1:
                    pt = struct.unpack_from("B", data_buf, pos)[0]; pos += 1
                    print(f"PointID: {pt}")
                if length >= pos+1:
                    hc = struct.unpack_from("B", data_buf, pos)[0]; pos += 1
                    print(f"HeroCount: {hc}")
                    for i in range(hc):
                        if length >= pos+2:
                            hid = struct.unpack_from("<H", data_buf, pos)[0]; pos += 2
                            print(f"  Hero: {hid}")
                
                print(f"Resto de bytes [{length - pos}]:")
                rest_hex = " ".join(f"{b:02X}" for b in data_buf[pos:])
                print(rest_hex)
                
                # Limpiar el trigger para esperar otro
                kernel32.WriteProcessMemory(bridge.handle, shared_buf, bytes(4), 4, None)
                
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
            
    # Restaurar original? Lo dejaremos así o crashea al cerrar, pero para leer está bien.
    print("[*] Saliendo...")

if __name__ == "__main__":
    main()
