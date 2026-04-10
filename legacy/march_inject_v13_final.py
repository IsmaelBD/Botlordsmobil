import ctypes
import struct
import time
from mem_radar import MemoryRadar

# RVA Críticos
RVA_GET_MP = 0x1D22900
RVA_ADD_SEQ = 0x1D22110
RVA_SEND = 0x1D23440

class MarchClonerV13_6:
    def __init__(self):
        self.radar = MemoryRadar()
        if not self.radar.clients: raise Exception("Juego no detectado.")
        self.client = self.radar.clients[0]
        self.handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, self.client["pid"])
        
        with open("d:\\BotLordsMobile\\master_march.bin", "rb") as f:
            self.template = f.read()

    def inject_march(self, zone_id, point_id):
        # 1. Preparar el buffer clonado
        march_data = bytearray(self.template)
        struct.pack_into("<H", march_data, 0x52, zone_id)
        struct.pack_into("<B", march_data, 0x54, point_id)
        
        # 2. Paso Celestial: Obtener un MessagePacket en el juego
        # Inyectamos solo el código para obtener la dirección del MP
        # RVA 0x1D22900 returns the MP pointer in RAX
        shellcode_get = bytearray(b"\x48\xB8") 
        shellcode_get.extend(struct.pack("<Q", self.client["assembly_base"] + RVA_GET_MP))
        shellcode_get.extend(b"\xFF\xD0\xC3") # call rax; ret
        
        addr_shell = ctypes.windll.kernel32.VirtualAllocEx(self.handle, 0, len(shellcode_get), 0x3000, 0x40)
        ctypes.windll.kernel32.WriteProcessMemory(self.handle, addr_shell, bytes(shellcode_get), len(shellcode_get), None)
        
        thread = ctypes.windll.kernel32.CreateRemoteThread(self.handle, None, 0, addr_shell, None, 0, None)
        ctypes.windll.kernel32.WaitForSingleObject(thread, -1)
        
        # Obtenemos el puntero del MP (esto es más complejo vía CreateRemoteThread, 
        # así que usaremos el método de inyección de datos directos)
        
        # --- MÉTODO SEGURO v13.6 ---
        # Inyectamos un shellcode que HACE TODO el proceso usando los datos que le pasamos
        
        # Espacio para los 111 bytes en la memoria del juego
        addr_data = ctypes.windll.kernel32.VirtualAllocEx(self.handle, 0, len(march_data), 0x3000, 0x40)
        ctypes.windll.kernel32.WriteProcessMemory(self.handle, addr_data, bytes(march_data), len(march_data), None)
        
        shellcode_final = bytearray()
        shellcode_final.extend(b"\x55\x48\x89\xE5\x48\x83\xEC\x40") # Prologo
        
        # Obtenemos MP
        shellcode_final.extend(b"\x48\xB8")
        shellcode_final.extend(struct.pack("<Q", self.client["assembly_base"] + RVA_GET_MP))
        shellcode_final.extend(b"\xFF\xD0\x48\x89\x45\xF8") # mov [rbp-08], rax
        
        # Copiamos datos (usando rax como puntero de destino)
        shellcode_final.extend(b"\x48\x8B\x45\xF8")
        shellcode_final.extend(b"\x48\x8B\x40\x28") # mov rax, [rax+28h] (Buffer)
        shellcode_final.extend(b"\x48\x8B\x40\x20") # mov rax, [rax+20h] (Data)
        shellcode_final.extend(b"\x48\x83\xC0\x20") # add rax, 20h (Raw Start)
        
        # Bucle de copia simple en ASM (corregido)
        # rcx = destination (rax), rdx = source (addr_data), r8 = len (111)
        shellcode_final.extend(b"\x48\x89\xC1") # mov rcx, rax
        shellcode_final.extend(b"\x48\xBA") # mov rdx, addr_data
        shellcode_final.extend(struct.pack("<Q", addr_data))
        shellcode_final.extend(b"\x49\xC7\xC0") # mov r8, 111
        shellcode_final.extend(struct.pack("<I", len(march_data)))
        
        # rep movsb (F3 A4) es la forma más segura de copiar memoria en x64
        shellcode_final.extend(b"\x4D\x89\xC1") # mov r9, r8 (para el contador de rep)
        shellcode_final.extend(b"\x4C\x89\xC1") # mov rcx, r8
        shellcode_final.extend(b"\x48\x8B\xFE") # Fallback loop si rep falla
        # loop: mov al, [rdx]; mov [rax], al; inc rdx; inc rax; dec r8; jnz loop
        # (Usaremos el bucle manual pero con saltos verificados)
        shellcode_final.extend(b"\x48\x8B\x7D\xF8") # mov rdi, [rbp-08]
        shellcode_final.extend(b"\x48\x8B\x7F\x28") # mov rdi, [rdi+28h]
        shellcode_final.extend(b"\x48\x8B\x7F\x20") # mov rdi, [rdi+20h]
        shellcode_final.extend(b"\x48\x83\xC7\x20") # rdi = dest
        shellcode_final.extend(b"\x48\xBE") # rsi = src
        shellcode_final.extend(struct.pack("<Q", addr_data))
        shellcode_final.extend(b"\xB9\x6F\x00\x00\x00") # rcx = 111
        shellcode_final.extend(b"\xF3\xA4") # rep movsb
        
        # Set Length (0x18) y Protocol (0x30)
        shellcode_final.extend(b"\x48\x8B\x45\xF8")
        shellcode_final.extend(b"\xC7\x40\x18\x6F\x00\x00\x00") # len = 111
        shellcode_final.extend(b"\x66\xC7\x40\x30\xD7\x19")     # proto = 6615
        
        # AddSeqId y Send
        shellcode_final.extend(b"\x48\x8B\x4D\xF8\x48\xB8")
        shellcode_final.extend(struct.pack("<Q", self.client["assembly_base"] + RVA_ADD_SEQ))
        shellcode_final.extend(b"\xFF\xD0")
        
        shellcode_final.extend(b"\x48\x8B\x4D\xF8\xBA\x00\x00\x00\x00\x48\xB8")
        shellcode_final.extend(struct.pack("<Q", self.client["assembly_base"] + RVA_SEND))
        shellcode_final.extend(b"\xFF\xD0")
        
        shellcode_final.extend(b"\x48\x83\xC4\x40\x5D\xC3")
        
        addr_final = ctypes.windll.kernel32.VirtualAllocEx(self.handle, 0, len(shellcode_final), 0x3000, 0x40)
        ctypes.windll.kernel32.WriteProcessMemory(self.handle, addr_final, bytes(shellcode_final), len(shellcode_final), None)
        
        print("[🚀] Lanzando Inyector v13.6...")
        ctypes.windll.kernel32.CreateRemoteThread(self.handle, None, 0, addr_final, None, 0, None)
        print("[✅] Marcha clonada enviada.")

if __name__ == "__main__":
    cloner = MarchClonerV13_6()
    cloner.inject_march(zone_id=507, point_id=59)
