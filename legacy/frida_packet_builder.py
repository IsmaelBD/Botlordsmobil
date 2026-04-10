import frida
import sys
from mem_radar import MemoryRadar

# Offsets obtenidos en dump.cs
RVA_MP_ADD_BYTE = 0x1D22860
RVA_MP_ADD_USHORT = 0x1D224A0
RVA_MP_ADD_UINT = 0x1D22430
RVA_MP_ADD_ULONG = 0x1D22470
RVA_MP_SEND = 0x1D23440

js_code = """
try {
    var m = Process.getModuleByName('GameAssembly.dll');
    var baseAddr = m.base;
    console.log('[+] GameAssembly.dll Base: ' + baseAddr);

    var fnAddByte = baseAddr.add(PTR_ADD_BYTE);
    var fnAddUshort = baseAddr.add(PTR_ADD_USHORT);
    var fnAddUint = baseAddr.add(PTR_ADD_UINT);
    var fnAddUlong = baseAddr.add(PTR_ADD_ULONG);
    var fnSend = baseAddr.add(PTR_SEND);

    var packetLog = [];

    Interceptor.attach(fnSend, {
        onEnter: function(args) {
            var proto = args[0].add(0x30).readU16();
            if (proto === 2415 || proto === 6615) {
                var out = "\\n[🚀] ¡PAQUETE DE MARCHA ENVIADO! Protocol: " + proto + "\\nESTRUCTURA DEL PAYLOAD:\\n";
                for (var i = 0; i < packetLog.length; i++) {
                    out += "  -> " + packetLog[i] + "\\n";
                }
                send(out);
            }
            packetLog = [];
        }
    });

    function hookAdd(addr, typeStr) {
        Interceptor.attach(addr, {
            onEnter: function(args) {
                var mp = args[0];
                var proto = mp.add(0x30).readU16();
                if (proto === 2415 || proto === 6615) {
                    var val = args[1].toInt32(); 
                    packetLog.push('Add(' + typeStr + ') = ' + val);
                }
            }
        });
    }

    hookAdd(fnAddByte, 'byte');
    hookAdd(fnAddUshort, 'ushort');
    hookAdd(fnAddUint, 'uint');

    send('[+] Hooks inyectados con éxito. Esperando que envíes la marcha...');
} catch(e) {
    send("Error en script Frida: " + e.message);
}
"""

js_code = js_code.replace("PTR_ADD_BYTE", str(RVA_MP_ADD_BYTE))
js_code = js_code.replace("PTR_ADD_USHORT", str(RVA_MP_ADD_USHORT))
js_code = js_code.replace("PTR_ADD_UINT", str(RVA_MP_ADD_UINT))
js_code = js_code.replace("PTR_ADD_ULONG", str(RVA_MP_ADD_ULONG))
js_code = js_code.replace("PTR_SEND", str(RVA_MP_SEND))

def on_message(message, data):
    if message['type'] == 'send':
        # Escribe al archivo directamente para que nada se pierda en el buffer.
        with open("d:\\BotLordsMobile\\frida_resultados.txt", "a", encoding="utf-8") as f:
            f.write(message['payload'] + "\\n")
        print(message['payload'], flush=True)
    elif message['type'] == 'error':
        print(message['stack'], flush=True)

def main():
    radar = MemoryRadar()
    if not radar.clients: 
        print("No se encontró el juego.")
        return
    pid = radar.clients[0]["pid"]
    
    try:
        # Abrir archivo nuevo
        with open("d:\\BotLordsMobile\\frida_resultados.txt", "w", encoding="utf-8") as f:
            f.write("--- LOG DE FRIDA ---\\n")
            
        session = frida.attach(pid)
        print(f"[+] Conectado al PID {pid}", flush=True)
        
        script = session.create_script(js_code)
        script.on('message', on_message)
        script.load()
        
        # Keep alive
        sys.stdin.read()
    except Exception as e:
        print(f"Error Frida Python: {e}", flush=True)

if __name__ == "__main__":
    main()
