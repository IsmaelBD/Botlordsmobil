import socket
import struct
import time

def test_seed_offsets(oggid, session_key, udid, host, port):
    # Intentaremos los 16 posibles offsets de la llave de 16 bytes
    key_bytes = bytes.fromhex(session_key)
    
    for offset in range(16):
        print(f"[*] Probando Offset de Cifrado: {offset}...")
        
        def local_cipher(data, start_offset):
            out = bytearray(data)
            for i in range(len(out)):
                # Aplicamos el XOR rotando desde el offset indicado
                out[i] ^= key_bytes[(i + start_offset) % len(key_bytes)]
            return out

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((host, port))
                
                # Preparamos login con este offset
                session_bytes = session_key.encode('utf-16le')
                body_1043 = struct.pack("<Q", oggid) + struct.pack("<H", len(session_bytes)) + session_bytes
                body_1043_enc = local_cipher(body_1043, offset)
                
                # [Size(2)][OpCode(2)][Seq(4)][Body]
                size = 2+2+4+len(body_1043_enc)
                packet = struct.pack("<HHI", size, 1043, 1) + body_1043_enc
                
                s.sendall(packet)
                resp = s.recv(1024)
                if resp:
                    print(f"[!!!] ¡RESPUESTA RECIBIDA CON OFFSET {offset}!: {resp.hex()}")
                    return offset
        except:
            pass
        time.sleep(0.5)
    
    print("[!] Ningún offset de semilla funcionó. El problema podría ser la secuencia.")
    return None

if __name__ == "__main__":
    # Datos actuales
    IGGID = 2129137494
    KEY = "0f42e4173e047f002acf88d72897ad68"
    UDID = "eyJha2lkIjoyMDIxMDQy..."
    HOST = "205.252.125.129"
    PORT = 11977
    test_seed_offsets(IGGID, KEY, UDID, HOST, PORT)
