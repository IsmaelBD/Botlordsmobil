import psapi
import ctypes
from ctypes import wintypes
from mem_radar import MemoryRadar

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class BotBrain:
    """Representa el cerebro individual de cada cuenta abierta."""
    def __init__(self, instance_info):
        self.pid = instance_info["pid"]
        self.handle = instance_info["handle"]
        self.base = instance_info["base"]
        self.radar = MemoryRadar()
        self.stats = {}

    def update_telemetry(self):
        """Lee el corazón de la RAM para esta cuenta específica."""
        # Buscamos el DataManager Instance (Logic already in mem_radar)
        try:
            self.stats = self.radar.get_player_state(self.handle, self.base)
            return True
        except Exception as e:
            return False

class BotHive:
    def __init__(self):
        print("="*60)
        print("         CORE DE COLMENA (TASK MANAGER V2.0)")
        print("="*60)
        self.brains = []
        self.refresh_instances()

    def refresh_instances(self):
        """Escanea el sistema buscando todas las cabezas del Dragón (PIDs)."""
        temp_radar = MemoryRadar()
        self.brains = []
        
        if not temp_radar.clients:
            print("[!] No se detectaron instancias activas de Lords Mobile.")
            return

        for client in temp_radar.clients:
            brain = BotBrain(client)
            if brain.update_telemetry():
                self.brains.append(brain)
                name = brain.stats.get("Name", "Lord") # To implement proper name reading
                print(f"[+] Vinculada Cuenta -> [PID: {brain.pid}] Level: {brain.stats['Level']} | Gems: {brain.stats['Diamond']}")
            else:
                print(f"[?] PID {brain.pid} detectado pero aún no ha cargado el RoleInfo.")

    def run_heartbeat(self):
        """Mantiene la colmena actualizada en tiempo real."""
        print("\n[*] Entrando en bucle de vigilancia remota...")
        try:
            while True:
                for brain in self.brains:
                    brain.update_telemetry()
                    # Aquí irá la toma de decisiones lógicas
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n[*] Colmena detenida por el usuario.")

if __name__ == "__main__":
    hive = BotHive()
    hive.run_heartbeat()
