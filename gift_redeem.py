import socket
import struct

# --- DATOS SINCRONIZADOS ---
IGG_ID = "2129137494"
SESSION_KEY = "4d92c043efb7fe9effd66f4952815f8a"
SERVER_IP = "192.243.45.144"
PORT = 21977
NEXT_SEQUENCE = 3 # Tu secuencia actual (2) + 1
# ---------------------------

def igg_cipher(data, key_str, seq):
    """Cifrado XOR circular sincronizado con el número de secuencia del juego."""
    key = key_str.encode('ascii')
    res = bytearray()
    for i in range(len(data)):
        # La secuencia suele ser una semilla para el XOR
        res.append(data[i] ^ (key[i % len(key)] ^ (seq & 0xFF)))
    return res

def build_authenticated_packet(idd, code, skey, seq):
    payload = bytearray()
    payload.extend(struct.pack("<Q", int(idd)))
    payload.extend(code.encode('utf-8').ljust(20, b'\x00'))
    payload.extend(skey.encode('utf-8').ljust(32, b'\x00'))
    
    opcode = 478
    # Cuerpo: [Secuencia (4 bytes)] [OpCode (2 bytes)] [Payload]
    body = struct.pack("<IH", seq, opcode) + payload
    
    encrypted_body = igg_cipher(body, skey, seq)
    
    # Paquete final: [Longitud (2 bytes)] [Cuerpo Cifrado]
    total_len = 2 + len(encrypted_body)
    return struct.pack("<H", total_len) + encrypted_body

def run_final_redeem():
    code = "LM2026"
    print(f"[*] --- LORDS MOBILE GIFT BOT v3 (SYNCED) ---")
    print(f"[*] Sincronizando con Secuencia #{NEXT_SEQUENCE}")
    
    packet = build_authenticated_packet(IGG_ID, code, SESSION_KEY, NEXT_SEQUENCE)
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((SERVER_IP, PORT))
            print(f"[*] Enviando ráfaga sincronizada...")
            s.sendall(packet)
            
            resp = s.recv(1024)
            if resp:
                print(f"[+] ¡EL SERVIDOR RESPONDIÓ!")
                print(f"[*] Hex: {resp.hex()}")
                # Descifrar respuesta para ver el resultado
                if len(resp) > 2:
                    dec = igg_cipher(resp[2:], SESSION_KEY, NEXT_SEQUENCE)
                    print(f"[*] Respuesta Descifrada: {dec.hex()}")
            else:
                print("[!] El servidor cerró la conexión. La secuencia pudo haber cambiado.")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    run_final_redeem()
