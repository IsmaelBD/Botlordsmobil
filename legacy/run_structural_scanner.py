import frida
import sys
from mem_radar import MemoryRadar

def on_message(message, data):
    if message['type'] == 'send':
        print(message['payload'], flush=True)
    elif message['type'] == 'error':
        print(message['stack'], flush=True)

def main():
    radar = MemoryRadar()
    if not radar.clients: return
    pid = radar.clients[0]["pid"]
    
    try:
        session = frida.attach(pid)
        print(f"[+] Hookeando ESCÁNER ESTRUCTURAL en PID {pid}...")
        
        with open("d:\\BotLordsMobile\\frida_structural_scanner.js", "r", encoding="utf-8") as f:
            script_code = f.read()
            
        script = session.create_script(script_code)
        script.on('message', on_message)
        script.load()
        
        print("[+] ESCUCHANDO... Envía la marcha manual (Bosque Lv.3) ahora.")
        sys.stdin.read()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
