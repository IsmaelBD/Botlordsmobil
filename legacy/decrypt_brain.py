import os
import struct
import string

def extract_strings(data, min_length=4):
    """Extrae cadenas ASCII legibles de un bloque binario, útil para encontrar claves o nombres."""
    result = []
    current_string = ""
    for byte in data:
        char = chr(byte)
        if char in string.printable and byte >= 32 and byte <= 126:
            current_string += char
        else:
            if len(current_string) >= min_length:
                result.append(current_string)
            current_string = ""
    if len(current_string) >= min_length:
        result.append(current_string)
    return result

def analyze_igg_binary(filename):
    print(f"\n[🔬] ANALIZANDO ARCHIVO BINARIO: {os.path.basename(filename)}")
    
    if not os.path.exists(filename):
        print(f"[!] Archivo no encontrado: {filename}")
        return

    with open(filename, 'rb') as f:
        data = f.read()
    
    size = len(data)
    print(f"[-] Tamaño total: {size} bytes")

    # 1. Chequeo de compresión (Zlib, Gzip, Lz4, etc)
    if data.startswith(b'\x78\x9c') or data.startswith(b'\x78\x01') or data.startswith(b'\x78\xda'):
        print("[!] Formato detectado: Comprimido con ZLIB.")
        import zlib
        try:
            data = zlib.decompress(data)
            print(f"[-] ¡Descomprimido con éxito! Nuevo tamaño: {len(data)} bytes")
        except Exception as e:
            print(f"[!] Falló la descompresión ZLIB: {e}")
    elif data.startswith(b'\x1f\x8b'):
        print("[!] Formato detectado: Comprimido con GZIP.")
    else:
        print("[-] Formato detectado: Tabla de registros planos (C# Serializado o Struct arrays).")

    # 2. Búsqueda de Strings
    strings_found = extract_strings(data[:1000], min_length=4)
    if strings_found:
        print(f"\n[-] Cadenas legibles (Primeros 1000 bytes):")
        for s in strings_found[:5]:  # Mostrar los primeros 5
            print(f"    > '{s}'")
    else:
        print("\n[-] No hay cadenas ASCII legibles en la cabecera. Es puramente numérico (IDs/Valores).")

    # 3. Análisis de Registros / Cabecera (Heurística C# BinaryReader)
    # Casi todos los motores exportan los assets con un encabezado indicando el número de registros o la versión.
    print("\n[-] Volcado Estructural de Cabecera (Primeros 16 bytes):")
    if size >= 16:
        # Extraemos como una secuencia de enteros cortos (Int16) usual en C# para IDs
        shorts = struct.unpack('<8H', data[:16])
        print(f"    > Vista como INT16 (Shorts): {shorts}")
        
        # Extraemos como enteros de 32 bits (Int32)
        ints = struct.unpack('<4I', data[:16])
        print(f"    > Vista como INT32 (Integers): {ints}")

    # 4. Adivinar el tamaño del bloque (Struct Array Length)
    # Suelen tener un registro que se repite sistemáticamente.
    print("\n[-] Extracción Dinámica Final:")
    if shorts[0] == 1 and shorts[2] == 1: 
        print("    >> Probable tabla de identificadores secuenciales (IDs 1, 2, 3...).")
        print("    >> Cada registro de objeto (ej. Item) es un Struct de ancho fijo de C#.")
    else:
         print("    >> Intentando leer posibles longitudes dinámicas de array...")


def main():
    base_dir = r"D:\Herramientas\LordsBot-Release\GameAssets"
    # Analizamos archivos clave usando análisis binario dinámico
    analyze_igg_binary(os.path.join(base_dir, "Item.txt"))
    analyze_igg_binary(os.path.join(base_dir, "Monster.txt"))
    analyze_igg_binary(os.path.join(base_dir, "buildUP.txt"))

if __name__ == "__main__":
    main()
