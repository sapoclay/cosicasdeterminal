"""
Muestra hostname, gateway, DNS, rutas y VPN
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
import socket
import subprocess
import netifaces
import platform
from platform_utils import get_firewall_status, is_windows, get_dns_servers, get_route_command

class NetworkSystemInfo(App):
    """Aplicación para mostrar información del sistema de red"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #content {
        height: 100%;
        overflow-y: auto;
        padding: 1 2;
    }
    
    .info-section {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        height: auto;
    }
    
    #button-container {
        height: auto;
        padding: 1;
        align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "refresh", "Actualizar"),
        Binding("ctrl+c", "quit", "Salir"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="content"):
            yield Static("Cargando información del sistema...", id="info")
        with Horizontal(id="button-container"):
            yield Button("🔄 Actualizar", id="refresh-btn", variant="primary")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar, cargar información"""
        self.title = "🖥️ Información del Sistema de Red"
        self.refresh_info()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clic en botones"""
        if event.button.id == "refresh-btn":
            self.refresh_info()
    
    def action_refresh(self) -> None:
        """Actualizar información"""
        self.refresh_info()
    
    def get_dns_servers(self) -> list:
        """Obtener servidores DNS configurados"""
        return get_dns_servers()
    
    def get_routing_table(self) -> list:
        """Obtener tabla de enrutamiento simplificada"""
        routes = []
        try:
            result = subprocess.run(
                get_route_command(),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n')[:10]:  # Top 10 rutas
                    routes.append(line)
        except:
            routes = ['No disponible']
        
        return routes
    
    def check_vpn_connections(self) -> list:
        """Detectar conexiones VPN activas"""
        vpn_info = []
        
        try:
            # Buscar interfaces tun/tap
            interfaces = netifaces.interfaces()
            vpn_interfaces = [i for i in interfaces if i.startswith(('tun', 'tap', 'vpn'))]
            
            for iface in vpn_interfaces:
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    vpn_info.append(f"{iface}: {ip}")
        except:
            pass
        
        return vpn_info if vpn_info else ['No detectadas']
    
    def refresh_info(self) -> None:
        """Actualizar información del sistema"""
        info_widget = self.query_one("#info", Static)
        
        results = []
        
        # 1. Información básica del sistema
        results.append("[bold cyan]═══ INFORMACIÓN DEL SISTEMA ═══[/]\n")
        
        try:
            hostname = socket.gethostname()
            fqdn = socket.getfqdn()
            results.append(f"[bold]Hostname:[/] [cyan]{hostname}[/]")
            if fqdn != hostname:
                results.append(f"[bold]FQDN:[/] [cyan]{fqdn}[/]")
        except:
            results.append("[red]Error obteniendo hostname[/]")
        
        # Sistema operativo
        results.append(f"[bold]Sistema:[/] {platform.system()} {platform.release()}")
        results.append(f"[bold]Arquitectura:[/] {platform.machine()}")
        
        # 2. Gateway predeterminado
        results.append("\n[bold cyan]═══ GATEWAY PREDETERMINADO ═══[/]\n")
        try:
            gateways = netifaces.gateways()
            default_gw = gateways.get('default', {})
            
            if netifaces.AF_INET in default_gw:
                gw_data = default_gw[netifaces.AF_INET]
                gw_ip = gw_data[0]
                gw_iface = gw_data[1]
                results.append(f"[bold]IPv4:[/] [green]{gw_ip}[/] (via {gw_iface})")
            else:
                results.append("[yellow]No configurado[/]")
            
            if netifaces.AF_INET6 in default_gw:
                gw_data6 = default_gw[netifaces.AF_INET6]
                gw_ip6 = gw_data6[0]
                gw_iface6 = gw_data6[1]
                results.append(f"[bold]IPv6:[/] [green]{gw_ip6}[/] (via {gw_iface6})")
        except Exception as e:
            results.append(f"[red]Error: {str(e)}[/]")
        
        # 3. Servidores DNS
        results.append("\n[bold cyan]═══ SERVIDORES DNS ═══[/]\n")
        dns_servers = self.get_dns_servers()
        for i, dns in enumerate(dns_servers, 1):
            results.append(f"[bold]{i}.[/] [cyan]{dns}[/]")
        
        # 4. Direcciones IP locales
        results.append("\n[bold cyan]═══ DIRECCIONES IP LOCALES ═══[/]\n")
        try:
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr.get('addr')
                        if ip and not ip.startswith('127.'):
                            results.append(f"[bold]{iface}:[/] [cyan]{ip}[/]")
        except:
            results.append("[red]Error obteniendo IPs[/]")
        
        # 5. Conexiones VPN
        results.append("\n[bold cyan]═══ CONEXIONES VPN ═══[/]\n")
        vpn_connections = self.check_vpn_connections()
        for vpn in vpn_connections:
            if vpn == 'No detectadas':
                results.append(f"[dim]{vpn}[/]")
            else:
                results.append(f"[green]✓[/] {vpn}")
        
        # 6. Tabla de enrutamiento
        results.append("\n[bold cyan]═══ TABLA DE ENRUTAMIENTO (Top 10) ═══[/]\n")
        routes = self.get_routing_table()
        for route in routes[:10]:
            if route == 'No disponible':
                results.append(f"[dim]{route}[/]")
            else:
                results.append(f"[dim]{route}[/]")
        
        # 7. Puertos y servicios del firewall
        results.append("\n[bold cyan]═══ FIREWALL ═══[/]\n")
        firewall_status = get_firewall_status()
        results.append(firewall_status)
        
        results.append("\n[dim]Pulsa 'r' para actualizar | 'q' para salir[/]")
        info_widget.update("\n".join(results))

if __name__ == "__main__":
    app = NetworkSystemInfo()
    app.run()
