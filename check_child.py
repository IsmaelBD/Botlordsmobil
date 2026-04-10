import ctypes

user32 = ctypes.windll.user32

def enum_child_windows(parent_hwnd):
    child_windows = []
    
    EnumChildProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    
    def callback(hwnd, current_lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        
        class_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buff, 256)
        
        child_windows.append({"hwnd": hwnd, "title": buff.value, "class": class_buff.value})
        return True
        
    user32.EnumChildWindows(parent_hwnd, EnumChildProc(callback), 0)
    return child_windows

parent = user32.FindWindowW(None, "Lords Mobile PC")
if parent:
    print(f"[*] Ventana Padre: {parent}")
    hijos = enum_child_windows(parent)
    print(f"[*] Encontradas {len(hijos)} sub-ventanas:")
    for h in hijos:
        print(f"    -> HWND: {h['hwnd']} | Clase: '{h['class']}' | Título: '{h['title']}'")
else:
    print("[!] No se encontró el juego.")
