import re

def extract_struct(dump_file, struct_name):
    print(f"[*] Analizando {dump_file} para encontrar {struct_name}")
    in_struct = False
    fields = []
    
    with open(dump_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if re.match(rf'\s*public struct {struct_name}\b', line):
                in_struct = True
                continue
                
            if in_struct:
                if line.strip() == "}":
                    break
                    
                # Match field: public ushort EquipKey; // 0x0
                match = re.search(r'public ([\w\[\]]+) (\w+);\s*// (0x[0-9A-Fa-f]+)', line)
                if match:
                    t_type, name, offset = match.groups()
                    fields.append((name, t_type, int(offset, 16)))
                    
    print(f"[+] Struct {struct_name} encontrado con {len(fields)} campos:")
    for f in fields:
        print(f"    Offset: 0x{f[2]:02X} | {f[1]} {f[0]}")

if __name__ == "__main__":
    extract_struct(r"d:\BotLordsMobile\dump.cs", "Equip")
