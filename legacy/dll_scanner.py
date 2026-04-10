import os

def scan_real_dll_for_xor():
    file_path = r"D:\Lords Mobile PC\Game\GameAssembly.dll"
    if not os.path.exists(file_path):
        print(f"[!] No se encontró el archivo en: {file_path}")
        return

    print(f"[*] Escaneando el Cerebro Real en {file_path}...")
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            
            # Buscando el OpCode 13000 (c8 32)
            pattern = b"\xC8\x32"
            idx = data.find(pattern)
            if idx != -1:
                print(f"[!!!] OpCode 13000 localizado en offset: {hex(idx)}")
                # Cerca de aquí debe estar la tabla de 256 bytes del cifrado
                # Vamos a volcar los bytes sospechosos alrededor
                context = data[idx-64:idx+256]
                print(f"  > HEX DATA: {context.hex()}")
                return
            
            print("[!] OpCode no encontrado en el archivo estático. Probable compresión.")

    except Exception as e:
        print(f"[!] Error de acceso: {e}")

if __name__ == "__main__":
    scan_real_dll_for_xor()
