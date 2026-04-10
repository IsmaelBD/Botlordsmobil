import frida
import sys
from mem_radar import MemoryRadar

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, str):
            print(payload, flush=True)
        else:
            print(f"--- CAPTURA ENCONTRADA ---", flush=True)
            print(f"MapID: {payload.get('mapID')}", flush=True)
            print(f"ZoneID: {payload.get('zone')}", flush=True)
            print(f"PointID: {payload.get('point')}", flush=True)
            # Guardar en un archivo para uso posterior
            with open("d:\\BotLordsMobile\\target_coords.txt", "w") as f:
                f.write(f"{payload.get('zone')},{payload.get('point')}")
            print("Guardado en target_coords.txt. ¡Ya puedes cerrar esto!", flush=True)
    elif message['type'] == 'error':
        print(message['stack'], flush=True)

def main():
    radar = MemoryRadar()
    if not radar.clients: return
    pid = radar.clients[0]["pid"]
    
    try:
        session = frida.attach(pid)
        print(f"[+] Hookeando PID {pid}...")
        
        with open("d:\\BotLordsMobile\\find_coordinate_id.js", "r", encoding="utf-8") as f:
            script_code = f.read()
            
        script = session.create_script(script_code)
        script.on('message', on_message)
        script.load()
        
        print("[+] ESCUCHANDO... Haz click en la mina en el juego (solo abrir menú).")
        sys.stdin.read()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
