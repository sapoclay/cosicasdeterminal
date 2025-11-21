"""
Analizador de ancho de banda por proceso
Muestra qué aplicaciones están usando la red
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, DataTable
from textual.binding import Binding
import psutil
import time
from collections import defaultdict


class BandwidthAnalyzerApp(App):
    """Aplicación de análisis de ancho de banda por proceso"""
    
    TITLE = "📊 Ancho de Banda"
    
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
    
    #controls {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }
    
    #stats-section {
        height: 8;
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    #table-section {
        height: 1fr;
        border: solid $primary;
    }
    
    Button {
        margin: 0 1;
    }
    
    DataTable {
        height: 100%;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "refresh", "Actualizar"),
        Binding("s", "sort", "Ordenar"),
    ]
    
    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.last_io = {}
        self.last_time = time.time()
        self.sort_column = "download"
        self.sort_reverse = True
    
    def compose(self) -> ComposeResult:
        """Compone la interfaz de usuario"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="title-section"):
                yield Static("📊 ANÁLISIS DE ANCHO DE BANDA POR PROCESO", classes="title")
            
            with Container(id="controls"):
                yield Button("▶️ Iniciar Monitoreo", variant="success", id="start-btn")
                yield Button("⏸️ Pausar", variant="warning", id="pause-btn")
                yield Button("🔄 Actualizar", variant="primary", id="refresh-btn")
                yield Button("📊 Ordenar por Bajada", variant="default", id="sort-download-btn")
                yield Button("📤 Ordenar por Subida", variant="default", id="sort-upload-btn")
            
            with Container(id="stats-section"):
                yield Static("Presiona 'Iniciar Monitoreo' para comenzar", id="stats")
            
            with Container(id="table-section"):
                yield DataTable(id="processes-table")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Se ejecuta cuando la aplicación se monta"""
        table = self.query_one("#processes-table", DataTable)
        table.add_columns("PID", "Proceso", "Usuario", "📥 Bajada", "📤 Subida", "🔗 Conexiones")
        table.cursor_type = "row"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "start-btn":
            self.start_monitoring()
        elif event.button.id == "pause-btn":
            self.pause_monitoring()
        elif event.button.id == "refresh-btn":
            self.action_refresh()
        elif event.button.id == "sort-download-btn":
            self.sort_column = "download"
            self.sort_reverse = True
            self.notify("Ordenando por descarga", severity="information")
        elif event.button.id == "sort-upload-btn":
            self.sort_column = "upload"
            self.sort_reverse = True
            self.notify("Ordenando por subida", severity="information")
    
    def start_monitoring(self) -> None:
        """Inicia la monitorización"""
        if not self.monitoring:
            self.monitoring = True
            self.notify("Monitoreo iniciado", severity="information")
            self.update_processes()
            self.set_interval(2.0, self.update_processes)
    
    def pause_monitoring(self) -> None:
        """Pausa la monitorización"""
        self.monitoring = False
        self.notify("Monitorización pausada", severity="warning")
    
    def action_refresh(self) -> None:
        """Actualiza manualmente"""
        if self.monitoring:
            self.update_processes()
            self.notify("Datos actualizados", severity="information")
        else:
            self.notify("Inicia la monitorización primero", severity="warning")
    
    def action_sort(self) -> None:
        """Cambia el ordenamiento"""
        self.sort_reverse = not self.sort_reverse
        self.notify("Orden invertido", severity="information")
    
    def update_processes(self) -> None:
        """Actualiza la información de procesos"""
        if not self.monitoring:
            return
        
        try:
            current_time = time.time()
            time_diff = current_time - self.last_time
            
            # Obtener I/O de red total
            net_io = psutil.net_io_counters()
            total_sent = net_io.bytes_sent
            total_recv = net_io.bytes_recv
            
            # Calcular velocidades totales
            if hasattr(self, 'last_total_sent'):
                total_download_speed = (total_recv - self.last_total_recv) / time_diff
                total_upload_speed = (total_sent - self.last_total_sent) / time_diff
            else:
                total_download_speed = 0
                total_upload_speed = 0
            
            self.last_total_sent = total_sent
            self.last_total_recv = total_recv
            
            # Obtener procesos con conexiones de red
            processes_data = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    username = proc.info['username'] or "N/A"
                    
                    # Obtener conexiones
                    connections = proc.connections(kind='inet')
                    num_connections = len(connections)
                    
                    if num_connections > 0:
                        # Intentar obtener I/O (puede requerir permisos)
                        try:
                            io = proc.io_counters()
                            current_read = io.read_bytes
                            current_write = io.write_bytes
                            
                            if pid in self.last_io:
                                download = (current_read - self.last_io[pid]['read']) / time_diff
                                upload = (current_write - self.last_io[pid]['write']) / time_diff
                            else:
                                download = 0
                                upload = 0
                            
                            self.last_io[pid] = {
                                'read': current_read,
                                'write': current_write
                            }
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            download = 0
                            upload = 0
                        
                        processes_data.append({
                            'pid': pid,
                            'name': name,
                            'username': username,
                            'download': download,
                            'upload': upload,
                            'connections': num_connections
                        })
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Ordenar según columna seleccionada
            processes_data.sort(
                key=lambda x: x[self.sort_column],
                reverse=self.sort_reverse
            )
            
            # Actualizar tabla
            table = self.query_one("#processes-table", DataTable)
            table.clear()
            
            for proc in processes_data[:50]:  # Limitar a top 50
                table.add_row(
                    str(proc['pid']),
                    proc['name'][:30],
                    proc['username'][:15],
                    self.format_bytes(proc['download']) + "/s",
                    self.format_bytes(proc['upload']) + "/s",
                    str(proc['connections'])
                )
            
            # Actualizar estadísticas
            stats = f"[bold cyan]📊 Estadísticas Totales[/]\n\n"
            stats += f"Procesos con actividad de red: [yellow]{len(processes_data)}[/]\n"
            stats += f"Velocidad de descarga total:  [green]{self.format_bytes(total_download_speed)}/s[/]\n"
            stats += f"Velocidad de subida total:    [blue]{self.format_bytes(total_upload_speed)}/s[/]\n"
            stats += f"Ordenado por: [cyan]{self.sort_column}[/]"
            
            self.query_one("#stats", Static).update(stats)
            
            self.last_time = current_time
            
        except Exception as e:
            self.notify(f"Error al actualizar: {str(e)}", severity="error")
    
    def format_bytes(self, bytes_value: float) -> str:
        """Formatea bytes a formato legible"""
        if bytes_value < 1024:
            return f"{bytes_value:.1f} B"
        elif bytes_value < 1024 ** 2:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 ** 3:
            return f"{bytes_value / (1024 ** 2):.1f} MB"
        else:
            return f"{bytes_value / (1024 ** 3):.1f} GB"


def main():
    """Función principal"""
    app = BandwidthAnalyzerApp()
    app.run()


if __name__ == "__main__":
    main()
