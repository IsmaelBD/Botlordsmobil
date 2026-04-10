import json

def find_datamanager_typeinfo(json_path):
    print("[*] Cargando 122MB de script.json...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print("[*] Buscando la Clase y el Puntero de DataManager...")
    
    # Buscamos en los metadatos de las clases (TypeInfo)
    if "ScriptMetadata" in data:
        for md in data["ScriptMetadata"]:
            if md.get("Name") == "DataManager_TypeInfo":
                print(f"[+] Puntero de Clase Encontrado: 0x{md.get('Address'):X}")
                
    # También podemos buscar los métodos para ver dónde instancia
    if "ScriptMethod" in data:
        for md in data["ScriptMethod"]:
            if md.get("Name") == "DataManager$$get_Instance":
                print(f"[+] Método Get_Instance Encontrado en RVA: 0x{md.get('Address'):X}")

if __name__ == "__main__":
    find_datamanager_typeinfo(r"D:\Herramientas\Il2CppDumper-win-v6.7.46\script.json")
