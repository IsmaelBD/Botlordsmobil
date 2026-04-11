import socket
import struct

# --- DATOS REALES INTERCEPTADOS ---
IGG_ID = "2129137494"
SESSION_KEY = "4d92c043efb7fe9effd66f4952815f8a"
UDID = "eyJha2lkIjoyMDIxMDQyMiwicmtpZCI6MjAyMTA0MjMsImciOjEwNTEwOTk5MDcsInYiOjN9.B5J-DO-jjcZRA6U2cleMp4Z-oOWanCPlmhMj4PRNrgymUOuoQa4777qR5Y-vGX0B-WZNR9zHTq9XGZuf0DdkCoY8TN_WQrBYCtBvDknGYZ5CiQCx3iG5rvZfL1rI_WPLhKHhosA4_uzb0FLqgAEgahVq0OrWk62001vcKL4dpBI.GT9aWbaMOfFVq0vnwJMWqNGBPoIDRQiuPTOeziHDCxAK9EtSMioqUY29pNvSxZ0bBUi7m6_utHmgyoAHCMOTRAqrDQ13nwduKvFlQwy2-YrV72EhD08J8j36ZlDeo-vDV5FgIk1sOpHiTXQlr6xRI23TcWbdupXQB5aep5SEZfc"
SERVER_IP = "192.243.45.144"
PORT = 21977
# ----------------------------------

def create_active_packet(udid_str):
    # OpCode 1024 (_MSG_REQUEST_ACTIVE)
    # Estructura observada: Longitud variable con el UDID
    udid_bytes = udid_str.encode('utf-16le') # IGG PC usa UTF-16 para strings largos
    opcode = 1024
    header_len = 2 + 2 
    payload = udid_bytes
    total_len = header_len + len(payload)
    
    return struct.pack("<HH", total_len, opcode) + payload

def run_headless_bot(gift_code):
    print(f"[*] --- LORDS MOBILE HEADLESS BOT ---")
    print(f"[*] Objetivo: {gift_code}")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(15)
            s.connect((SERVER_IP, PORT))
            
            # PASO 1: ACTIVACIÓN
            print("[*] Paso 1: Enviando paquete de activación (UDID)...")
            s.sendall(create_active_packet(UDID))
            
            # PASO 2: LOGIN (Emulado)
            # Aquí iría el OpCode 1043 si el servidor pide más auth
            
            # PASO 3: CANJE
            print(f"[*] Paso 3: Intentando canje de {gift_code}...")
            # ... (Cifrado XOR con SessionKey como vimos antes) ...
            
            print("[!] Bot en fase de pruebas. Paquete de activación enviado con éxito.")
            
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    run_headless_bot("LM2026")
