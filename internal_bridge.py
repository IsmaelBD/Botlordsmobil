import ctypes
from ctypes import wintypes
import time
import struct

# Constantes Win32
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_EXECUTE_READWRITE = 0x40

kernel32 = ctypes.windll.kernel32

# Configuracion de tipos para 64-bit
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]

kernel32.VirtualAllocEx.restype = ctypes.c_void_p
kernel32.VirtualAllocEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]

kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

kernel32.CreateRemoteThread.restype = wintypes.HANDLE
kernel32.CreateRemoteThread.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]

kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

class InternalBridge:
    """Motor de Inyeccion de Llamadas Internas (IL2CPP Bridge)."""
    def __init__(self, pid, assembly_base):
        self.pid = pid
        # Nota: 0x1F0FFF = PROCESS_ALL_ACCESS
        self.handle = kernel32.OpenProcess(0x1F0FFF, False, pid)
        self.base = assembly_base
        if not self.handle:
            raise Exception(f"[!] No se pudo abrir el proceso {pid}")
        print(f"[*] Puente Interno Vinculado -> PID: {pid} | Base: 0x{self.base:X}")

    def call_rva(self, rva, args=None):
        """
        Ejecuta una funcion en la direccion Base + RVA usando shellcode x64.
        Soporta hasta 4 argumentos (convencion fastcall: rcx, rdx, r8, r9).
        """
        if args is None: args = []
        target_addr = self.base + rva
        remote_mem = kernel32.VirtualAllocEx(self.handle, 0, 512, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
        if not remote_mem: return 0
            
        return_buffer = remote_mem + 256

        # Shellcode x64 (FastCall)
        shellcode = b"\x48\x83\xEC\x28" # sub rsp, 0x28
        
        # Mapeo de argumentos a registros
        if len(args) > 0: # Arg 0 -> RCX
            shellcode += b"\x48\xB9" + struct.pack("<Q", args[0])
        if len(args) > 1: # Arg 1 -> RDX
            shellcode += b"\x48\xBA" + struct.pack("<Q", args[1])
        if len(args) > 2: # Arg 2 -> R8
            shellcode += b"\x49\xB8" + struct.pack("<Q", args[2])
        if len(args) > 3: # Arg 3 -> R9
            shellcode += b"\x49\xB9" + struct.pack("<Q", args[3])

        shellcode += b"\x48\xB8" + struct.pack("<Q", target_addr) # mov rax, target_addr
        shellcode += b"\xFF\xD0" # call rax
        
        shellcode += b"\x48\xBB" + struct.pack("<Q", return_buffer) # mov rbx, return_buffer
        shellcode += b"\x48\x89\x03" # mov [rbx], rax
        shellcode += b"\x48\x83\xC4\x28" # add rsp, 0x28
        shellcode += b"\xC3" # ret

        # Escribimos el shellcode
        kernel32.WriteProcessMemory(self.handle, remote_mem, shellcode, len(shellcode), None)

        # Ejecutamos
        # Argumentos: Handle, lpThreadAttributes, dwStackSize, lpStartAddress, lpParameter, dwCreationFlags, lpThreadId
        thread = kernel32.CreateRemoteThread(self.handle, None, 0, remote_mem, None, 0, None)
        if not thread:
            print("[!] Error al crear el hilo remoto.")
            return 0
        
        kernel32.WaitForSingleObject(thread, 5000) # Esperamos 5 segundos max
        
        # Leemos el puntero de retorno
        ret_val = ctypes.c_ulonglong()
        kernel32.ReadProcessMemory(self.handle, ctypes.c_void_p(return_buffer), ctypes.byref(ret_val), 8, None)
        
        # Limpieza
        kernel32.CloseHandle(thread)
        return ret_val.value

    def read_memory(self, addr, fmt):
        """Lee memoria del proceso remoto usando struct.unpack."""
        size = struct.calcsize(fmt)
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        if kernel32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), buffer, size, ctypes.byref(bytes_read)):
            return struct.unpack(fmt, buffer.raw)
        return None

    def read_ptr(self, addr):
        """Lee un puntero de 64 bits de la direccion especificada."""
        val = self.read_memory(addr, "<Q")
        return val[0] if val else 0

    def read_unity_string(self, addr):
        """Lee un System.String de Unity (UTF-16)."""
        if not addr: return ""
        length_data = self.read_memory(addr + 0x10, "<I")
        if not length_data: return ""
        length = length_data[0]
        if length == 0: return ""
        # Leer caracteres (UTF-16, 2 bytes por char)
        chars_data = self.read_memory(addr + 0x14, f"{length*2}B")
        if not chars_data: return ""
        return bytes(chars_data).decode("utf-16", errors="ignore")

    def read_cstring(self, addr):
        """Lee la clase personalizada CString del juego."""
        if not addr: return ""
        # MyString (System.String) esta en offset 0x18
        str_ptr = self.read_ptr(addr + 0x18)
        return self.read_unity_string(str_ptr)

if __name__ == "__main__":
    # Test local con una instancia abierta
    from mem_radar import MemoryRadar
    radar = MemoryRadar()
    if radar.clients:
        client = radar.clients[0]
        bridge = InternalBridge(client["pid"], client["assembly_base"])
        
        print("[*] Test: Obteniendo NetworkManager.Instance...")
        nm_instance = bridge.call_rva(0x1D2CD40) # RVA get_Instance
        print(f"[+] NetworkManager Localizado en: 0x{nm_instance:X}")
