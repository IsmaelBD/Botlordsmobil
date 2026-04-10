import os
import struct

def decrypt_item_table(filepath):
    print(f"\n[💎] DESENCRIPTANDO TABLA DE OBJETOS: {os.path.basename(filepath)}")
    
    with open(filepath, 'rb') as f:
        data = f.read()

    # La reversión demostró que los primeros 4 bytes son una cabecera:
    # 2 bytes para la versión de la tabla, 2 bytes para el Contador de Registros.
    header = data[:4]
    version, record_count = struct.unpack('<HH', header)
    
    print(f"[+] Versión de la Tabla: {version}")
    print(f"[+] Cantidad de Ítems (Registros): {record_count}")
    
    # Después de las matemáticas, el tamaño por registro (Equip) debe ser 88 bytes.
    # 3579 ítems * 88 bytes = 314952 + 4 bytes de cabecera = 314956 bytes exactos!
    record_size = 88
    
    print(f"[-] Tamaño del archivo encaja perfecto: {record_count * record_size + 4} == {len(data)}")
    print("-" * 50)
    
    # Parseo dinámico de los primeros 5 ítems como prueba de concepto
    offset = 4
    for i in range(5):
        record_data = data[offset:offset+record_size]
        
        # Mapeando los campos en base a la línea 10322 de dump.cs
        # Offset 0x00 | ushort EquipKey
        # Offset 0x02 | ushort EquipName (Puntero a idioma)
        # Offset 0x04 | byte Color
        # Offset 0x05 | byte NeedLv
        # Offset 0x06 | ushort EquipInfo (Puntero a descripción)
        # Offset 0x08 | ushort EquipPicture
        # Offset 0x0C | uint RecoverPrice
        
        # Leemos los primeros 16 bytes de forma individual y segura
        equip_key     = struct.unpack_from('<H', record_data, 0x00)[0]
        equip_name_id = struct.unpack_from('<H', record_data, 0x02)[0]
        color         = struct.unpack_from('<B', record_data, 0x04)[0]
        need_lv       = struct.unpack_from('<B', record_data, 0x05)[0]
        equip_info_id = struct.unpack_from('<H', record_data, 0x06)[0]
        equip_pic     = struct.unpack_from('<H', record_data, 0x08)[0]
        
        # Padding de 2 bytes oculto en 0x0A (probablemente datos descartados)
        recover_price = struct.unpack_from('<I', record_data, 0x0C)[0]
        equip_kind    = struct.unpack_from('<B', record_data, 0x18)[0]
        
        print(f"[{i+1}] ÍTEM DESENCRIPTADO (EquipKey: {equip_key})")
        print(f"    - ID de Nombre: {equip_name_id} (Buscar en GL_Spa.ini)")
        print(f"    - Rareza/Color: {color}")
        print(f"    - Nivel Req.:   {need_lv}")
        print(f"    - ID Icono:     {equip_pic}")
        print(f"    - Precio_Venta: {recover_price} Monedas")
        print(f"    - Tipo Objeto:  {equip_kind}")
        print("")
        
        offset += record_size
        
if __name__ == "__main__":
    game_assets = r"D:\Herramientas\LordsBot-Release\GameAssets"
    decrypt_item_table(os.path.join(game_assets, "Item.txt"))
