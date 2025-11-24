"""
Escáner WiFi (WiFi Scanner)
Escanea redes inalámbricas cercanas usando nmcli
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, DataTable, Label
from textual.binding import Binding
import subprocess
import shutil
import os

class WifiScannerApp(App):
    """Aplicación de Escáner WiFi"""
    
    TITLE = "📡 Escáner WiFi"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        padding: 1 2;
    }
    
    DataTable {
        height: 1fr;
        border: solid $primary;
    }
    
    #controls {
        height: auto;
        padding: 1;
        background: $panel;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "scan_wifi", "Escanear"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with ScrollableContainer(id="main-container"):
            yield Static("📡 ESCÁNER DE REDES WIFI", classes="title")
            
            with Horizontal(id="controls"):
                yield Button("🔄 Escanear Redes", id="btn-scan", variant="primary")
                yield Static("  (Requiere NetworkManager/nmcli)", classes="description")
            
            yield DataTable(zebra_stripes=True)
        
        yield Footer()
        
    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("SSID", "BSSID", "Canal", "Señal", "Seguridad", "Barras")
        
        if not shutil.which("nmcli"):
            self.notify("Error: 'nmcli' no encontrado. Instala NetworkManager.", severity="error", timeout=10)
        else:
            self.scan_wifi()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-scan":
            self.scan_wifi()

    def scan_wifi(self):
        self.notify("Escaneando redes...")
        table = self.query_one(DataTable)
        table.clear()
        
        self.run_worker(self._perform_scan, thread=True)

    def _perform_scan(self):
        import platform
        system = platform.system()
        
        try:
            if system == "Linux":
                self._scan_linux()
            elif system == "Windows":
                self._scan_windows()
            elif system == "Darwin": # macOS
                self._scan_macos()
            else:
                self.app.call_from_thread(self.notify, f"Sistema no soportado: {system}", severity="error")
                
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error: {e}", severity="error")

    def _scan_linux(self):
        # Force rescan
        subprocess.run(['nmcli', 'dev', 'wifi', 'rescan'], capture_output=True)
        
        # Get list
        cmd = ['nmcli', '-t', '-f', 'SSID,BSSID,CHAN,SIGNAL,SECURITY,BARS', 'dev', 'wifi', 'list']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.app.call_from_thread(self.notify, "Error al escanear. ¿Tienes permisos?", severity="error")
            return

        self._parse_nmcli_output(result.stdout)

    def _scan_windows(self):
        # netsh wlan show networks mode=bssid
        cmd = ['netsh', 'wlan', 'show', 'networks', 'mode=bssid']
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='cp850', errors='replace') # Windows encoding
        
        if result.returncode != 0:
            self.app.call_from_thread(self.notify, "Error al ejecutar netsh", severity="error")
            return
            
        self._parse_windows_output(result.stdout)

    def _scan_macos(self):
        # airport utility
        airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if not os.path.exists(airport_path):
             self.app.call_from_thread(self.notify, "Herramienta 'airport' no encontrada", severity="error")
             return
             
        cmd = [airport_path, '-s']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.app.call_from_thread(self.notify, "Error al ejecutar airport", severity="error")
            return
            
        self._parse_macos_output(result.stdout)

    def _parse_nmcli_output(self, output):
        table = self.query_one(DataTable)
        lines = output.split('\n')
        count = 0
        
        for line in lines:
            if not line.strip(): continue
            parts = self.parse_nmcli_line(line)
            
            if len(parts) >= 6:
                ssid = parts[0]
                bssid = parts[1]
                chan = parts[2]
                signal = parts[3]
                security = parts[4]
                bars = parts[5]
                
                self._add_row(ssid, bssid, chan, signal, security, bars)
                count += 1
        
        self.app.call_from_thread(self.notify, f"Escaneo completado. {count} redes encontradas.")

    def _parse_windows_output(self, output):
        # Parse netsh output
        # SSID 1 : WiFiName
        # ...
        #     BSSID 1         : 00:11:22:33:44:55
        #     Signal          : 99%
        #     Channel         : 11
        #     Authentication  : WPA2-Personal
        
        lines = output.split('\n')
        current_ssid = ""
        networks = []
        current_net = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("SSID"):
                if current_net and "BSSID" in current_net: # Save previous if complete
                     self._add_row(current_net.get("SSID", ""), current_net.get("BSSID", ""), 
                                 current_net.get("Channel", ""), current_net.get("Signal", ""), 
                                 current_net.get("Auth", ""), "")
                
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_ssid = parts[1].strip()
                    current_net = {"SSID": current_ssid}
            elif line.startswith("BSSID"):
                parts = line.split(":", 1)
                if len(parts) > 1: current_net["BSSID"] = parts[1].strip()
            elif line.startswith("Signal"):
                parts = line.split(":", 1)
                if len(parts) > 1: current_net["Signal"] = parts[1].strip().replace("%", "")
            elif line.startswith("Channel"):
                parts = line.split(":", 1)
                if len(parts) > 1: current_net["Channel"] = parts[1].strip()
            elif line.startswith("Authentication"):
                parts = line.split(":", 1)
                if len(parts) > 1: current_net["Auth"] = parts[1].strip()
                
        # Add last one
        if current_net and "BSSID" in current_net:
             self._add_row(current_net.get("SSID", ""), current_net.get("BSSID", ""), 
                         current_net.get("Channel", ""), current_net.get("Signal", ""), 
                         current_net.get("Auth", ""), "")
                         
        self.app.call_from_thread(self.notify, "Escaneo Windows completado.")

    def _parse_macos_output(self, output):
        # SSID BSSID RSSI CHANNEL HT CC SECURITY (WEP/WPA/WPA2/WPA3)
        lines = output.split('\n')
        # Skip header
        for line in lines[1:]:
            if not line.strip(): continue
            # Fixed width parsing is safer for airport output but split might work if SSID has no spaces
            # Actually SSID can have spaces. Airport output is column aligned.
            # Simple approach: split and assume last columns are fixed
            parts = line.split()
            if len(parts) < 6: continue
            
            # SSID is everything up to BSSID (mac address format)
            # Find BSSID index (pattern xx:xx:xx:xx:xx:xx)
            bssid_idx = -1
            for i, part in enumerate(parts):
                if len(part) == 17 and part.count(':') == 5:
                    bssid_idx = i
                    break
            
            if bssid_idx != -1:
                ssid = " ".join(parts[:bssid_idx])
                bssid = parts[bssid_idx]
                rssi = parts[bssid_idx+1]
                chan = parts[bssid_idx+2]
                security = " ".join(parts[bssid_idx+4:])
                
                # Convert RSSI to % roughly
                try:
                    rssi_val = int(rssi)
                    signal = str(min(100, max(0, 2 * (rssi_val + 100))))
                except: signal = "?"
                
                self._add_row(ssid, bssid, chan, signal, security, "")

        self.app.call_from_thread(self.notify, "Escaneo macOS completado.")

    def _add_row(self, ssid, bssid, chan, signal, security, bars):
        table = self.query_one(DataTable)
        
        # Colorize signal
        try:
            sig_int = int(signal)
            if sig_int > 70: signal = f"[green]{signal}%[/]"
            elif sig_int > 40: signal = f"[yellow]{signal}%[/]"
            else: signal = f"[red]{signal}%[/]"
        except: pass
        
        self.app.call_from_thread(table.add_row, ssid, bssid, chan, signal, security, bars)

    def parse_nmcli_line(self, line):
        # Handle escaped colons "\:"
        parts = []
        current = ""
        escape = False
        for char in line:
            if escape:
                current += char
                escape = False
            elif char == '\\':
                escape = True
            elif char == ':':
                parts.append(current)
                current = ""
            else:
                current += char
        parts.append(current)
        return parts

def main():
    app = WifiScannerApp()
    app.run()

if __name__ == "__main__":
    main()
