import time
from mem_radar import MemoryRadar
from win32_manager import Win32GhostClient

class AutoGrinderBot:
    def __init__(self):
        print("[*] Iniciando Auto-Grinder AI...")
        # 1. Instanciamos el Lector de Memoria
        self.radar = MemoryRadar()
        
        # 2. Instanciamos las Manos (Win32)
        self.hands = Win32GhostClient("Lords Mobile PC")
        
        if not self.radar.clients or not self.hands.hwnd:
            print("[!] FATAL: No se puede inicializar la IA. Abre el juego primero.")
            self.active = False
            return
            
        self.active = True
        self.client_pid = self.radar.clients[0]["pid"]
        self.handle = self.radar.clients[0]["handle"]
        self.assembly_base = self.radar.clients[0]["assembly_base"]
        
        # 3. Forzar Resolución Estándar
        self.hands.force_resolution(1280, 720)

    def get_player_state(self):
        """Lee el Cerebro del Juego (Punteros) y extrae las variables operativas en 1 milisegundo."""
        target_rva = 0x58F5368
        dm_typeinfo_ptr = self.assembly_base + target_rva
        type_info_addr = self.radar.read_pointer(self.handle, dm_typeinfo_ptr)
        
        if type_info_addr == 0: return None
        
        static_fields_ptr = self.radar.read_pointer(self.handle, type_info_addr + 0xB8)
        instance_ptr = self.radar.read_pointer(self.handle, static_fields_ptr + 0x18)
        if instance_ptr == 0: return None
            
        role_attr_addr = instance_ptr + 0x470
        
        # Leemos variables críticas para toma de decisiones
        state = {
            "Level": self.radar.read_byte(self.handle, role_attr_addr + 0x32),
            "Diamond": self.radar.read_uint32(self.handle, role_attr_addr + 0x98),
            # El Flag del Tutorial está en Offset 0x78. Guide.LValue está en +0x8 (Total: 0x80)
            "TutorialStep": self.radar.read_uint32(self.handle, role_attr_addr + 0x80) 
        }
        return state

    def macro_gather_resources(self):
        """Macro Win32: Automáticamente envía tropas a recolectar usando la UI."""
        print("[+] 🚜 Iniciando recolección automática de madera en los alrededores...")
        
        # NOTA: Las coordenadas [X, Y] están estimadas para una resolución de 1280x720.
        #       Deben afinarse una vez verificadas en la pantalla del VPS.
        
        # 1. Clic Botón Mapa Global / Salir al Exterior
        self.hands.vClick(80, 622)
        time.sleep(2.5)  # Animación de salida al mapa
        
        # 2. Clic en el cultivo visible / Nodo de Recursos
        self.hands.vClick(522, 356)
        time.sleep(1.2)
        
        # 3. Clic menú emergente (Recolectar)
        self.hands.vClick(528, 298)
        time.sleep(1.2)
        
        # 4. Asignar las tropas máximas permitidas
        self.hands.vClick(583, 252) 
        time.sleep(1.5)
        
        # 5. Clic al botón FINAL de Despliegue de Marcha!
        self.hands.vClick(787, 460)
        print("[!] Ciclo de recolección inyectado. Comprueba si las tropas marchan en segundo plano.")

    def run_loop(self):
        """La Máquina de Estados Finita (FSM). Bucle central de la inteligencia."""
        print("\n" + "="*50)
        print("    INICIALIZANDO MOTOR AUTÓNOMO DE TOMA DE DECISIÓN")
        print("="*50)
        
        while self.active:
            state = self.get_player_state()
            if not state:
                print("[-] Esperando a que el jugador o el mundo termine de cargar...")
                time.sleep(2)
                continue

            print(f"[RADAR] Stats Recibidas -> Nivel: {state['Level']} | Riqueza: {state['Diamond']} Gemas | Tutorial: Fase {state['TutorialStep']}")

            # LÓGICA DE DECISIÓN DE LA IA:
            if state["TutorialStep"] > 0 and state["TutorialStep"] < 999: # Estás atascado en el Tutorial
                print(f"[IA] El juego está forzando un tutorial (Paso {state['TutorialStep']}). Evadiendo sistema...")
                # (Aquí programaríamos la lógica para clickear el elemento brillante o saltarlo)
                self.hands.vClick(300, 400) # Clic de prueba evasivo
                
            elif state["Level"] >= 2: # Si ya somos jugables y no estamos en tutorial
                # Llamamos a nuestro algoritmo macro Win32
                self.macro_gather_resources()
                # Dormimos la IA 5 minutos (300 seg) mientras las tropas van y vienen para no saturarla ni ser baneados
                print("[IA] Entrando en Crio-Sueño de 5 minutos, esperando retorno de marcha.")
                time.sleep(300) 
            
            else:
                # Si nada importa, esperar
                time.sleep(5)

if __name__ == "__main__":
    bot = AutoGrinderBot()
    if bot.active:
        bot.run_loop()
