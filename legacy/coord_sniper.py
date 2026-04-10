import ctypes
import time
from win32_manager import Win32GhostClient

user32 = ctypes.windll.user32

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def snipe_coordinates():
    hands = Win32GhostClient("Lords Mobile PC")
    if not hands.hwnd:
        print("[!] Error: No encuentro el juego abierto para calibrar.")
        return

    # IMPORTANTE: Forzamos la resolución ANTES de pedir coordenadas
    # para que los números siempre coincidan con el motor del bot.
    hands.force_resolution(1280, 720)
    time.sleep(1)

    print("="*60)
    print(" 🎯 FRANCOTIRADOR DE MACROS (CALIBRACIÓN WIN32) ")
    print("="*60)
    print("Instrucciones:")
    print("1. Mueve tu ratón y sitúalo justo encima del botón del juego que quieras cliquear.")
    print("2. Sin mover el ratón de ahí, presiona la tecla ENTER en esta ventana negra.")
    print("3. Repite por cada botón del flujo de recolección.\n")

    try:
        paso = 1
        while True:
            input(f"[Paso {paso}] Pon el ratón en el botón y presiona ENTER...")
            pt = POINT()
            # Obtenemos el Pixel Físico Global de la Pantalla
            user32.GetCursorPos(ctypes.byref(pt))
            # Lo traducimos matemáticamente a las coordenadas internas del Lienzo de Unity!
            user32.ScreenToClient(hands.hwnd, ctypes.byref(pt))
            print(f"        ✅ COORDENADA PERFECTA -> self.hands.vClick({pt.x}, {pt.y})")
            paso += 1
    except KeyboardInterrupt:
        print("\n[*] Calibración finalizada.")

if __name__ == "__main__":
    snipe_coordinates()
