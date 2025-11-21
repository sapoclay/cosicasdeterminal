"""
Muestra consumo de datos y procesos que más usan la red
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable, ProgressBar
from textual.binding import Binding
import psutil
import time
from datetime import datetime

class SimpleNetworkMonitor(App):
    """Monitor simple de uso de red"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #content {
        height: 100%;
        overflow-y: auto;
        padding: 1 2;
    }
    
    .stats-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        height: auto;
    }
    
    DataTable {
        height: auto;
        max-height: 15;
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
        Binding("r", "reset", "Reiniciar"),
        Binding("ctrl+c", "quit", "Salir"),
    ]
    
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
        self.start_bytes_sent = 0
        self.start_bytes_recv = 0
        self.last_bytes_sent = 0
        self.last_bytes_recv = 0
        self.update_timer = None
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="content"):
            yield Static("Iniciando monitor de red...", id="stats", classes="stats-box")
            yield Static("[bold cyan]TOP 5 PROCESOS USANDO RED[/]", id="processes-title")
            yield DataTable(id="processes-table")
        with Horizontal(id="button-container"):
            yield Button("🔄 Reiniciar contadores", id="reset-btn", variant="warning")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar, inicializar contadores"""
        self.title = "💾 Monitor de uso de red"
        
        # Configurar tabla
        table = self.query_one("#processes-table", DataTable)
        table.add_columns("Proceso", "PID", "📤 Subida", "📥 Bajada", "Total")
        table.cursor_type = "row"
        
        # Inicializar contadores
        net_io = psutil.net_io_counters()
        self.start_bytes_sent = net_io.bytes_sent
        self.start_bytes_recv = net_io.bytes_recv
        self.last_bytes_sent = net_io.bytes_sent
        self.last_bytes_recv = net_io.bytes_recv
        
        # Iniciar actualización automática
        self.set_interval(1.0, self.update_stats)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clic en botones"""
        if event.button.id == "reset-btn":
            self.action_reset()
    
    def action_reset(self) -> None:
        """Reiniciar contadores"""
        self.start_time = time.time()
        net_io = psutil.net_io_counters()
        self.start_bytes_sent = net_io.bytes_sent
        self.start_bytes_recv = net_io.bytes_recv
        self.last_bytes_sent = net_io.bytes_sent
        self.last_bytes_recv = net_io.bytes_recv
        self.update_stats()
    
    def format_bytes(self, bytes_val: int) -> str:
        """Formatear bytes en unidades legibles"""
        value = float(bytes_val)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if value < 1024.0:
                return f"{value:.2f} {unit}"
            value /= 1024.0
        return f"{value:.2f} PB"
    
    def format_speed(self, bytes_per_sec: float) -> str:
        """Formatear velocidad en unidades legibles"""
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if bytes_per_sec < 1024.0:
                return f"{bytes_per_sec:.2f} {unit}"
            bytes_per_sec /= 1024.0
        return f"{bytes_per_sec:.2f} TB/s"
    
    def update_stats(self) -> None:
        """Actualizar estadísticas"""
        stats_widget = self.query_one("#stats", Static)
        table = self.query_one("#processes-table", DataTable)
        
        # Obtener estadísticas actuales
        net_io = psutil.net_io_counters()
        
        # Calcular totales desde inicio
        total_sent = net_io.bytes_sent - self.start_bytes_sent
        total_recv = net_io.bytes_recv - self.start_bytes_recv
        total = total_sent + total_recv
        
        # Calcular velocidad actual
        bytes_sent_diff = net_io.bytes_sent - self.last_bytes_sent
        bytes_recv_diff = net_io.bytes_recv - self.last_bytes_recv
        
        upload_speed = bytes_sent_diff  # bytes por segundo
        download_speed = bytes_recv_diff
        
        self.last_bytes_sent = net_io.bytes_sent
        self.last_bytes_recv = net_io.bytes_recv
        
        # Tiempo transcurrido
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        # Crear estadísticas
        stats_text = f"""[bold cyan]═══ ESTADÍSTICAS DE RED ═══[/]

[bold]Tiempo de sesión:[/] {hours:02d}:{minutes:02d}:{seconds:02d}

[bold green]📤 SUBIDA:[/]
  Velocidad actual: [cyan]{self.format_speed(upload_speed)}[/]
  Total sesión: [green]{self.format_bytes(total_sent)}[/]
  Paquetes: {net_io.packets_sent - psutil.net_io_counters().packets_sent + net_io.packets_sent:,}

[bold blue]📥 BAJADA:[/]
  Velocidad actual: [cyan]{self.format_speed(download_speed)}[/]
  Total sesión: [blue]{self.format_bytes(total_recv)}[/]
  Paquetes: {net_io.packets_recv:,}

[bold yellow]📊 TOTAL:[/]
  Transferido: [yellow]{self.format_bytes(total)}[/]
  Errores: [red]{net_io.errin + net_io.errout}[/]
  Perdidos: [red]{net_io.dropin + net_io.dropout}[/]
"""
        
        stats_widget.update(stats_text)
        
        # Actualizar tabla de procesos
        table.clear()
        
        try:
            # Obtener procesos con conexiones de red
            processes_net = {}
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    connections = proc.net_connections()
                    if connections:
                        io = proc.io_counters()
                        pid = proc.info['pid']
                        name = proc.info['name']
                        
                        # Acumular I/O de red (aproximación)
                        if name not in processes_net:
                            processes_net[name] = {
                                'pid': pid,
                                'read': io.read_bytes,
                                'write': io.write_bytes,
                                'total': io.read_bytes + io.write_bytes
                            }
                        else:
                            processes_net[name]['read'] += io.read_bytes
                            processes_net[name]['write'] += io.write_bytes
                            processes_net[name]['total'] += io.read_bytes + io.write_bytes
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar por total y tomar top 5
            top_processes = sorted(
                processes_net.items(),
                key=lambda x: x[1]['total'],
                reverse=True
            )[:5]
            
            for name, data in top_processes:
                table.add_row(
                    name[:20],
                    str(data['pid']),
                    self.format_bytes(data['write']),
                    self.format_bytes(data['read']),
                    self.format_bytes(data['total'])
                )
            
            if not top_processes:
                table.add_row("-", "-", "-", "-", "[dim]No hay procesos con tráfico de red[/]")
                
        except Exception as e:
            table.add_row("-", "-", "-", "-", f"[red]Error: {str(e)}[/]")

if __name__ == "__main__":
    app = SimpleNetworkMonitor()
    app.run()
