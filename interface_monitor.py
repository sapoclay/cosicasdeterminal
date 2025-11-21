"""
Muestra todas las interfaces, estados, IPs, MACs y estadísticas
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Static, Button, DataTable
from textual.binding import Binding
import psutil
import netifaces
import socket

class NetworkInterfaceMonitor(App):
    """Aplicación para monitorear interfaces de red"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #info-container {
        height: 100%;
        overflow-y: auto;
        padding: 1 2;
    }
    
    .interface-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        height: auto;
    }
    
    .active {
        border: solid $success;
    }
    
    .inactive {
        border: solid $error;
    }
    
    #button-container {
        height: auto;
        padding: 1;
        align: center middle;
    }
    
    DataTable {
        height: auto;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "refresh", "Actualizar"),
        Binding("ctrl+c", "quit", "Salir"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="info-container"):
            yield Static("Cargando información de interfaces...", id="output")
        with Horizontal(id="button-container"):
            yield Button("🔄 Actualizar", id="refresh-btn", variant="primary")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar, cargar información de interfaces"""
        self.title = "📡 Monitor de interfaces de red"
        self.refresh_interfaces()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clic en botones"""
        if event.button.id == "refresh-btn":
            self.refresh_interfaces()
    
    def action_refresh(self) -> None:
        """Actualizar información"""
        self.refresh_interfaces()
    
    def get_interface_type(self, name: str) -> str:
        """Determinar tipo de interfaz"""
        name_lower = name.lower()
        if name_lower.startswith('lo'):
            return "🔁 Loopback"
        elif name_lower.startswith(('eth', 'en')):
            return "🔌 Ethernet"
        elif name_lower.startswith(('wlan', 'wl', 'wifi')):
            return "📶 WiFi"
        elif name_lower.startswith(('tun', 'tap')):
            return "🔒 VPN"
        elif name_lower.startswith('docker'):
            return "🐳 Docker"
        elif name_lower.startswith('br'):
            return "🌉 Bridge"
        elif name_lower.startswith('veth'):
            return "🔗 Virtual"
        else:
            return "❓ Otro"
    
    def refresh_interfaces(self) -> None:
        """Actualizar información de interfaces"""
        output = self.query_one("#output", Static)
        
        results = []
        results.append("[bold cyan]═══ INTERFACES DE RED DEL SISTEMA ═══[/]\n")
        
        # Obtener estadísticas de red
        net_io = psutil.net_io_counters(pernic=True)
        
        # Obtener todas las interfaces
        interfaces = netifaces.interfaces()
        
        active_count = 0
        inactive_count = 0
        
        for iface in interfaces:
            addrs = netifaces.ifaddresses(iface)
            
            # Determinar si está activa
            stats = psutil.net_if_stats().get(iface)
            is_up = stats.isup if stats else False
            
            if is_up:
                active_count += 1
                status_icon = "[green]🟢[/]"
                status_text = "[green]ACTIVA[/]"
            else:
                inactive_count += 1
                status_icon = "[red]🔴[/]"
                status_text = "[red]INACTIVA[/]"
            
            iface_type = self.get_interface_type(iface)
            
            results.append(f"\n[bold]{status_icon} {iface}[/] - {iface_type}")
            results.append(f"Estado: {status_text}")
            
            # Dirección IPv4
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get('addr', 'N/A')
                    netmask = addr.get('netmask', 'N/A')
                    broadcast = addr.get('broadcast', 'N/A')
                    results.append(f"  IPv4: [cyan]{ip}[/]")
                    results.append(f"  Máscara: {netmask}")
                    if broadcast != 'N/A':
                        results.append(f"  Broadcast: {broadcast}")
            
            # Dirección IPv6
            if netifaces.AF_INET6 in addrs:
                for addr in addrs[netifaces.AF_INET6]:
                    ip6 = addr.get('addr', 'N/A')
                    results.append(f"  IPv6: [cyan]{ip6.split('%')[0]}[/]")
            
            # Dirección MAC
            if netifaces.AF_LINK in addrs:
                for addr in addrs[netifaces.AF_LINK]:
                    mac = addr.get('addr', 'N/A')
                    if mac != 'N/A' and mac != '00:00:00:00:00:00':
                        results.append(f"  MAC: [yellow]{mac}[/]")
            
            # MTU y velocidad
            if stats:
                results.append(f"  MTU: {stats.mtu} bytes")
                if stats.speed > 0:
                    results.append(f"  Velocidad: {stats.speed} Mbps")
            
            # Estadísticas de tráfico
            if iface in net_io:
                io = net_io[iface]
                sent_mb = io.bytes_sent / (1024 * 1024)
                recv_mb = io.bytes_recv / (1024 * 1024)
                results.append(f"  📤 Enviados: [green]{sent_mb:.2f} MB[/] ({io.packets_sent:,} paquetes)")
                results.append(f"  📥 Recibidos: [blue]{recv_mb:.2f} MB[/] ({io.packets_recv:,} paquetes)")
                
                if io.errin > 0 or io.errout > 0:
                    results.append(f"  [red]⚠ Errores: {io.errin + io.errout}[/]")
                if io.dropin > 0 or io.dropout > 0:
                    results.append(f"  [yellow]⚠ Paquetes perdidos: {io.dropin + io.dropout}[/]")
        
        # Resumen
        results.append(f"\n[bold cyan]═══ RESUMEN ═══[/]")
        results.append(f"Total de interfaces: [cyan]{len(interfaces)}[/]")
        results.append(f"Activas: [green]{active_count}[/]")
        results.append(f"Inactivas: [red]{inactive_count}[/]")
        
        # Gateway predeterminado
        try:
            gateways = netifaces.gateways()
            default_gw = gateways.get('default', {})
            if netifaces.AF_INET in default_gw:
                gw_data = default_gw[netifaces.AF_INET]
                gw_ip = gw_data[0]
                gw_iface = gw_data[1]
                results.append(f"\nGateway predeterminado: [cyan]{gw_ip}[/] (vía {gw_iface})")
        except:
            pass
        
        results.append("\n[dim]Pulsa 'r' para actualizar | 'q' para salir[/]")
        output.update("\n".join(results))

if __name__ == "__main__":
    app = NetworkInterfaceMonitor()
    app.run()
