import struct

spa_file = r"D:\Herramientas\LordsBot-Release\GameAssets\Strings\Spa\StringTable2.txt"
with open(spa_file, 'rb') as f:
    data = f.read()

c = struct.unpack('<I', data[:4])[0]
t_s = 4 + (c * 4)

print("[*] Buscando 'Gema' y 'Espada Corta' en todo StringTable...")
found = 0
for i in range(c):
    if found > 10: break
    
    off1 = struct.unpack_from('<I', data, 4 + (i * 4))[0]
    next_off = struct.unpack_from('<I', data, 4 + ((i + 1) * 4))[0] if i + 1 < c else len(data) - t_s
    
    text = data[t_s + off1 : t_s + next_off]
    if text.endswith(b'\x00'): text = text[:-1]
    
    try:
        t = text.decode('utf-8')
        if t == "Espada Corta" or t == "Gema":
            print(f"  [+] Encontrado '{t}' en el ID {i + 1}")
            found += 1
    except:
        pass
