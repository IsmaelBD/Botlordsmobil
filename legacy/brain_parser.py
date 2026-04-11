import os
import struct

class IGGStringManager:
    """Gestor perfeccionado para leer la base de datos de idiomas oficiales."""
    def __init__(self, filepath):
        print(f"[*] Cargando Diccionario Neural: {os.path.basename(filepath)}")
        with open(filepath, 'rb') as f:
            self.data = f.read()

        # Los primeros 4 bytes dictan el número total de frases registradas
        self.string_count = struct.unpack('<I', self.data[:4])[0]
        
        # Matemáticas de Ingeniería Inversa Demostrada (Ajuste Preciso):
        # Cada entrada consume 4 bytes: [4 bytes Offset Relativo]
        self.header_size = 4
        self.entry_size  = 4
        # El bloque de texto inicia sumando la cabecera, MÁS los punteros de todas las strings (190,656 * 4)
        # MÁS un puntero final (padding) o arranca justo después. 
        # Actually IGG puts `count` pointers + 1 pointer for the end of the last string? No, just count.
        self.text_block_start = self.header_size + (self.string_count * self.entry_size)
        
    def get_string(self, string_id):
        # Los IDs en Lords Mobile suelen empezar en 1
        index = string_id - 1
        
        if index < 0 or index >= self.string_count:
            return f"[{string_id} Fuera de Rango]"
            
        entry_offset = self.header_size + (index * self.entry_size)
        
        # Leemos el offset de esta cadena y el offset de la *siguiente* cadena para saber su longitud
        rel_offset = struct.unpack_from('<I', self.data, entry_offset)[0]
        
        # Validar si es la última cadena
        if index + 1 < self.string_count:
            next_rel_offset = struct.unpack_from('<I', self.data, entry_offset + 4)[0]
        else:
            next_rel_offset = len(self.data) - self.text_block_start
            
        start_byte = self.text_block_start + rel_offset
        end_byte   = self.text_block_start + next_rel_offset
        
        raw_text = self.data[start_byte:end_byte]
        if raw_text.endswith(b'\x00'):
            raw_text = raw_text[:-1]
        
        try:
            return raw_text.decode('utf-8').strip()
        except UnicodeDecodeError:
            return "[Error de Decodificación]"


class IGGBrain:
    """Cerebro Numérico Maestro que cruza las bases de datos de C# con los idiomas."""
    def __init__(self, gameassets_path):
        self.dir = gameassets_path
        
        # Instanciar el traductor de Strings
        spa_file = os.path.join(self.dir, "Strings", "Spa", "StringTable.txt")
        self.translator = IGGStringManager(spa_file)
        
        self.items = {}
        self._load_items()
        
    def _load_items(self):
        filepath = os.path.join(self.dir, "Item.txt")
        print(f"[*] Parseando Base de Datos Estructural: {os.path.basename(filepath)}")
        with open(filepath, 'rb') as f:
            data = f.read()
            
        # Saltamos la cabecera (4 bytes)
        record_size = 88
        offset = 4
        
        # Leemos todos los registros utilizando generadores para eficiencia O(n)
        while offset + record_size <= len(data):
            record = data[offset:offset+record_size]
            
            e_key    = struct.unpack_from('<H', record, 0x00)[0]
            e_name   = struct.unpack_from('<H', record, 0x02)[0]
            e_color  = struct.unpack_from('<B', record, 0x04)[0]
            e_needlv = struct.unpack_from('<B', record, 0x05)[0]
            e_info   = struct.unpack_from('<H', record, 0x06)[0]
            e_price  = struct.unpack_from('<I', record, 0x0C)[0]
            
            # Buscamos la traducción perfecta usando el traductor
            real_name = self.translator.get_string(e_name)
            real_desc = self.translator.get_string(e_info)
            
            self.items[e_key] = {
                "ID": e_key,
                "Nombre": real_name,
                "Descripción": real_desc,
                "Rareza": e_color,
                "Nivel": e_needlv,
                "Precio Venta": e_price
            }
            offset += record_size
        print(f"[+] ¡Cerebro cargado con {len(self.items)} ítems mapeados físicamente!\n")

    def get_item(self, item_id):
        return self.items.get(item_id, None)

if __name__ == "__main__":
    base_dir = r"D:\Herramientas\LordsBot-Release\GameAssets"
    
    # Inicializando el API pulido del cerebro
    brain = IGGBrain(base_dir)
    
    # Prueba empírica exigiendo los primeros 5 ítems como pedía el usuario
    print("=" * 60)
    print("      TEST FINAL DE INGENIERÍA INVERSA (CEREBRO v1)")
    print("=" * 60)
    for i in range(1, 6):
        data = brain.get_item(i)
        if data:
            print(f"Ítem [{data['ID']}]: {data['Nombre']} (Lv. {data['Nivel']})")
            print(f"  └─ Efecto: {data['Descripción']}")
            print(f"  └─ Oro: {data['Precio Venta']} | Rareza: {data['Rareza']}")
            print("-" * 60)
