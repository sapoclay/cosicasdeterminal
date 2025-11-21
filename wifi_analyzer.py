"""
Muestra redes WiFi disponibles con información detallada
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Static, Button, DataTable
from textual.binding import Binding
import subprocess
import re
from platform_utils import get_wifi_scan_command, is_windows, get_installation_help

class WiFiAnalyzer(App):
    """Aplicación para analizar redes WiFi disponibles"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #content {
        height: 100%;
        overflow-y: auto;
        padding: 1 2;
    }
    
    DataTable {
        height: 80%;
        margin: 1 0;
    }
    
    #summary {
        height: auto;
        padding: 1;
        border: solid $primary;
        margin: 1 0;
    }
    
    #button-container {
        height: auto;
        padding: 1;
        align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "scan", "Escanear"),
        Binding("ctrl+c", "quit", "Salir"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="content"):
            yield Static("Iniciando escaneo de redes WiFi...", id="summary")
            yield DataTable(id="wifi-table")
        with Horizontal(id="button-container"):
            yield Button("🔄 Escanear WiFi", id="scan-btn", variant="primary")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar, configurar tabla y escanear"""
        self.title = "📶 Analizador de WiFi"
        
        table = self.query_one("#wifi-table", DataTable)
        table.add_columns("SSID", "Señal", "Canal", "Frecuencia", "Seguridad", "BSSID")
        table.cursor_type = "row"
        
        self.scan_wifi()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clic en botones"""
        if event.button.id == "scan-btn":
            self.scan_wifi()
    
    def action_scan(self) -> None:
        """Ejecutar escaneo"""
        self.scan_wifi()
    
    def get_signal_icon(self, signal: int) -> str:
        """Obtener icono según fuerza de señal"""
        if signal >= -50:
            return "[green]████[/]"
        elif signal >= -60:
            return "[green]███[/dim]░[/]"
        elif signal >= -70:
            return "[yellow]██[/dim]░░[/]"
        elif signal >= -80:
            return "[red]█[/dim]░░░[/]"
        else:
            return "[dim]░░░░[/]"
    
    def scan_wifi(self) -> None:
        """Escanear redes WiFi disponibles"""
        summary = self.query_one("#summary", Static)
        table = self.query_one("#wifi-table", DataTable)
        
        summary.update("🔍 Escaneando redes WiFi...")
        table.clear()
        
        try:
            # Obtener comando de escaneo WiFi según la plataforma
            wifi_cmd = get_wifi_scan_command()
            
            if not wifi_cmd:
                raise Exception("Escaneo WiFi no soportado en esta plataforma")
            
            result = subprocess.run(
                wifi_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                networks = []
                
                # Parsear según plataforma
                if is_windows():
                    networks = self.parse_netsh(result.stdout)
                else:
                    # Parsear formato nmcli
                    lines = result.stdout.strip().split('\n')[1:]  # Saltar encabezado
                    
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 6:
                            ssid = parts[0] if parts[0] != '--' else '(Oculto)'
                            signal = int(parts[1]) if parts[1].isdigit() else 0
                            channel = parts[2]
                            freq = parts[3] + " MHz"
                            security = parts[4] if parts[4] != '--' else 'Abierta'
                            bssid = parts[5]
                            
                            # Convertir señal de porcentaje a dBm aproximado
                            signal_dbm = -100 + signal
                            signal_display = f"{self.get_signal_icon(signal_dbm)} {signal}%"
                            
                            networks.append({
                                'ssid': ssid,
                                'signal': signal,
                                'signal_display': signal_display,
                                'channel': channel,
                                'freq': freq,
                                'security': security,
                                'bssid': bssid
                            })
                
                # Ordenar por señal
                networks.sort(key=lambda x: x['signal'], reverse=True)
                
                for net in networks:
                    table.add_row(
                        net['ssid'],
                        net['signal_display'],
                        net['channel'],
                        net['freq'],
                        net['security'],
                        net['bssid']
                    )
                
                # Actualizar resumen
                total = len(networks)
                open_nets = sum(1 for n in networks if n['security'] == 'Abierta')
                secure_nets = total - open_nets
                
                # Detectar congestión de canales
                channels = {}
                for net in networks:
                    ch = net['channel']
                    channels[ch] = channels.get(ch, 0) + 1
                
                most_used = max(channels.items(), key=lambda x: x[1]) if channels else (None, 0)
                
                summary_text = f"""[bold cyan]═══ REDES WIFI DETECTADAS ═══[/]

[green]●[/] Total de redes: [cyan]{total}[/]
  • Seguras: [green]{secure_nets}[/]
  • Abiertas: [yellow]{open_nets}[/]

[blue]●[/] Canal más usado: [cyan]{most_used[0]}[/] ({most_used[1]} redes)

[dim]Presiona 'r' para actualizar | 'q' para salir[/]"""
                
                summary.update(summary_text)
                
            else:
                raise Exception("Comando WiFi falló")
                
        except Exception as e:
            if is_windows():
                error_msg = f"""[red]✗[/] No se pudo escanear WiFi

[yellow]Motivos posibles:[/]
  • No hay adaptador WiFi disponible
  • El adaptador WiFi está desactivado
  • El servicio WLAN AutoConfig no está activo

[dim]Verifica tu hardware WiFi en Configuración → Red[/]
{get_installation_help()}"""
            else:
                error_msg = f"""[red]✗[/] No se pudo escanear WiFi

[yellow]Motivos posibles:[/]
  • NetworkManager no está instalado
  • No hay adaptador WiFi disponible
  • Se requieren permisos de root
  • El adaptador está desactivado

[dim]Intenta ejecutar con sudo o verifica tu hardware WiFi[/]
{get_installation_help()}"""
            summary.update(error_msg)
            table.add_row("-", "-", "[dim]No disponible[/]", "-", "-", "-")
    
    def parse_iwlist(self, output: str) -> list:
        """Parsear salida de iwlist"""
        networks = []
        current = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if 'Cell' in line and 'Address:' in line:
                if current:
                    networks.append(current)
                current = {'bssid': line.split('Address: ')[1]}
            elif 'ESSID:' in line:
                ssid = re.search(r'ESSID:"(.+)"', line)
                current['ssid'] = ssid.group(1) if ssid else '(Oculto)'
            elif 'Channel:' in line:
                channel = re.search(r'Channel:(\d+)', line)
                current['channel'] = channel.group(1) if channel else '?'
            elif 'Frequency:' in line:
                freq = re.search(r'Frequency:([\d.]+)', line)
                current['freq'] = f"{freq.group(1)} GHz" if freq else '?'
            elif 'Signal level=' in line:
                signal = re.search(r'Signal level=(-?\d+)', line)
                if signal:
                    signal_dbm = int(signal.group(1))
                    current['signal'] = str(signal_dbm)
                    current['signal_display'] = f"{self.get_signal_icon(signal_dbm)} {signal_dbm}dBm"
            elif 'Encryption key:' in line:
                if 'off' in line.lower():
                    current['security'] = 'Abierta'
                else:
                    current['security'] = 'WPA/WPA2'
        
        if current:
            networks.append(current)
        
        return networks
    
    def parse_netsh(self, output: str) -> list:
        """Parsear salida de netsh wlan show networks mode=bssid (Windows)"""
        networks = []
        current = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith('SSID'):
                if current:
                    networks.append(current)
                # SSID 1 : NetworkName
                parts = line.split(':', 1)
                ssid = parts[1].strip() if len(parts) > 1 else '(Oculto)'
                current = {'ssid': ssid}
            elif 'Authentication' in line:
                auth = line.split(':', 1)[1].strip() if ':' in line else 'Desconocida'
                current['security'] = 'Abierta' if 'Open' in auth else auth
            elif 'Signal' in line:
                # Signal : 100%
                signal_str = line.split(':', 1)[1].strip() if ':' in line else '0%'
                signal = int(signal_str.replace('%', '')) if signal_str.replace('%', '').isdigit() else 0
                signal_dbm = -100 + signal
                current['signal'] = str(signal)
                current['signal_display'] = f"{self.get_signal_icon(signal_dbm)} {signal}%"
            elif 'Channel' in line:
                channel = line.split(':', 1)[1].strip() if ':' in line else '?'
                current['channel'] = channel
            elif 'BSSID' in line:
                bssid = line.split(':', 1)[1].strip() if ':' in line else '?'
                current['bssid'] = bssid
            elif 'Radio type' in line and 'freq' not in current:
                # Estimar frecuencia del tipo de radio
                radio = line.split(':', 1)[1].strip() if ':' in line else ''
                if '802.11a' in radio or '802.11ac' in radio:
                    current['freq'] = '5 GHz'
                else:
                    current['freq'] = '2.4 GHz'
        
        # Añadir última red
        if current:
            # Asegurar que todos los campos existen
            if 'freq' not in current:
                current['freq'] = '?'
            if 'channel' not in current:
                current['channel'] = '?'
            if 'bssid' not in current:
                current['bssid'] = '?'
            networks.append(current)
        
        return networks

if __name__ == "__main__":
    app = WiFiAnalyzer()
    app.run()
