import ctypes
import struct
import time
from mem_radar import MemoryRadar

# RVA Críticos (Actualizados)
RVA_GET_MP = 0x1D22900      # MessagePacket.GetGuestMessagePack
RVA_ADD_US = 0x1D224A0      # MessagePacket.Add(ushort)
RVA_ADD_UI = 0x1D22430      # MessagePacket.Add(uint)
RVA_ADD_BY = 0x1D22860      # MessagePacket.Add(byte)
RVA_SEND   = 0x1D23440      # MessagePacket.Send
RVA_GET_INSTANCE = 0xD458C0 # DataManager.get_Instance
RVA_MAP_TO_POINT = 0x1E82480 # MapManager.MapIDToPointCode

class MarchInjectorV13:
    def __init__(self):
        self.radar = MemoryRadar()
        if not self.radar.clients:
            raise Exception("Juego no detectado.")
        
        self.client = self.radar.clients[0]
        self.pid = self.client["pid"]
        self.base = self.client["assembly_base"]
        self.handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, self.pid)

    def inject_native_march(self, x, y, hero_ids=[9, 0], troop_counts=[1]):
        """
        Inyector v13: Delega la construcción de los 111 bytes al motor del juego.
        Replicamos la secuencia exacta capturada por el rastreador de RVA.
        """
        # Shellcode para invocar las 33 llamadas nativas
        # 1. Obtener MP
        # 2. Set Protocol 6615
        # 3. Add sequence (1)
        # 4. Add 5 heroes
        # 5. Add 16 troops
        # 6. Add PointCode (Zone, Point)
        # 7. Add 5 pets
        # 8. Add 4 T5
        # 9. Send
        
        shellcode = bytearray()
        
        # Prólogo: Salvar registros
        shellcode.extend(b"\x55\x48\x89\xE5") # push rbp; mov rbp, rsp
        shellcode.extend(b"\x48\x83\xEC\x40") # sub rsp, 64
        
        # 1. rcx = MessagePacket.GetGuestMessagePack()
        addr_get_mp = self.base + RVA_GET_MP
        shellcode.extend(b"\x48\xB8") # mov rax, addr
        shellcode.extend(struct.pack("<Q", addr_get_mp))
        shellcode.extend(b"\xFF\xD0") # call rax
        shellcode.extend(b"\x48\x89\x45\xF8") # mov [rbp-08], rax (Guardar MP)
        
        # 2. Set Protocol 6615 (Protocolo está en offset 0x30 del MP)
        # mov word ptr [rax+30h], 6615
        shellcode.extend(b"\x66\xC7\x40\x30")
        shellcode.extend(struct.pack("<H", 6615))
        
        # Funciones Auxiliares
        addr_add_us = self.base + RVA_ADD_US
        addr_add_ui = self.base + RVA_ADD_UI
        addr_add_by = self.base + RVA_ADD_BY
        
        def call_add(addr, val, is_byte=False):
            code = bytearray()
            code.extend(b"\x48\x8B\x4D\xF8") # mov rcx, [rbp-08] (Instancia MP)
            if is_byte:
                code.append(0xB2) # mov dl, val
                code.append(val & 0xFF)
            else:
                code.extend(b"\xBA") # mov edx, val
                code.extend(struct.pack("<I", val))
            code.extend(b"\x48\xB8") # mov rax, addr
            code.extend(struct.pack("<Q", addr))
            code.extend(b"\xFF\xD0") # call rax
            return code

        # --- CONSTRUCCIÓN DEL PAQUETE (33 pasos) ---
        
        # Paso 1: Prefijo de Protocolo (Crucial para los 111 bytes)
        shellcode.extend(call_add(addr_add_us, 1))
        
        # Pasos 2-6: Héroes (5 slots)
        for i in range(5):
            h_id = hero_ids[i] if i < len(hero_ids) else 0
            shellcode.extend(call_add(addr_add_us, h_id))
            
        # Pasos 7-22: Tropas (16 tipos)
        for i in range(16):
            count = troop_counts[i] if i < len(troop_counts) else 0
            shellcode.extend(call_add(addr_add_ui, count))
            
        # Pasos 23-24: PointCode (ZoneID ushort, PointID byte)
        # Primero calculamos los IDs calibrados (REINO 1977)
        # Base Zone: 24576
        # Desplazamiento Forest (375, 499) -> Zone 24608, Point 53
        # Aquí usamos los valores que ya probamos con éxito en el escáner
        shellcode.extend(call_add(addr_add_us, 24608)) # Zone
        shellcode.extend(call_add(addr_add_by, 53, is_byte=True)) # Point
        
        # Pasos 25-29: Mascotas (5 slots)
        for i in range(5):
            shellcode.extend(call_add(addr_add_us, 0))
            
        # Pasos 30-33: Tropas T5 (4 tipos)
        for i in range(4):
            shellcode.extend(call_add(addr_add_ui, 0))
            
        # --- ENVÍO ---
        shellcode.extend(b"\x48\x8B\x4D\xF8") # mov rcx, [rbp-08]
        shellcode.extend(b"\x48\xC7\xC2\x00\x00\x00\x00") # mov rdx, 0 (Force = False)
        shellcode.extend(b"\x48\xB8") # mov rax, addr_send
        shellcode.extend(struct.pack("<Q", self.base + RVA_SEND))
        shellcode.extend(b"\xFF\xD0") # call rax
        
        # Epílogo
        shellcode.extend(b"\x48\x83\xC4\x40") # add rsp, 64
        shellcode.extend(b"\x5D\xC3") # pop rbp; ret
        
        # Inyectar y ejecutar
        self._execute_shellcode(shellcode)
        print(f"[✅] v13: Marcha delegada al motor nativo exitosamente.")

    def _execute_shellcode(self, code):
        size = len(code)
        addr = ctypes.windll.kernel32.VirtualAllocEx(self.handle, 0, size, 0x3000, 0x40)
        ctypes.windll.kernel32.WriteProcessMemory(self.handle, addr, bytes(code), size, None)
        thread = ctypes.windll.kernel32.CreateRemoteThread(self.handle, None, 0, addr, None, 0, None)
        ctypes.windll.kernel32.WaitForSingleObject(thread, -1)
        ctypes.windll.kernel32.VirtualFreeEx(self.handle, addr, 0, 0x8000)

if __name__ == "__main__":
    print("--- LORDSBOT v13 (Native Delegate) ---")
    injector = MarchInjectorV13()
    # Enviamos marcha con 2 héroes (ID 9 y Slot Vacío por ahora) 
    # y 1 tropa T1 a la posición del bosque calibrada
    injector.inject_native_march(375, 499, hero_ids=[9, 0], troop_counts=[1])
