import os
import struct

def find_string_id(spa_file, keyword="Espada"):
    """Busca una palabra clave en StringTable y devuelve su ID numérico."""
    with open(spa_file, 'rb') as f:
        data = f.read()

    string_count = struct.unpack('<I', data[:4])[0]
    header_size = 4
    entry_size = 4
    text_block_start = header_size + (string_count * entry_size)

    print(f"[*] Buscando la palabra '{keyword}' en el diccionario de {string_count} traducciones...")
    
    found_ids = []
    
    for index in range(string_count):
        entry_offset = header_size + (index * entry_size)
        rel_offset = struct.unpack_from('<I', data, entry_offset)[0]
        
        if index + 1 < string_count:
            next_rel_offset = struct.unpack_from('<I', data, entry_offset + 4)[0]
        else:
            next_rel_offset = len(data) - text_block_start
            
        start_byte = text_block_start + rel_offset
        end_byte   = text_block_start + next_rel_offset
        
        raw_text = data[start_byte:end_byte]
        if raw_text.endswith(b'\x00'):
            raw_text = raw_text[:-1]
            
        try:
            text = raw_text.decode('utf-8').strip()
            # Buscamos coincidencias de nombres cortos de ítems
            if text.startswith(keyword) and len(text) < 20: 
                string_id = index + 1
                found_ids.append((string_id, text))
        except UnicodeDecodeError:
            pass
            
    print(f"[+] Encontrados {len(found_ids)} IDs posibles para '{keyword}'.\n")
    return found_ids

def find_offset_in_item(item_file, target_id):
    """Busca en el primer registro de Item.txt en qué offset byte exacto aparece nuestro ID."""
    with open(item_file, 'rb') as f:
        data = f.read()
        
    record_size = 88
    # Tomamos el registro del Ítem 1 (Bytes del 4 al 92)
    record = data[4:4+record_size]
    
    print(f"[*] Escaneando los 88 bytes del Item 1 buscando el número mágico {target_id}...")
    
    # Escaneamos byte por byte (asumiendo que es un ushort o uint32)
    found_offsets = []
    for offset in range(record_size - 2): # -2 porque ushort toma 2 bytes
        val = struct.unpack_from('<H', record, offset)[0]
        if val == target_id:
            found_offsets.append(offset)
            
    return found_offsets

if __name__ == "__main__":
    spa_file = r"D:\Herramientas\LordsBot-Release\GameAssets\Strings\Spa\StringTable.txt"
    item_file = r"D:\Herramientas\LordsBot-Release\GameAssets\Item.txt"
    
    # "Lanza" o "Espada" suelen ser los ítems de nivel bajo de inicio.
    candidates = find_string_id(spa_file, "Espada")
    
    print("-" * 50)
    for string_id, text in candidates[:5]: # Solo mostramos 5
        print(f"    - ID {string_id} == '{text}'")
    print("-" * 50)
    
    print("\n[!] Ahora hacemos al revés. Leemos los primeros 50 IDs que Item.txt declara para el Item 1:")
    with open(item_file, 'rb') as f:
        data = f.read()
    rec1 = data[4:4+88]
    
    for offset in range(0, 30, 2):
        val = struct.unpack_from('<H', rec1, offset)[0]
        print(f"    Offset 0x{offset:02X} -> Valor: {val}")

