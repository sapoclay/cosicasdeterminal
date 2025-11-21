"""
Muestra qué puertos está escuchando tu máquina y qué procesos los usan
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable
from textual.binding import Binding
import psutil
import socket

class LocalPortScanner(App):
    """Aplicación para escanear puertos locales"""
    
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
    
    # Servicios comunes
    COMMON_SERVICES = {
        20: "FTP Data",
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
        6379: "Redis",
        8080: "HTTP-Alt",
        8443: "HTTPS-Alt",
        9200: "Elasticsearch",
        27017: "MongoDB",
    }
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="content"):
            yield Static("Iniciando escaneo de puertos locales...", id="summary")
            yield DataTable(id="ports-table")
        with Horizontal(id="button-container"):
            yield Button("🔄 Escanear puertos", id="scan-btn", variant="primary")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar, configurar tabla y escanear"""
        self.title = "🔌 Escáner de puertos locales"
        
        table = self.query_one("#ports-table", DataTable)
        table.add_columns("Puerto", "Protocolo", "Estado", "Servicio", "Proceso", "PID")
        table.cursor_type = "row"
        
        self.scan_ports()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clic en botones"""
        if event.button.id == "scan-btn":
            self.scan_ports()
    
    def action_scan(self) -> None:
        """Ejecutar escaneo"""
        self.scan_ports()
    
    def get_service_name(self, port: int) -> str:
        """Obtener nombre del servicio"""
        if port in self.COMMON_SERVICES:
            return self.COMMON_SERVICES[port]
        
        try:
            return socket.getservbyport(port)
        except:
            return "Desconocido"
    
    def scan_ports(self) -> None:
        """Escanear puertos locales en uso"""
        summary = self.query_one("#summary", Static)
        table = self.query_one("#ports-table", DataTable)
        
        summary.update("🔍 Escaneando puertos locales...")
        table.clear()
        
        # Obtener todas las conexiones
        connections = psutil.net_connections(kind='inet')
        
        listening_ports = []
        established_ports = []
        
        for conn in connections:
            if conn.status == 'LISTEN':
                listening_ports.append(conn)
            elif conn.status == 'ESTABLISHED':
                established_ports.append(conn)
        
        # Procesar puertos en escucha
        seen_ports = set()
        for conn in sorted(listening_ports, key=lambda x: x.laddr.port):
            port = conn.laddr.port
            if port in seen_ports:
                continue
            seen_ports.add(port)
            
            protocol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            addr = conn.laddr.ip if conn.laddr.ip != '0.0.0.0' else "*"
            
            # Obtener información del proceso
            try:
                if conn.pid:
                    process = psutil.Process(conn.pid)
                    proc_name = process.name()
                    pid = str(conn.pid)
                else:
                    proc_name = "N/A"
                    pid = "-"
            except:
                proc_name = "N/A"
                pid = "-"
            
            service = self.get_service_name(port)
            
            # Añadir fila a la tabla
            table.add_row(
                f"{addr}:{port}",
                protocol,
                "[green]ESCUCHANDO[/]",
                service,
                proc_name,
                pid
            )
        
        # Actualizar resumen
        tcp_count = sum(1 for c in listening_ports if c.type == socket.SOCK_STREAM)
        udp_count = sum(1 for c in listening_ports if c.type == socket.SOCK_DGRAM)
        
        summary_text = f"""[bold cyan]═══ RESUMEN DE PUERTOS LOCALES ═══[/]

[green]●[/] Puertos en escucha: [cyan]{len(seen_ports)}[/]
  • TCP: [blue]{tcp_count}[/]
  • UDP: [blue]{udp_count}[/]

[yellow]●[/] Conexiones establecidas: [cyan]{len(established_ports)}[/]

[dim]Pulsa 'r' para actualizar | 'q' para salir[/]"""
        
        summary.update(summary_text)
        
        if len(seen_ports) == 0:
            table.add_row("-", "-", "[dim]No hay puertos en escucha[/]", "-", "-", "-")

if __name__ == "__main__":
    app = LocalPortScanner()
    app.run()
