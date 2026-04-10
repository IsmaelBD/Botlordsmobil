import ctypes
from ctypes import wintypes
import time
import random

# Cargamos el núcleo de Windows (User32.dll)
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

# Mensajes Hexadecimales Oficiales de Microsoft
WM_MOUSEMOVE     = 0x0200
WM_LBUTTONDOWN   = 0x0201
WM_LBUTTONUP     = 0x0202
WM_ACTIVATE      = 0x0006
WM_SETFOCUS      = 0x0007
WA_ACTIVE        = 1
WM_MOUSEACTIVATE = 0x0021
MA_ACTIVATE      = 1

class Win32GhostClient:
    def __init__(self, target_window_title="Lords Mobile PC"):
        self.target_title = target_window_title
        self.hwnd = self._find_window()
        if not self.hwnd:
            print(f"[!] ADVERTENCIA: No se encontró ninguna ventana llamada '{self.target_title}'.")
            print("[!] El bot no inyectará hasta que detecte una ventana válida.")
            
    def _find_window(self):
        """Busca el descriptor (Handle) de la ventana del Launcher Oficial."""
        # Se requiere usar string literal 'Lords Mobile' en ctypes para FindWindowW
        hwnd = user32.FindWindowW(None, self.target_title)
        return hwnd

    def force_resolution(self, width=1280, height=720):
        """Obliga al ejecutable oficial a tomar un tamaño constante. Crucial para clicks estáticos."""
        if not self.hwnd: return False
        # Flags: SWP_NOZORDER (no altera profundidad) y SWP_SHOWWINDOW
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040
        # Lo movemos a las coordenadas 0,0 de la pantalla para evitar colisiones
        result = user32.SetWindowPos(self.hwnd, 0, 0, 0, width, height, SWP_NOZORDER | SWP_SHOWWINDOW)
        if result:
            print(f"[*] Pantalla de Lords Mobile forzada exitosamente a -> {width}x{height}")
        return result

    def _make_lparam(self, x, y):
        """Traducción matemática de MakeLParam (C#) a Python."""
        # Combina X e Y en un entero de 32 bits (LPARAM)
        return (y << 16) | (x & 0xFFFF)

    def _jitter(self, base_ms=30):
        """Implementa la orden Anti-Cheat del usuario: Añade retardos erráticos."""
        # Fluctúa entre base_ms y base_ms + 15ms
        sleep_time = random.uniform(base_ms, base_ms + 15) / 1000.0
        time.sleep(sleep_time)

    def vClick(self, x, y):
        """Genera un Clic Izquierdo en coordenadas X,Y de manera paralela e invisible."""
        if not self.hwnd:
            self.hwnd = self._find_window()
            if not self.hwnd: return False

        lparam = self._make_lparam(x, y)
        
        # --- SECUENCIA DE ACTIVACIÓN FANTASMA ---
        # Intentamos convencer a Unity de que la ventana está siendo interactuada humanamente.
        user32.PostMessageW(self.hwnd, WM_MOUSEACTIVATE, self.hwnd, (WM_LBUTTONDOWN << 16) | MA_ACTIVATE)
        user32.PostMessageW(self.hwnd, WM_ACTIVATE, WA_ACTIVE, 0)
        user32.PostMessageW(self.hwnd, WM_SETFOCUS, 0, 0)
        
        # Movimiento previo sincroniza el Raycaster de Unity
        user32.PostMessageW(self.hwnd, WM_MOUSEMOVE, 1, lparam)
        self._jitter(20)
        
        # DOWN
        user32.PostMessageW(self.hwnd, WM_LBUTTONDOWN, 1, lparam)
        
        # Jitter entre presión y liberación
        self._jitter(40)
        
        # UP
        user32.PostMessageW(self.hwnd, WM_LBUTTONUP, 0, lparam)
        
        print(f"[*] GhostClick inyectado en [{x}, {y}] con éxito (Modo Silencioso).")
        return True

    def vDrag(self, start_x, start_y, end_x, end_y):
        """Simula arrastrar el dedo/ratón (Desplazar Mapa) en 40 micro-pasos."""
        if not self.hwnd:
            self.hwnd = self._find_window()
            if not self.hwnd: return False

        # Matemáticas para la fragmentación manual sacada de Controller.cs
        dx = (end_x - start_x) / 40.0
        dy = (end_y - start_y) / 40.0
        
        # Pulsamos
        user32.SendMessageW(self.hwnd, WM_LBUTTONDOWN, 1, self._make_lparam(start_x, start_y))
        
        # Movimiento anti-robótico
        for i in range(1, 41):
            curr_x = int(start_x + (i * dx))
            curr_y = int(start_y + (i * dy))
            
            lparam = self._make_lparam(curr_x, curr_y)
            user32.SendMessageW(self.hwnd, WM_MOUSEMOVE, 1, lparam)
            
            # Demora estricta durante el arrastre para engañar al motor Unity
            # C# usaba 50ms, usaremos ~30ms como indicaste para que sea más veloz.
            self._jitter(30)
            
        # Soltamos al llegar
        user32.SendMessageW(self.hwnd, WM_LBUTTONUP, 0, self._make_lparam(end_x, end_y))
        print(f"[*] GhostDrag inyectado: [{start_x},{start_y}] -> [{end_x},{end_y}]")
        return True

if __name__ == "__main__":
    # Script de prueba unitaria y ejemplo de uso
    print("=" * 50)
    print("        INICIALIZANDO LAS MANOS DEL FANTASMA")
    print("=" * 50)
    
    bot = Win32GhostClient("Lords Mobile PC")
    
    if bot.hwnd:
        print(f"[+] Juego detectado exitosamente. HWND: {bot.hwnd}")
        print("[-] Simulando clic invisible en 2 segundos...")
        time.sleep(2)
        # Esto inyectaría un clic en Cero, Cero. Podría cerrar un anuncio si está ahí.
        bot.vClick(100, 100) 
    else:
        print("[!] Abre Lords Mobile PC para realizar la inyección de prueba.")
