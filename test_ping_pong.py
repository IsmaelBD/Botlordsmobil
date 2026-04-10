import time
from win32_manager import Win32GhostClient

def test_ping_pong():
    print("="*60)
    print(" 🏓 TEST DE CONECTIVIDAD GHOST (PING-PONG) ")
    print("="*60)
    
    hands = Win32GhostClient("Lords Mobile PC")
    if not hands.hwnd:
        print("[!] Error: No se encontró la ventana del juego.")
        return

    # Forzamos resolución para asegurar que las coordenadas son válidas
    hands.force_resolution(1280, 720)
    time.sleep(1)

    # COORDENADA 1: BOTÓN MAPA (Desde el Castillo)
    print("[1] Intentando salir al MAPA...")
    hands.vClick(80, 622)
    
    time.sleep(4) # Esperamos a que cargue el mapa exterior

    # COORDENADA 2: BOTÓN CASTILLO (Desde el Mapa)
    print("[2] Intentando volver al CASTILLO...")
    hands.vClick(80, 622) 

    print("\n[*] Test finalizado. ¿Viste algún movimiento en el juego?")

if __name__ == "__main__":
    test_ping_pong()
