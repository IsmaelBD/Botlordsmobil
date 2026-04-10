import os
import struct

def read_string_table(filepath, target_ids):
    print(f"\n[📖] MAPEO DE IDIOMA EN: {os.path.basename(filepath)}")
    
    with open(filepath, 'rb') as f:
        data = f.read()

    # Los primeros 4 bytes son la cantidad total de frases en el diccionario
    string_count = struct.unpack('<I', data[:4])[0]
    print(f"[+] Total de palabras/frases en IGG: {string_count}")
    
    # El diccionario funciona con "Punteros de Desplazamiento" (Offsets)
    # Por cada palabra hay un entero de 4 bytes que indica en qué byte empieza
    base_offset = 4
    string_offsets = []
    for i in range(string_count):
        off = struct.unpack_from('<I', data, base_offset + (i*4))[0]
        string_offsets.append(off)
        
    print(f"[+] Diccionario cargado con éxito. Buscando traducción...\n")
    print("-" * 50)
    
    # El bloque de texto arranca dspués del array de punteros
    text_data_start = base_offset + (string_count * 4)
    
    for string_id in target_ids:
        # Los IDs en el juego parecen estar basados en 1, así que restamos 1 para el array
        index = string_id - 1
        
        if index < 0 or index >= string_count:
            print(f"ID {string_id} fuera de rango.")
            continue
            
        start_pos = text_data_start + string_offsets[index]
        
        # El final de la cadena es donde empieza la siguiente
        if index + 1 < string_count:
            end_pos = text_data_start + string_offsets[index + 1]
        else:
            end_pos = len(data)
            
        # Extraemos y decodificamos el texto
        raw_string = data[start_pos:end_pos]
        # quitamos el byte nulo \x00 al final si existe
        if raw_string.endswith(b'\x00'):
            raw_string = raw_string[:-1]
            
        try:
            decoded_string = raw_string.decode('utf-8')
            print(f"[>] ID de Texto {string_id} ==> \"{decoded_string}\"")
        except:
            print(f"[>] ID de Texto {string_id} ==> (Error Decodificación)")

if __name__ == "__main__":
    spa_strings = r"D:\Herramientas\LordsBot-Release\GameAssets\Strings\Spa\StringTable.txt"
    # Buscamos los IDs de nombre de nuestros items 1, 2, 3, 4 y 5.
    target_ids = [2301, 2302, 2303, 2304, 2305] 
    read_string_table(spa_strings, target_ids)
