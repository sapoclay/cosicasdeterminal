"""
Ping, Traceroute, Port Scanner, DNS Lookup, etc.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Select, TabbedContent, TabPane, Label
from textual.binding import Binding
import socket
import subprocess
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from platform_utils import (get_ping_command, get_traceroute_command, 
                           get_dns_lookup_command, check_whois_available,
                           get_whois_command, is_windows)


class NetworkToolsApp(App):
    """Aplicación de herramientas de diagnóstico de red"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    #header-section {
        height: auto;
        width: 100%;
        background: $primary;
        padding: 1 2;
        margin-bottom: 1;
        content-align: center middle;
    }
    
    TabbedContent {
        width: 100%;
        height: 1fr;
        margin-bottom: 1;
    }
    
    TabPane {
        padding: 1 2;
    }
    
    .tool-controls {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }
    
    .tool-output {
        height: 1fr;
        width: 100%;
        border: solid $primary;
        padding: 1 2;
    }
    
    Input {
        width: 1fr;
        margin-right: 1;
    }
    
    Button {
        width: auto;
        min-width: 15;
    }
    
    Label {
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("ctrl+c", "cancel", "Cancelar", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.running = False
    
    def compose(self) -> ComposeResult:
        """Compone la interfaz de usuario"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="header-section"):
                yield Static("🛠️ HERRAMIENTAS DE DIAGNÓSTICO DE RED")
            
            with TabbedContent():
                # Tab 1: Ping
                with TabPane("🏓 Ping", id="ping-tab"):
                    yield Label("[bold]Enviar pings a un host[/]")
                    with Horizontal(classes="tool-controls"):
                        yield Input(placeholder="Ej: google.com o 8.8.8.8", id="ping-input")
                        yield Button("Ejecutar", variant="success", id="ping-btn")
                    with ScrollableContainer(classes="tool-output"):
                        yield Static("El resultado aparecerá aquí...", id="ping-output")
                
                # Tab 2: Traceroute
                with TabPane("🗺️ Traceroute", id="trace-tab"):
                    yield Label("[bold]Rastrear ruta a un host[/]")
                    with Horizontal(classes="tool-controls"):
                        yield Input(placeholder="Ej: google.com", id="trace-input")
                        yield Button("Ejecutar", variant="success", id="trace-btn")
                    with ScrollableContainer(classes="tool-output"):
                        yield Static("El resultado aparecerá aquí...", id="trace-output")
                
                # Tab 3: DNS Lookup
                with TabPane("🔍 DNS Lookup", id="dns-tab"):
                    yield Label("[bold]Resolver nombre de dominio[/]")
                    with Horizontal(classes="tool-controls"):
                        yield Input(placeholder="Ej: google.com", id="dns-input")
                        yield Button("Resolver", variant="success", id="dns-btn")
                    with ScrollableContainer(classes="tool-output"):
                        yield Static("El resultado aparecerá aquí...", id="dns-output")
                
                # Tab 4: Port Scanner
                with TabPane("🔌 Port Scanner", id="port-tab"):
                    yield Label("[bold]Escanear puertos abiertos[/]")
                    with Horizontal(classes="tool-controls"):
                        yield Input(placeholder="Host (Ej: 192.168.1.1)", id="port-host-input")
                        yield Input(placeholder="Puertos (Ej: 80,443,22)", id="port-range-input")
                        yield Button("Escanear", variant="success", id="port-btn")
                    with ScrollableContainer(classes="tool-output"):
                        yield Static("El resultado aparecerá aquí...", id="port-output")
                
                # Tab 5: Whois
                with TabPane("ℹ️ Whois", id="whois-tab"):
                    yield Label("[bold]Información de dominio/IP[/]")
                    with Horizontal(classes="tool-controls"):
                        yield Input(placeholder="Ej: google.com o 8.8.8.8", id="whois-input")
                        yield Button("Consultar", variant="success", id="whois-btn")
                    with ScrollableContainer(classes="tool-output"):
                        yield Static("El resultado aparecerá aquí...", id="whois-output")
                
                # Tab 6: IP Info
                with TabPane("🌐 Mi IP", id="myip-tab"):
                    yield Label("[bold]Información de tu conexión[/]")
                    with Horizontal(classes="tool-controls"):
                        yield Button("🔄 Obtener Info", variant="primary", id="myip-btn")
                    with ScrollableContainer(classes="tool-output"):
                        yield Static("Presiona el botón para obtener tu información...", id="myip-output")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Se ejecuta cuando la aplicación se monta"""
        self.query_one("#ping-input").focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "ping-btn":
            self.run_ping()
        elif event.button.id == "trace-btn":
            self.run_traceroute()
        elif event.button.id == "dns-btn":
            self.run_dns_lookup()
        elif event.button.id == "port-btn":
            self.run_port_scan()
        elif event.button.id == "whois-btn":
            self.run_whois()
        elif event.button.id == "myip-btn":
            self.run_myip()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Maneja enter en inputs"""
        if event.input.id == "ping-input":
            self.run_ping()
        elif event.input.id == "trace-input":
            self.run_traceroute()
        elif event.input.id == "dns-input":
            self.run_dns_lookup()
        elif event.input.id == "whois-input":
            self.run_whois()
    
    def run_ping(self) -> None:
        """Ejecuta ping"""
        if self.running:
            self.notify("Ya hay una operación en curso", severity="warning")
            return
        
        input_widget = self.query_one("#ping-input", Input)
        host = input_widget.value.strip()
        
        if not host:
            self.notify("Ingresa un host", severity="error")
            return
        
        self.running = True
        output = self.query_one("#ping-output", Static)
        output.update(f"⏳ Ejecutando ping a {host}...\n")
        
        from functools import partial
        worker_func = partial(self.execute_ping, host)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def execute_ping(self, host: str) -> str:
        """Ejecuta el comando ping"""
        try:
            result = subprocess.run(
                get_ping_command(host, count=5),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output = f"[bold cyan]Ping a {host}[/] - {timestamp}\n\n"
            output += result.stdout
            
            if result.returncode == 0:
                output += "\n[green]✅ Ping exitoso[/]"
            else:
                output += "\n[red]❌ Ping falló[/]"
            
            return output
            
        except subprocess.TimeoutExpired:
            return f"[red]❌ Timeout: El host no responde[/]"
        except Exception as e:
            return f"[red]❌ Error: {e}[/]"
    
    def run_traceroute(self) -> None:
        """Ejecuta traceroute"""
        if self.running:
            self.notify("Ya hay una operación en curso", severity="warning")
            return
        
        input_widget = self.query_one("#trace-input", Input)
        host = input_widget.value.strip()
        
        if not host:
            self.notify("Ingresa un host", severity="error")
            return
        
        self.running = True
        output = self.query_one("#traceroute-output", Static)
        output.update(f"⏳ Ejecutando traceroute a {host}...\n")
        
        from functools import partial
        worker_func = partial(self.execute_traceroute, host)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def execute_traceroute(self, host: str) -> str:
        """Ejecuta traceroute"""
        try:
            # Usar comando apropiado según plataforma
            cmd = get_traceroute_command(host)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output = f"[bold cyan]Traceroute a {host}[/] - {timestamp}\n\n"
            output += result.stdout if result.stdout else result.stderr
            
            return output
            
        except subprocess.TimeoutExpired:
            return f"[red]❌ Timeout: La operación tomó demasiado tiempo[/]"
        except Exception as e:
            return f"[red]❌ Error: {e}[/]"
    
    def run_dns_lookup(self) -> None:
        """Ejecuta DNS lookup"""
        input_widget = self.query_one("#dns-input", Input)
        host = input_widget.value.strip()
        
        if not host:
            self.notify("Ingresa un dominio", severity="error")
            return
        
        output = self.query_one("#dns-output", Static)
        output.update(f"⏳ Resolviendo {host}...\n")
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = f"[bold cyan]DNS Lookup: {host}[/] - {timestamp}\n\n"
            
            # Resolver IPv4
            try:
                ipv4_list = socket.getaddrinfo(host, None, socket.AF_INET)
                result += "[bold]Direcciones IPv4:[/]\n"
                ipv4_addresses = set(addr[4][0] for addr in ipv4_list)
                for ip in ipv4_addresses:
                    result += f"  • {ip}\n"
            except socket.gaierror:
                result += "[yellow]No se encontraron direcciones IPv4[/]\n"
            
            result += "\n"
            
            # Resolver IPv6
            try:
                ipv6_list = socket.getaddrinfo(host, None, socket.AF_INET6)
                result += "[bold]Direcciones IPv6:[/]\n"
                ipv6_addresses = set(addr[4][0] for addr in ipv6_list)
                for ip in ipv6_addresses:
                    result += f"  • {ip}\n"
            except socket.gaierror:
                result += "[yellow]No se encontraron direcciones IPv6[/]\n"
            
            # Reverse DNS
            try:
                ip = socket.gethostbyname(host)
                reverse = socket.gethostbyaddr(ip)[0]
                result += f"\n[bold]Reverse DNS:[/] {reverse}\n"
            except:
                pass
            
            result += "\n[green]✅ Resolución completada[/]"
            output.update(result)
            self.notify("DNS lookup completado", severity="information")
            
        except socket.gaierror as e:
            output.update(f"[red]❌ Error: No se pudo resolver el dominio\n{e}[/]")
            self.notify("Error en resolución DNS", severity="error")
        except Exception as e:
            output.update(f"[red]❌ Error: {e}[/]")
            self.notify("Error inesperado", severity="error")
    
    def run_port_scan(self) -> None:
        """Ejecuta escaneo de puertos"""
        if self.running:
            self.notify("Ya hay una operación en curso", severity="warning")
            return
        
        host_input = self.query_one("#port-host-input", Input)
        ports_input = self.query_one("#port-range-input", Input)
        
        host = host_input.value.strip()
        ports_str = ports_input.value.strip()
        
        if not host:
            self.notify("Ingresa un host", severity="error")
            return
        
        if not ports_str:
            ports_str = "21,22,23,25,80,443,3306,3389,8080"
        
        # Parsear puertos
        try:
            ports = [int(p.strip()) for p in ports_str.split(',')]
        except ValueError:
            self.notify("Formato de puertos inválido. Usa: 80,443,22", severity="error")
            return
        
        self.running = True
        output = self.query_one("#port-output", Static)
        output.update(f"⏳ Escaneando puertos en {host}...\n")
        
        from functools import partial
        worker_func = partial(self.execute_port_scan, host, ports)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def execute_port_scan(self, host: str, ports: list) -> str:
        """Ejecuta el escaneo de puertos"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = f"[bold cyan]Port Scan: {host}[/] - {timestamp}\n\n"
            result += f"Escaneando {len(ports)} puertos...\n\n"
            
            open_ports = []
            closed_ports = []
            
            def scan_port(port: int) -> tuple:
                """Escanea un puerto específico"""
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                try:
                    result_code = sock.connect_ex((host, port))
                    sock.close()
                    return (port, result_code == 0)
                except:
                    return (port, False)
            
            # Escanear en paralelo
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(scan_port, port): port for port in ports}
                
                for future in as_completed(futures):
                    port, is_open = future.result()
                    if is_open:
                        open_ports.append(port)
                    else:
                        closed_ports.append(port)
            
            # Ordenar puertos
            open_ports.sort()
            closed_ports.sort()
            
            # Mostrar resultados
            if open_ports:
                result += f"[bold green]Puertos ABIERTOS ({len(open_ports)}):[/]\n"
                for port in open_ports:
                    service = self.get_service_name(port)
                    result += f"  🟢 {port:5d} - {service}\n"
            else:
                result += "[yellow]No se encontraron puertos abiertos[/]\n"
            
            result += f"\n[bold red]Puertos CERRADOS: {len(closed_ports)}[/]\n"
            result += "\n[green]✅ Escaneo completado[/]"
            
            return result
            
        except Exception as e:
            return f"[red]❌ Error: {e}[/]"
    
    def run_whois(self) -> None:
        """Ejecuta whois"""
        if self.running:
            self.notify("Ya hay una operación en curso", severity="warning")
            return
        
        input_widget = self.query_one("#whois-input", Input)
        host = input_widget.value.strip()
        
        if not host:
            self.notify("Escribe un dominio o IP", severity="error")
            return
        
        self.running = True
        output = self.query_one("#whois-output", Static)
        output.update(f"⏳ Consultando información whois para {host}...\n")
        
        from functools import partial
        worker_func = partial(self.execute_whois, host)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def execute_whois(self, host: str) -> str:
        """Ejecuta comando whois"""
        try:
            if not check_whois_available():
                msg = "[red]❌ Error: El comando 'whois' no está instalado[/]\n"
                if is_windows():
                    msg += "[yellow]En Windows, descarga whois desde Sysinternals[/]"
                else:
                    msg += "[yellow]Instálalo con: sudo apt install whois[/]"
                return msg
            
            result = subprocess.run(
                get_whois_command(host),
                capture_output=True,
                text=True,
                timeout=15
            )
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output = f"[bold cyan]Whois: {host}[/] - {timestamp}\n\n"
            output += result.stdout
            
            return output
            
        except FileNotFoundError:
            msg = "[red]❌ Error: El comando 'whois' no está instalado[/]\n"
            if is_windows():
                msg += "[yellow]En Windows, descarga whois desde Sysinternals[/]"
            else:
                msg += "[yellow]Instálalo con: sudo apt install whois[/]"
            return msg
        except subprocess.TimeoutExpired:
            return f"[red]❌ Timeout: La consulta tomó demasiado tiempo[/]"
        except Exception as e:
            return f"[red]❌ Error: {e}[/]"
    
    def run_myip(self) -> None:
        """Obtiene información de la IP pública"""
        output = self.query_one("#myip-output", Static)
        output.update("⏳ Obteniendo información...\n")
        
        try:
            import requests
            import netifaces
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = f"[bold cyan]Información de tu conexión[/] - {timestamp}\n\n"
            
            # ==== INFORMACIÓN LOCAL ====
            result += "[bold yellow]═══ INFORMACIÓN LOCAL ═══[/]\n"
            hostname = socket.gethostname()
            result += f"[bold]Hostname:[/] {hostname}\n\n"
            
            # Obtener todas las IPs locales
            result += "[bold]Interfaces de red:[/]\n"
            interfaces = netifaces.interfaces()
            local_ips = []
            
            for interface in interfaces:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr.get('addr')
                        if ip and not ip.startswith('127.'):
                            local_ips.append((interface, ip))
                            result += f"  • [yellow]{interface}[/]: [green]{ip}[/]\n"
            
            if not local_ips:
                # Fallback si no se detectan interfaces
                try:
                    local_ip = socket.gethostbyname(hostname)
                    result += f"  • [yellow]default[/]: [green]{local_ip}[/]\n"
                except:
                    result += "  • [dim]No se detectaron IPs locales[/]\n"
            
            # ==== INFORMACIÓN PÚBLICA ====
            result += "\n[bold cyan]═══ INFORMACIÓN PÚBLICA ═══[/]\n"
            
            try:
                # Intentar obtener IP pública con timeout más largo
                result += "Consultando IP pública...\n"
                output.update(result)
                
                response = requests.get('https://api.ipify.org?format=json', timeout=10)
                public_ip = response.json().get('ip', 'N/A')
                
                if public_ip != 'N/A':
                    result = result.replace("Consultando IP pública...\n", "")
                    result += f"[bold]IP Pública:[/] [green]{public_ip}[/]\n\n"
                    
                    # Intentar obtener geolocalización
                    try:
                        result += "Consultando geolocalización...\n"
                        output.update(result)
                        
                        response = requests.get(f'https://ipapi.co/{public_ip}/json/', timeout=10)
                        data = response.json()
                        
                        result = result.replace("Consultando geolocalización...\n", "")
                        
                        if 'error' not in data:
                            result += f"[bold]País:[/] {data.get('country_name', 'N/A')} ({data.get('country_code', 'N/A')})\n"
                            result += f"[bold]Región:[/] {data.get('region', 'N/A')}\n"
                            result += f"[bold]Ciudad:[/] {data.get('city', 'N/A')}\n"
                            result += f"[bold]Código Postal:[/] {data.get('postal', 'N/A')}\n"
                            result += f"[bold]ISP:[/] {data.get('org', 'N/A')}\n"
                            result += f"[bold]Timezone:[/] {data.get('timezone', 'N/A')}\n"
                            result += f"[bold]Coordenadas:[/] {data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}\n"
                        else:
                            result += "[yellow]⚠️ No se pudo obtener información de geolocalización[/]\n"
                    except requests.exceptions.RequestException as e:
                        result = result.replace("Consultando geolocalización...\n", "")
                        result += f"[yellow]⚠️ No se pudo obtener la geolocalización: {str(e)[:50]}[/]\n"
                else:
                    result = result.replace("Consultando IP pública...\n", "")
                    result += "[yellow]⚠️ No se pudo obtener la IP pública[/]\n"
                    
            except requests.exceptions.ConnectionError:
                result = result.replace("Consultando IP pública...\n", "")
                result += "[red]❌ Error de conexión: Verifica tu conexión a Internet[/]\n"
            except requests.exceptions.Timeout:
                result = result.replace("Consultando IP pública...\n", "")
                result += "[red]❌ Timeout: La conexión tardó demasiado[/]\n"
            except requests.exceptions.RequestException as e:
                result = result.replace("Consultando IP pública...\n", "")
                result += f"[red]❌ Error de red: {str(e)[:100]}[/]\n"
            
            result += "\n[green]✅ Consulta finalizada[/]"
            output.update(result)
            self.notify("Información obtenida", severity="information")
            
        except ImportError as e:
            output.update(f"[red]❌ Error: Falta librería {e}[/]\n[yellow]Instala con: pip install requests netifaces[/]")
            self.notify("Error de importación", severity="error")
        except Exception as e:
            output.update(f"[red]❌ Error inesperado: {e}[/]")
            self.notify("Error al obtener información", severity="error")
    
    def on_worker_state_changed(self, event) -> None:
        """Se ejecuta cuando cambia el estado del worker"""
        if event.state.name == "SUCCESS":
            self.running = False
            # Actualizar output con el resultado
            result = event.worker.result
            
            # Determinar qué output actualizar según la tarea
            if "Ping" in result:
                output = self.query_one("#ping-output", Static)
            elif "Traceroute" in result or "tracepath" in result:
                output = self.query_one("#trace-output", Static)
            elif "Port Scan" in result:
                output = self.query_one("#port-output", Static)
            elif "Whois" in result:
                output = self.query_one("#whois-output", Static)
            else:
                return
            
            output.update(result)
            self.notify("Operación completada", severity="information")
            
        elif event.state.name == "ERROR":
            self.running = False
            self.notify("Error durante la operación", severity="error")
    
    @staticmethod
    def get_service_name(port: int) -> str:
        """Obtiene el nombre del servicio para un puerto"""
        common_ports = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            445: "SMB",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            8080: "HTTP-ALT",
            8443: "HTTPS-ALT",
        }
        return common_ports.get(port, "Unknown")


def main():
    """Función principal para ejecutar la aplicación"""
    app = NetworkToolsApp()
    app.run()


if __name__ == "__main__":
    main()
