"""
Cambiador de MAC (MAC Spoofer)
Cambia la dirección MAC de las interfaces de red
Requiere permisos de ROOT/SUDO
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label, Select, DataTable
from textual.binding import Binding
import subprocess
import re
import random
import os

class MacChangerApp(App):
    """Aplicación de Cambio de MAC"""
    
    TITLE = "🎭 Cambiador de MAC"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        padding: 1 2;
    }
    
    .section {
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
    }
    
    .input-group {
        height: auto;
        margin-bottom: 1;
    }
    
    .input-label {
        width: 20;
        content-align: left middle;
    }
    
    Input {
        width: 1fr;
    }
    
    Button {
        margin: 0 1;
    }
    
    #status-box {
        border: solid $primary;
        padding: 1 2;
        background: $panel;
        height: auto;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "refresh_interfaces", "Recargar Interfaces"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with ScrollableContainer(id="main-container"):
            yield Static("🎭 CAMBIADOR DE MAC (MAC SPOOFER)", classes="title")
            
            # Selección de interfaz
            with Vertical(classes="section"):
                yield Static("📡 Selección de Interfaz", classes="section-title")
                yield Select([], prompt="Selecciona una interfaz", id="iface-select")
                yield Static("", id="current-mac-info")
            
            # Nueva MAC
            with Vertical(classes="section"):
                yield Static("✏️ Nueva Dirección MAC", classes="section-title")
                
                with Horizontal(classes="input-group"):
                    yield Label("Nueva MAC:", classes="input-label")
                    yield Input(placeholder="Ej: 00:11:22:33:44:55", id="mac-input")
                
                with Horizontal(classes="input-group"):
                    yield Button("🎲 Aleatoria", variant="primary", id="btn-random")
                    yield Button("💾 Aplicar Cambio", variant="error", id="btn-apply")
                    yield Button("🔄 Restaurar Original", variant="warning", id="btn-restore")
            
            # Estado
            with Vertical(classes="section"):
                yield Static("📊 Estado", classes="section-title")
                yield Static("Listo. Selecciona una interfaz.", id="status-box")
        
        yield Footer()
        
    def on_mount(self):
        self.refresh_interfaces()
        if os.geteuid() != 0:
            self.notify("⚠️ Se requieren permisos de ROOT para cambiar la MAC", severity="error", timeout=10)
            self.query_one("#status-box", Static).update("[red]ERROR: No tienes permisos de root. Ejecuta con sudo.[/]")
            self.query_one("#btn-apply", Button).disabled = True
            self.query_one("#btn-restore", Button).disabled = True

    def refresh_interfaces(self):
        import platform
        system = platform.system()
        
        try:
            interfaces = []
            
            if system == "Linux":
                result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if line and line[0].isdigit():
                        parts = line.split(': ')
                        if len(parts) >= 2:
                            iface = parts[1].strip()
                            if iface != "lo":
                                interfaces.append((iface, iface))
                                
            elif system == "Darwin": # macOS
                result = subprocess.run(['networksetup', '-listallhardwareports'], capture_output=True, text=True)
                # Hardware Port: Wi-Fi
                # Device: en0
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if "Device:" in line:
                        iface = line.split(": ")[1].strip()
                        interfaces.append((iface, iface))
                        
            elif system == "Windows":
                # getmac /v /fo csv
                result = subprocess.run(['getmac', '/v', '/fo', 'csv'], capture_output=True, text=True)
                # "Connection Name","Network Adapter","Physical Address","Transport Name"
                import csv
                import io
                reader = csv.reader(io.StringIO(result.stdout))
                next(reader, None) # Skip header
                for row in reader:
                    if len(row) > 0:
                        name = row[0]
                        # adapter = row[1]
                        interfaces.append((name, name))
                        
            select = self.query_one("#iface-select", Select)
            select.set_options(interfaces)
            
        except Exception as e:
            self.notify(f"Error al listar interfaces: {e}", severity="error")

    def update_current_mac(self, iface):
        import platform
        system = platform.system()
        
        try:
            mac = "Desconocida"
            
            if system == "Linux":
                result = subprocess.run(['ip', 'link', 'show', iface], capture_output=True, text=True)
                mac_match = re.search(r"link/ether ([\da-fA-F:]{17})", result.stdout)
                if mac_match: mac = mac_match.group(1)
                
            elif system == "Darwin":
                result = subprocess.run(['ifconfig', iface], capture_output=True, text=True)
                mac_match = re.search(r"ether ([\da-fA-F:]{17})", result.stdout)
                if mac_match: mac = mac_match.group(1)
                
            elif system == "Windows":
                result = subprocess.run(['getmac', '/v', '/fo', 'csv'], capture_output=True, text=True)
                import csv
                import io
                reader = csv.reader(io.StringIO(result.stdout))
                for row in reader:
                    if len(row) > 2 and row[0] == iface:
                        mac = row[2]
                        break
            
            self.query_one("#current-mac-info", Static).update(
                f"Interfaz: [bold cyan]{iface}[/]\nMAC Actual: [bold green]{mac}[/]"
            )
                
        except Exception as e:
            self.notify(f"Error obteniendo MAC: {e}", severity="error")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "iface-select" and event.value:
            self.update_current_mac(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-random":
            self.generate_random_mac()
        elif event.button.id == "btn-apply":
            self.change_mac()
        elif event.button.id == "btn-restore":
            self.restore_mac()

    def generate_random_mac(self):
        # Generate random MAC (unicast, locally administered)
        # First byte should be even (unicast) and have 2nd bit set (local) -> x2, x6, xA, xE
        first_byte = random.choice([0x02, 0x06, 0x0A, 0x0E])
        mac_bytes = [first_byte] + [random.randint(0x00, 0xFF) for _ in range(5)]
        mac_str = ':'.join(f'{b:02x}' for b in mac_bytes)
        self.query_one("#mac-input", Input).value = mac_str

    def change_mac(self):
        iface = self.query_one("#iface-select", Select).value
        new_mac = self.query_one("#mac-input", Input).value
        
        if not iface or not new_mac:
            self.notify("Selecciona interfaz y escribe MAC", severity="warning")
            return
            
        # Validate MAC format
        if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", new_mac):
            self.notify("Formato de MAC inválido", severity="error")
            return

        self.query_one("#status-box", Static).update(f"⏳ Cambiando MAC de {iface} a {new_mac}...")
        
        # Run in worker to avoid freezing
        self.run_worker(lambda: self._perform_mac_change(iface, new_mac), thread=True)

    def _perform_mac_change(self, iface, new_mac):
        import platform
        system = platform.system()
        
        try:
            if system == "Linux":
                subprocess.run(['ip', 'link', 'set', 'dev', iface, 'down'], check=True)
                subprocess.run(['ip', 'link', 'set', 'dev', iface, 'address', new_mac], check=True)
                subprocess.run(['ip', 'link', 'set', 'dev', iface, 'up'], check=True)
                
            elif system == "Darwin":
                # sudo ifconfig en0 ether xx:xx:xx:xx:xx:xx
                # Note: macOS often disassociates WiFi when changing MAC
                subprocess.run(['ifconfig', iface, 'ether', new_mac], check=True)
                
            elif system == "Windows":
                self.app.call_from_thread(self.notify, "Cambio de MAC no soportado en Windows CLI automáticamente.", severity="error")
                self.app.call_from_thread(self.query_one("#status-box", Static).update, 
                                        "[yellow]En Windows, usa el Administrador de Dispositivos o herramientas de terceros (TMAC).[/]")
                return

            self.app.call_from_thread(self.notify, "¡MAC cambiada con éxito!", severity="information")
            self.app.call_from_thread(self.update_current_mac, iface)
            self.app.call_from_thread(self.query_one("#status-box", Static).update, 
                                    f"[bold green]¡ÉXITO![/]\nLa MAC de {iface} ahora es {new_mac}")
            
        except subprocess.CalledProcessError as e:
            self.app.call_from_thread(self.notify, "Error al cambiar MAC", severity="error")
            self.app.call_from_thread(self.query_one("#status-box", Static).update, 
                                    f"[bold red]ERROR:[/]\n{e}")
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error inesperado: {e}", severity="error")

    def restore_mac(self):
        # To restore "permanent" MAC, we can try getting it from ethtool -P or similar, 
        # but simpler is to tell user to reboot or use specific tool logic.
        # For now, let's just warn.
        self.notify("Para restaurar la original, reinicia el equipo o usa la MAC permanente.", severity="information")
        
        iface = self.query_one("#iface-select", Select).value
        if iface:
             # Try to get permanent MAC
            try:
                res = subprocess.run(['ethtool', '-P', iface], capture_output=True, text=True)
                if "Permanent address" in res.stdout:
                    perm_mac = res.stdout.split(": ")[1].strip()
                    self.query_one("#mac-input", Input).value = perm_mac
                    self.notify(f"MAC Permanente detectada: {perm_mac}")
                else:
                    self.notify("No se pudo detectar MAC permanente (requiere ethtool)", severity="warning")
            except:
                self.notify("Instala 'ethtool' para detectar MAC original", severity="warning")

def main():
    app = MacChangerApp()
    app.run()

if __name__ == "__main__":
    main()
