"""
Verificador de conectividad a internet
Comprueba conectividad, DNS, latencia y detecta proxies/VPN
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
import socket
import requests
import subprocess
import time
from platform_utils import get_ping_command, is_windows, check_vpn_interface

class ConnectivityChecker(App):
    """Aplicación para verificar conectividad a internet"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #results {
        height: 100%;
        overflow-y: auto;
        padding: 1 2;
    }
    
    .result-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        height: auto;
    }
    
    .status-ok {
        color: $success;
    }
    
    .status-error {
        color: $error;
    }
    
    .status-warning {
        color: $warning;
    }
    
    #button-container {
        height: auto;
        padding: 1 2;
        align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "check", "Verificar"),
        Binding("ctrl+c", "quit", "Salir"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="results"):
            yield Static("Pulsa 'r' para iniciar verificación de conectividad...", id="output")
        with Horizontal(id="button-container"):
            yield Button("🔄 Verificar Conectividad", id="check-btn", variant="primary")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar, ejecutar verificación automática"""
        self.title = "🌐 Verificador de Conectividad"
        self.check_connectivity()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clic en botones"""
        if event.button.id == "check-btn":
            self.check_connectivity()
    
    def action_check(self) -> None:
        """Ejecutar verificación"""
        self.check_connectivity()
    
    def check_connectivity(self) -> None:
        """Verificar conectividad a internet"""
        output = self.query_one("#output", Static)
        output.update("🔍 Verificando conectividad...\n\n")
        
        results = []
        
        # 1. Verificar conexión básica a internet
        results.append("[bold cyan]═══ CONECTIVIDAD A INTERNET ═══[/]\n")
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            results.append("[bold green]✓[/] Conexión a internet: [green]ACTIVA[/]")
        except OSError:
            results.append("[bold red]✗[/] Conexión a internet: [red]NO DISPONIBLE[/]")
            output.update("\n".join(results))
            return
        
        # 2. Verificar servidores DNS principales
        results.append("\n[bold cyan]═══ SERVIDORES DNS ═══[/]")
        dns_servers = [
            ("Google DNS", "8.8.8.8"),
            ("Cloudflare", "1.1.1.1"),
            ("Quad9", "9.9.9.9"),
            ("OpenDNS", "208.67.222.222"),
        ]
        
        for name, ip in dns_servers:
            try:
                start = time.time()
                socket.create_connection((ip, 53), timeout=2)
                latency = (time.time() - start) * 1000
                results.append(f"[green]✓[/] {name} ({ip}): [green]{latency:.1f}ms[/]")
            except:
                results.append(f"[red]✗[/] {name} ({ip}): [red]No responde[/]")
        
        # 3. Verificar resolución DNS
        results.append("\n[bold cyan]═══ RESOLUCIÓN DNS ═══[/]")
        test_domains = ["google.com", "github.com", "cloudflare.com"]
        
        for domain in test_domains:
            try:
                start = time.time()
                socket.gethostbyname(domain)
                latency = (time.time() - start) * 1000
                results.append(f"[green]✓[/] {domain}: [green]{latency:.1f}ms[/]")
            except:
                results.append(f"[red]✗[/] {domain}: [red]Fallo en resolución[/]")
        
        # 4. Verificar latencia HTTP
        results.append("\n[bold cyan]═══ LATENCIA HTTP/HTTPS ═══[/]")
        http_tests = [
            ("Google", "https://www.google.com"),
            ("GitHub", "https://api.github.com"),
            ("Cloudflare", "https://1.1.1.1"),
        ]
        
        for name, url in http_tests:
            try:
                start = time.time()
                response = requests.get(url, timeout=5)
                latency = (time.time() - start) * 1000
                status = "OK" if response.status_code < 400 else "Error"
                color = "green" if response.status_code < 400 else "red"
                results.append(f"[{color}]✓[/] {name}: [{color}]{latency:.0f}ms ({response.status_code})[/]")
            except Exception as e:
                results.append(f"[red]✗[/] {name}: [red]Sin respuesta[/]")
        
        # 5. Detectar proxy
        results.append("\n[bold cyan]═══ CONFIGURACIÓN DE RED ═══[/]")
        try:
            import os
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            if http_proxy or https_proxy:
                results.append(f"[yellow]⚠[/] Proxy detectado:")
                if http_proxy:
                    results.append(f"  HTTP: [yellow]{http_proxy}[/]")
                if https_proxy:
                    results.append(f"  HTTPS: [yellow]{https_proxy}[/]")
            else:
                results.append("[green]✓[/] Sin proxy configurado")
        except:
            results.append("[dim]No se pudo verificar proxy[/]")
        
        # 6. Verificar IP pública
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                ip_data = response.json()
                results.append(f"[green]✓[/] IP pública: [cyan]{ip_data['ip']}[/]")
        except:
            results.append("[yellow]⚠[/] No se pudo obtener la IP pública")
        
        # 7. Detectar VPN (heurística simple)
        vpn_detected, vpn_message = check_vpn_interface()
        if vpn_detected:
            results.append(f"[yellow]⚠[/] {vpn_message}")
        else:
            results.append(f"[green]✓[/] {vpn_message}")
        
        results.append("\n[dim]Pulsa 'r' para actualizar | 'q' para salir[/]")
        output.update("\n".join(results))

if __name__ == "__main__":
    app = ConnectivityChecker()
    app.run()
