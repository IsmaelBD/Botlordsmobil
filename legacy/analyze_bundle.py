import os
import struct

def analyze_net_bundle(filepath):
    print(f"[*] Analizando {filepath} ({os.path.getsize(filepath) // (1024*1024)} MB)")
    with open(filepath, 'rb') as f:
        # Los Single-File Bundles de .NET suelen tener el bundle header al final del archivo 
        # en .NET 5+, o buscan la firma.
        # Firma típica de bundle de .NET Core 3.1 / .NET 5+:
        BUNDLE_SIGNATURE = bytes([0x8b, 0x12, 0x02, 0xb9, 0x6a, 0xc1, 0x33, 0x46, 0x90, 0x1b, 0xec, 0xc4, 0xeb, 0x84, 0xc1, 0xac])
        
        # Leer el principio para confirmar MZ
        mz = f.read(2)
        if mz != b"MZ":
            print("[!] No es un archivo PE válido (falta MZ).")
            return
            
        print("[+] Archivo PE válido. Escaneando la firma del Bundle de .NET...")
        
        # Como el archivo es grande (222MB), buscaremos la firma mapeando el archivo en memoria o leyendo por bloques.
        f.seek(0)
        chunk_size = 10 * 1024 * 1024
        overlap = len(BUNDLE_SIGNATURE)
        
        found = False
        offset = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
                
            idx = chunk.find(BUNDLE_SIGNATURE)
            if idx != -1:
                abs_offset = offset + idx
                print(f"[!!!] Firma de .NET Single-File Bundle encontrada en el offset: {hex(abs_offset)}")
                found = True
                
                # Leer la información del bundle si es posible
                f.seek(abs_offset + len(BUNDLE_SIGNATURE))
                # Formato del Manifest: version, number of files, etc.
                version = int.from_bytes(f.read(4), 'little')
                print(f"  > Versión del Bundle: {version}")
                break
                
            if len(chunk) < chunk_size:
                break
                
            offset += chunk_size - overlap
            f.seek(offset)
            
        if not found:
            print("[-] No se encontró la firma de un .NET Single-File Bundle. Podría ser un empaquetador de terceros (Enigma, VMProtect) o NativeAOT.")

if __name__ == "__main__":
    analyze_net_bundle(r'D:\Herramientas\LordsBot-Release\LordsMobileBot.exe')
