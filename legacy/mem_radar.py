import ctypes
from ctypes import wintypes
import subprocess

# Configuración Kernel32 / Psapi
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

# Permisos requeridos para escanear memoria sin permisos de depuración peligrosos
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

# Retiramos argtypes globales para evitar conflictos directos con ctypes arrays.
# Solo aplicaremos casting (wintypes.HMODULE) en las llamadas conflictivas.

class MemoryRadar:
    def __init__(self, process_name="Lords Mobile PC.exe"):
        self.process_name = process_name
        self.pids = self._get_pids()
        
        if not self.pids:
            print(f"[!] Ninguna instancia detectada de '{self.process_name}'")
            return
            
        print(f"[*] Módulo Radar en Línea. Múltiples Instancias Soportadas: {len(self.pids)} detectadas.")
        
        # Guardaremos el manejador de Windows y el desplazamiento de cada juego
        self.clients = []
        for pid in self.pids:
            self._attach_to_process(pid)

    def _get_pids(self):
        """Usa consola remota local para buscar los PIDs de todos los Lords Mobile abiertos."""
        try:
            output = subprocess.check_output(['tasklist', '/FI', f'imagename eq {self.process_name}', '/FO', 'CSV'])
            lines = output.decode('utf-8', errors='ignore').strip().split('\n')
            pids = []
            # Saltamos la cabecera CSV (Image Name, PID, Session Name...)
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split('","')
                    if len(parts) >= 2:
                        pids.append(int(parts[1]))
            return pids
        except:
            return []

    def _attach_to_process(self, pid):
        """Inyecta un gancho de lectura en el proceso sin levantar alarmas de escritura."""
        # Se abre en modo Solo Lectura
        h_process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h_process:
            print(f"[-] Fallo abriendo proceso PID: {pid}. Permisos insuficientes o Anti-Cheat activo.")
            return

        game_assembly_base = self._get_module_base(h_process, "GameAssembly.dll")
        if game_assembly_base:
            print(f"[+] [PID: {pid}] Gancho exitoso a GameAssembly.dll en la dirección: {hex(game_assembly_base)}")
            self.clients.append({
                "pid": pid,
                "handle": h_process,
                "assembly_base": game_assembly_base
            })
        else:
            print(f"[-] [PID: {pid}] No se pudo enrutar GameAssembly.dll")

    def _get_module_base(self, h_process, module_name):
        """Recorre la matriz de módulos inyectados del juego para encontrar la IA (GameAssembly)."""
        hMods = (wintypes.HMODULE * 1024)()
        cbNeeded = wintypes.DWORD()
        # Escaneamos módulos (0x03 pide módulos de 32 y 64 bits combinados)
        if psapi.EnumProcessModulesEx(h_process, ctypes.byref(hMods), ctypes.sizeof(hMods), ctypes.byref(cbNeeded), 3):
            module_count = int(cbNeeded.value / ctypes.sizeof(wintypes.HMODULE))
            for i in range(module_count):
                szModName = ctypes.create_unicode_buffer(260)
                # Casting seguro forzado a wintypes.HMODULE() para evitar Overflow en 64 bits
                psapi.GetModuleBaseNameW(h_process, wintypes.HMODULE(hMods[i]), szModName, ctypes.sizeof(szModName))
                if szModName.value.lower() == module_name.lower():
                    # La dirección de memoria base es directamente el Handle en Módulos.
                    return hMods[i]
        return None

    def read_mem(self, h_process, address, size=8):
        """Llamada base a memoria C."""
        buffer = (ctypes.c_byte * size)()
        bytes_read = ctypes.c_size_t()
        kernel32.ReadProcessMemory(h_process, ctypes.c_void_p(address), ctypes.byref(buffer), size, ctypes.byref(bytes_read))
        return bytearray(buffer)

    def read_pointer(self, h_process, address):
        """Lee un Puntero Windows nativo de 64 bits (8 bytes)."""
        data = self.read_mem(h_process, address, 8)
        return int.from_bytes(data, byteorder='little')

    def read_uint32(self, h_process, address):
        data = self.read_mem(h_process, address, 4)
        return int.from_bytes(data, byteorder='little', signed=False)

    def read_uint64(self, h_process, address):
        data = self.read_mem(h_process, address, 8)
        return int.from_bytes(data, byteorder='little', signed=False)

    def read_byte(self, h_process, address):
        data = self.read_mem(h_process, address, 1)
        return int.from_bytes(data, byteorder='little', signed=False)

    def print_player_stats(self):
        """Atraviesa las profundidades de la memoria de Unity para extraer los datos del jugador."""
        target_rva = 0x58F5368
        for client in self.clients:
            base_address = client["assembly_base"]
            handle = client["handle"]
            
            # 1. Obtenemos TypeInfo
            dm_typeinfo_ptr = base_address + target_rva
            type_info_addr = self.read_pointer(handle, dm_typeinfo_ptr)
            
            if type_info_addr == 0:
                print(f"[-] [PID: {client['pid']}] Memoria vacía, juego cargando...")
                continue
                
            # 2. Las variables estáticas de Il2Cpp en esquemas modernos suelen estar en +0xB8
            static_fields_ptr = self.read_pointer(handle, type_info_addr + 0xB8)
            
            # 3. La variable "instance" está en el offset 0x18 de los static_fields
            instance_ptr = self.read_pointer(handle, static_fields_ptr + 0x18)
            
            if instance_ptr == 0:
                print(f"[-] [PID: {client['pid']}] El jugador no ha logueado en su cuenta.")
                continue
                
            # 4. Atravesar las variables del DataManager. instance_ptr es el inicio del C# Object.
            # RoleAttr (_ROLEINFO struct) está en 0x470.
            role_attr_addr = instance_ptr + 0x470
            
            # 5. Robar la Bóveda de Variables
            # Level: 0x32, Diamond: 0x98, Power: 0x110
            level = self.read_byte(handle, role_attr_addr + 0x32)
            diamond = self.read_uint32(handle, role_attr_addr + 0x98)
            power = self.read_uint64(handle, role_attr_addr + 0x110)
            
            print(f"[!] Extracción Física Exitosa [PID: {client['pid']}]:")
            print(f"    ⭐ Nivel del Lord : {level}")
            print(f"    💎 Diamantes/Gemas: {diamond:,}")
            print(f"    ⚔️ Poder Total    : {power:,}")

if __name__ == "__main__":
    print("=" * 60)
    print("       INICIALIZANDO RADAR FANTASMA (FASE 4)")
    print("=" * 60)
    
    radar = MemoryRadar()
    if radar.clients:
        radar.print_player_stats()
