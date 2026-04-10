import re

def find_send_methods():
    with open("dump.cs", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if "uint[]" in line and ("ushort[]" in line or "Hero" in line or "byte" in line) and "public void" in line:
            # Imprimir contexto
            rva_line = lines[i-1] if i > 0 and "// RVA:" in lines[i-1] else ""
            print(f"{i+1}: {rva_line.strip()} {line.strip()}")
            
if __name__ == "__main__":
    find_send_methods()
