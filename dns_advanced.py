"""
DNS avanzado con Textual
Consulta múltiples tipos de registros DNS y compara servidores
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label, Select
from textual.binding import Binding
import socket
import subprocess
from functools import partial


class DNSAdvancedApp(App):
    """Aplicación de consultas DNS avanzadas"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    #title-section {
        height: auto;
        width: 100%;
        background: $primary;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    .input-section {
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
    
    Select {
        width: 1fr;
    }
    
    Button {
        margin: 0 1;
    }
    
    #results-section {
        height: 1fr;
        border: solid $primary;
        padding: 1 2;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("l", "lookup", "Consultar"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compone la interfaz de usuario"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="title-section"):
                yield Static("🔍 DNS AVANZADO", classes="title")
            
            with Vertical(classes="input-section"):
                yield Static("📝 Configuración de consulta", classes="section-title")
                
                with Horizontal(classes="input-group"):
                    yield Label("Dominio:", classes="input-label")
                    yield Input(placeholder="Ej: google.com", id="domain-input")
                
                with Horizontal(classes="input-group"):
                    yield Label("Tipo de registro:", classes="input-label")
                    yield Select(
                        [
                            ("A - Dirección IPv4", "A"),
                            ("AAAA - Dirección IPv6", "AAAA"),
                            ("MX - Servidores de correo", "MX"),
                            ("TXT - Registros de texto", "TXT"),
                            ("NS - Servidores de nombres", "NS"),
                            ("CNAME - Alias", "CNAME"),
                            ("SOA - Autoridad", "SOA"),
                            ("PTR - Reverso", "PTR"),
                            ("ANY - Todos", "ANY"),
                        ],
                        id="record-type",
                        value="A"
                    )
                
                with Horizontal(classes="input-group"):
                    yield Label("Servidor DNS:", classes="input-label")
                    yield Select(
                        [
                            ("Sistema (por defecto)", "default"),
                            ("Google DNS (8.8.8.8)", "8.8.8.8"),
                            ("Cloudflare (1.1.1.1)", "1.1.1.1"),
                            ("OpenDNS (208.67.222.222)", "208.67.222.222"),
                            ("Quad9 (9.9.9.9)", "9.9.9.9"),
                        ],
                        id="dns-server",
                        value="default"
                    )
                
                with Horizontal(classes="input-group"):
                    yield Button("🔍 Consultar", variant="primary", id="lookup-btn")
                    yield Button("🔄 Comparar servidores", variant="success", id="compare-btn")
                    yield Button("🗑️ Limpiar", variant="warning", id="clear-btn")
            
            with ScrollableContainer(id="results-section"):
                yield Static("Escribe un dominio y selecciona el tipo de registro DNS", id="results")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "lookup-btn":
            self.action_lookup()
        elif event.button.id == "compare-btn":
            self.compare_dns_servers()
        elif event.button.id == "clear-btn":
            self.clear_results()
    
    def action_lookup(self) -> None:
        """Realiza la consulta DNS"""
        domain = self.query_one("#domain-input", Input).value
        record_type = str(self.query_one("#record-type", Select).value)
        dns_server = str(self.query_one("#dns-server", Select).value)
        
        if not domain:
            self.notify("Por favor escribe un dominio", severity="warning")
            return
        
        results_widget = self.query_one("#results", Static)
        results_widget.update(f"⏳ Consultando registros {record_type} para {domain}...\n")
        
        from functools import partial
        worker_func = partial(self.perform_dns_lookup, domain, record_type, dns_server)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def perform_dns_lookup(self, domain: str, record_type: str, dns_server: str) -> dict:
        """Ejecuta la consulta DNS"""
        try:
            result = {
                'domain': domain,
                'record_type': record_type,
                'dns_server': dns_server,
                'records': []
            }
            
            # Construir comando dig o nslookup
            cmd = []
            if dns_server != "default":
                cmd = ['dig', f'@{dns_server}', domain, record_type, '+short']
            else:
                cmd = ['dig', domain, record_type, '+short']
            
            try:
                output = subprocess.check_output(cmd, text=True, timeout=10, stderr=subprocess.DEVNULL)
                records = [line.strip() for line in output.strip().split('\n') if line.strip()]
                result['records'] = records if records else ["Sin registros encontrados"]
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Si dig no está disponible, intentar con Python
                if record_type == "A":
                    try:
                        ips = socket.gethostbyname_ex(domain)[2]
                        result['records'] = ips
                    except:
                        result['records'] = ["Error al resolver"]
                elif record_type == "AAAA":
                    try:
                        ips = socket.getaddrinfo(domain, None, socket.AF_INET6)
                        result['records'] = [ip[4][0] for ip in ips]
                    except:
                        result['records'] = ["No hay registros IPv6 o error"]
                else:
                    result['records'] = ["dig no disponible. Instala: sudo apt-get install dnsutils"]
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def on_worker_state_changed(self, event) -> None:
        """Se ejecuta cuando cambia el estado del worker"""
        if event.state.name == "SUCCESS":
            result = event.worker.result
            if result:
                # Verificar si es una lista (comparación) o dict (consulta simple)
                if isinstance(result, list):
                    self.display_comparison(result)
                elif isinstance(result, dict) and 'error' not in result:
                    self.display_dns_results(result)
                else:
                    error_msg = result.get('error', 'Error desconocido') if isinstance(result, dict) else 'Error desconocido'
                    self.query_one("#results", Static).update(f"[red]Error: {error_msg}[/]")
                    self.notify("Error en la consulta DNS", severity="error")
        elif event.state.name == "ERROR":
            self.query_one("#results", Static).update("[red]Error al realizar la consulta[/]")
            self.notify("Error en la consulta DNS", severity="error")
    
    def display_dns_results(self, result: dict) -> None:
        """Muestra los resultados de la consulta DNS"""
        output = f"[bold cyan]🔍 Resultados DNS[/]\n\n"
        output += f"Dominio:         [yellow]{result['domain']}[/]\n"
        output += f"Tipo de Registro: [green]{result['record_type']}[/]\n"
        
        if result['dns_server'] != "default":
            output += f"Servidor DNS:    [cyan]{result['dns_server']}[/]\n"
        else:
            output += f"Servidor DNS:    [cyan]Sistema (por defecto)[/]\n"
        
        output += f"\n[bold]Registros encontrados:[/]\n\n"
        
        for i, record in enumerate(result['records'], 1):
            output += f"  {i}. {record}\n"
        
        output += f"\nTotal: {len(result['records'])} registro(s)\n"
        
        self.query_one("#results", Static).update(output)
        self.notify(f"Consulta completada: {len(result['records'])} registros", severity="information")
    
    def compare_dns_servers(self) -> None:
        """Compara resultados de múltiples servidores DNS"""
        domain = self.query_one("#domain-input", Input).value
        record_type = str(self.query_one("#record-type", Select).value)
        
        if not domain:
            self.notify("Por favor escribe un dominio", severity="warning")
            return
        
        results_widget = self.query_one("#results", Static)
        results_widget.update(f"⏳ Comparando servidores DNS para {domain}...\n")
        
        from functools import partial
        worker_func = partial(self.compare_servers, domain, record_type)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def compare_servers(self, domain: str, record_type: str) -> list:
        """Compara respuestas de múltiples servidores DNS"""
        servers = {
            'Google DNS': '8.8.8.8',
            'Cloudflare': '1.1.1.1',
            'OpenDNS': '208.67.222.222',
            'Quad9': '9.9.9.9'
        }
        
        results = []
        for name, server in servers.items():
            try:
                cmd = ['dig', f'@{server}', domain, record_type, '+short']
                output = subprocess.check_output(cmd, text=True, timeout=5, stderr=subprocess.DEVNULL)
                records = [line.strip() for line in output.strip().split('\n') if line.strip()]
                results.append({
                    'name': name,
                    'server': server,
                    'records': records if records else ["Sin registros"]
                })
            except:
                results.append({
                    'name': name,
                    'server': server,
                    'records': ["Error o timeout"]
                })
        
        return results
    
    def display_comparison(self, results: list) -> None:
        """Muestra la comparación de servidores DNS"""
        output = f"[bold cyan]🔄 Comparación de servidores DNS[/]\n\n"
        
        for result in results:
            output += f"[bold yellow]{result['name']}[/] ({result['server']})\n"
            for record in result['records']:
                output += f"  • {record}\n"
            output += "\n"
        
        self.query_one("#results", Static).update(output)
        self.notify("Comparación completada", severity="information")
    
    def clear_results(self) -> None:
        """Limpia los resultados"""
        self.query_one("#domain-input", Input).value = ""
        self.query_one("#results", Static).update(
            "Ingresa un dominio y selecciona el tipo de registro DNS"
        )
        self.notify("Resultados limpiados", severity="information")


def main():
    """Función principal"""
    app = DNSAdvancedApp()
    app.run()


if __name__ == "__main__":
    main()
