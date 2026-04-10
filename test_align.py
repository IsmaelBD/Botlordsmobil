import struct

spa_file = r"D:\Herramientas\LordsBot-Release\GameAssets\Strings\Spa\StringTable.txt"
with open(spa_file, 'rb') as f:
    data = f.read()

string_count = struct.unpack('<I', data[:4])[0]
header_size = 4
entry_size = 4
text_block_start = header_size + (string_count * entry_size)

print(f"[*] Comprobando Alineación de Texto (Primeros 15 Textos):")
for index in range(15):
    entry_offset = header_size + (index * entry_size)
    rel_offset = struct.unpack_from('<I', data, entry_offset)[0]
    next_rel_offset = struct.unpack_from('<I', data, entry_offset + 4)[0]
    
    raw_text = data[text_block_start + rel_offset: text_block_start + next_rel_offset]
    try:
        t = raw_text.decode('utf-8').replace('\n', ' ')
        print(f"[{index}] -> '{t}'")
    except Exception as e:
        print(f"[{index}] -> ERROR: {e}")
