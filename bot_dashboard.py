import frida
import time
import os
from mem_radar import MemoryRadar

def load_config():
    config = {}
    if os.path.exists("d:\\BotLordsMobile\\config_coords.txt"):
        with open("d:\\BotLordsMobile\\config_coords.txt", "r") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=")
                    config[key] = val
    return config

def main():
    radar = MemoryRadar()
    if not radar.clients:
        print("[!] Abre el juego primero.")
        return
    
    pid = radar.clients[0]["pid"]
    print(f"[*] Conectando al Tablero de Mando (PID: {pid})...")
    
    session = frida.attach(pid)
    with open("d:\\BotLordsMobile\\frida_context_hijack.js", "r", encoding="utf-8") as f:
        script = session.create_script(f.read())
    
    script.load()
    print("[✅] BOT v14.0 EN LÍNEA. Escuchando cambios en 'config_coords.txt'...")
    
    last_zone = ""
    last_point = ""
    
    try:
        while True:
            conf = load_config()
            zone = int(conf.get("ZONE", 507))
            point = int(conf.get("POINT", 59))
            
            if zone != last_zone or point != last_point:
                script.exports.setcoords(zone, point)
                last_zone = zone
                last_point = point
                print(f"[📍] Destino actualizado: Zona {zone}, Punto {point}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("[!] Apagando Tablero de Mando...")
        session.detach()

if __name__ == "__main__":
    main()
