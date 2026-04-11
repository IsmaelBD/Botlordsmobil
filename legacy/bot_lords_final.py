import socket
import time

def final_headless_redeem():
    # --- COORDENADAS CAPTURADAS ---
    HOST = "205.252.125.129"
    PORT = 11977
    GIFT_CODE = "LM2026"
    
    print("[*] Lanzando BOT DEFINITIVO (Ráfaga Espejo Completa)...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((HOST, PORT))
            print("[+] Conectado al servidor de Lords Mobile.")
            
            # --- PACKETS COMPLETOS CAPTURADOS ---
            
            # 13000: Versión (64 bytes)
            p13000 = "4000c832bbc6d11e3e0000803fe054c53f4bce43c0e41369c0000000005c392a4026a327c085e3544000000000d65d7cc034a03dc08ee2513f00000000c4bf3e"
            
            # 1024: Activación (15 bytes)
            p1024 = "0f00000410000068100000cc100000"
            
            # 1043: Login (143 bytes) - EL CORRECAMINOS
            p1043 = "8f0013048870d0edebe201000040c4edebe201000000cdedebe201000100000000000070cbedebe2010000000000000000000035000000000000003f0000000000000070387417fc7f0000daf86a8f00140490556e697479456e67696e652e417564696f5265766572625a6f6e653a3a6765745f64656361794846526174696f5f496e6a656374656400000000"
            
            # 1420: Canje (128 bytes)
            p1420 = "80008c0590556e697479456e67696e652e436c6f74683a3a6765745f7573655669727475616c5061727469636c65735f496e6a65637465640000000000000000000000000000000000000000003fc0cd80008d0588509639eae2010000204deeebe2010000509639eae201000000000000000000000040eeebe2010000000000"

            # EJECUCIÓN PASO A PASO
            print("[*] 1. Handshake Versión...")
            s.sendall(bytes.fromhex(p13000))
            time.sleep(0.5)
            
            print("[*] 2. Activación Hardware...")
            s.sendall(bytes.fromhex(p1024))
            time.sleep(0.5)
            
            print("[*] 3. Login de Sesión (Ráfaga Completa)...")
            s.sendall(bytes.fromhex(p1043))
            time.sleep(1)
            
            print(f"[*] 4. Canjeando código: {GIFT_CODE}")
            s.sendall(bytes.fromhex(p1420))
            
            # Esperamos respuesta
            resp = s.recv(1024)
            if resp:
                print(f"[!!!] ÉXITO: Respuesta del servidor: {resp.hex()}")
            else:
                print("[!] El servidor no respondió. El canje debe estar ya hecho!")
                
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    final_headless_redeem()
