"""
Muestra estadísticas de red, velocidad, conexiones activas, etc.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, Button, DataTable
from textual.binding import Binding
import psutil
import socket
from datetime import datetime
import time


class StatCard(Static):
    """Tarjeta de estadística"""
    
    def __init__(self, title: str, value: str, icon: str = "📊"):
        self.title = title
        self.value = value
        self.icon = icon
        super().__init__()
        self.update_display()
    
    def update_display(self):
        """Actualiza la visualización de la tarjeta"""
        content = f"{self.icon} [bold]{self.title}[/]\n[cyan]{self.value}[/]"
        self.update(content)
    
    def set_value(self, value: str):
        """Actualiza el valor de la tarjeta"""
        self.value = value
        self.update_display()


class NetworkSpeedWidget(Static):
    """Widget para mostrar velocidad de red"""
    
    def __init__(self):
        super().__init__()
        self.last_sent = 0
        self.last_recv = 0
        self.last_time = time.time()
        self.update_speed()
    
    def update_speed(self):
        """Actualiza la velocidad de red"""
        try:
            net_io = psutil.net_io_counters()
            current_time = time.time()
            time_delta = current_time - self.last_time
            
            if self.last_sent > 0 and time_delta > 0:
                sent_speed = (net_io.bytes_sent - self.last_sent) / time_delta
                recv_speed = (net_io.bytes_recv - self.last_recv) / time_delta
                
                # Convertir a unidades legibles
                upload_str = self.format_bytes(sent_speed) + "/s"
                download_str = self.format_bytes(recv_speed) + "/s"
            else:
                upload_str = "0 B/s"
                download_str = "0 B/s"
            
            self.last_sent = net_io.bytes_sent
            self.last_recv = net_io.bytes_recv
            self.last_time = current_time
            
            content = f"[bold]🔄 VELOCIDAD DE RED[/]\n\n"
            content += f"⬆️  Subida:   [green]{upload_str:>12}[/]\n"
            content += f"⬇️  Bajada:   [cyan]{download_str:>12}[/]\n"
            
            self.update(content)
            
        except Exception as e:
            self.update(f"[red]Error: {e}[/]")
    
    @staticmethod
    def format_bytes(bytes_value: float) -> str:
        """Formatea bytes a unidades legibles"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"


class ConnectionsTable(DataTable):
    """Tabla de conexiones activas"""
    
    def __init__(self):
        super().__init__()
        self.cursor_type = "row"
    
    def on_mount(self):
        """Configura las columnas"""
        self.add_columns("Protocolo", "Local", "Remoto", "Estado", "PID")


class NetworkMonitorApp(App):
    """Aplicación de monitoreo de red"""
    
    TITLE = "📊 Monitor de Red"
    
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
        height: 5;
        width: 100%;
        content-align: center middle;
        background: $primary;
        margin-bottom: 1;
    }
    
    #stats-grid {
        height: auto;
        width: 100%;
        grid-size: 4 1;
        grid-gutter: 1;
        margin-bottom: 1;
    }
    
    StatCard {
        width: 100%;
        height: 5;
        border: solid $primary;
        padding: 1;
        content-align: center middle;
    }
    
    #speed-section {
        height: auto;
        width: 100%;
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    #connections-section {
        height: 1fr;
        width: 100%;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }
    
    #controls {
        height: auto;
        width: 100%;
        content-align: center middle;
    }
    
    ConnectionsTable {
        width: 100%;
        height: 100%;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "refresh", "Refrescar"),
        Binding("p", "toggle_pause", "Pausar/Reanudar"),
    ]
    
    def __init__(self):
        super().__init__()
        self.paused = False
    
    def compose(self) -> ComposeResult:
        """Compone la interfaz de usuario"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="header-section"):
                yield Static("📊 MONITOR DE RED EN TIEMPO REAL")
                yield Static(datetime.now().strftime("%H:%M:%S"), id="clock")
            
            with Grid(id="stats-grid"):
                yield StatCard("Total Enviado", "0 B", "⬆️")
                yield StatCard("Total Recibido", "0 B", "⬇️")
                yield StatCard("Conexiones", "0", "🔗")
                yield StatCard("Interfaces", "0", "📡")
            
            yield NetworkSpeedWidget()
            
            with Vertical(id="connections-section"):
                yield Static("[bold]🔗 CONEXIONES ACTIVAS[/]", id="conn-title")
                yield ConnectionsTable()
            
            with Horizontal(id="controls"):
                yield Button("🔄 Refrescar", variant="primary", id="refresh-btn")
                yield Button("⏸️  Pausar", variant="warning", id="pause-btn")
                yield Button("📊 Estadísticas", variant="success", id="stats-btn")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Se ejecuta cuando la aplicación se monta"""
        # Actualizar inmediatamente al montar
        self.call_after_refresh(self.update_all)
        # Configurar actualizaciones periódicas
        self.set_interval(1, self.update_stats)
        self.set_interval(1, self.update_clock)
        self.set_interval(2, self.update_connections)
    
    def update_clock(self) -> None:
        """Actualiza el reloj"""
        try:
            clock = self.query_one("#clock", Static)
            clock.update(datetime.now().strftime("%H:%M:%S"))
        except:
            pass
    
    def update_stats(self) -> None:
        """Actualiza las estadísticas generales"""
        if self.paused:
            return
        
        try:
            # Estadísticas de red
            net_io = psutil.net_io_counters()
            
            # Total enviado/recibido
            stats = list(self.query(StatCard))
            if len(stats) >= 4:
                stats[0].set_value(self.format_bytes(net_io.bytes_sent))
                stats[1].set_value(self.format_bytes(net_io.bytes_recv))
                
                # Número de conexiones
                try:
                    connections = psutil.net_connections()
                    stats[2].set_value(str(len(connections)))
                except:
                    stats[2].set_value("N/A")
                
                # Número de interfaces
                interfaces = psutil.net_if_stats()
                stats[3].set_value(str(len(interfaces)))
            
            # Actualizar velocidad
            try:
                speed_widgets = self.query(NetworkSpeedWidget)
                if speed_widgets:
                    speed_widgets[0].update_speed()
            except:
                pass
            
        except Exception as e:
            # Error silencioso para no molestar al usuario
            pass
    
    def update_connections(self) -> None:
        """Actualiza la tabla de conexiones"""
        if self.paused:
            return
        
        try:
            # Verificar si existe la tabla antes de actualizar
            tables = self.query(ConnectionsTable)
            if not tables:
                return  # No hay tabla que actualizar (puede estar mostrando estadísticas)
            
            table = tables[0]
            table.clear()
            
            connections = psutil.net_connections(kind='inet')
            
            # Limitar a las primeras 50 conexiones
            for conn in connections[:50]:
                try:
                    proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                    local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                    remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                    status = conn.status if conn.status else "N/A"
                    pid = str(conn.pid) if conn.pid else "N/A"
                    
                    table.add_row(proto, local, remote, status, pid)
                except:
                    pass
                    
        except Exception as e:
            # No mostrar error si simplemente no existe la tabla
            pass
    
    def update_all(self) -> None:
        """Actualiza todos los componentes"""
        self.update_stats()
        self.update_connections()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "refresh-btn":
            self.action_refresh()
        elif event.button.id == "pause-btn":
            self.action_toggle_pause()
        elif event.button.id == "stats-btn":
            self.show_detailed_stats()
    
    def action_refresh(self) -> None:
        """Refresca manualmente los datos y restaura vista de conexiones"""
        # Restaurar la vista de conexiones si está mostrando estadísticas
        try:
            conn_section = self.query_one("#connections-section", Vertical)
            # Verificar si está mostrando estadísticas detalladas
            detailed_stats = conn_section.query("#detailed-stats")
            if detailed_stats:
                # Limpiar y restaurar
                for child in list(conn_section.children):
                    child.remove()
                
                conn_section.mount(Static("[bold]🔗 CONEXIONES ACTIVAS[/]", id="conn-title"))
                table = ConnectionsTable()
                conn_section.mount(table)
                # Forzar actualización de la tabla
                self.call_after_refresh(self.update_connections)
        except Exception as e:
            pass
        
        self.update_all()
        self.notify("Datos actualizados", severity="information")
    
    def action_toggle_pause(self) -> None:
        """Pausa/reanuda la actualización automática"""
        self.paused = not self.paused
        
        try:
            pause_btn = self.query_one("#pause-btn", Button)
            if self.paused:
                pause_btn.label = "▶️  Reanudar"
                self.notify("Actualizaciones pausadas", severity="warning")
            else:
                pause_btn.label = "⏸️  Pausar"
                self.notify("Actualizaciones reanudadas", severity="information")
        except:
            pass
    
    def show_detailed_stats(self) -> None:
        """Muestra estadísticas detalladas en la sección de conexiones"""
        try:
            net_io = psutil.net_io_counters()
            net_if = psutil.net_if_stats()
            
            stats_text = "[bold cyan]═══ ESTADÍSTICAS DETALLADAS DE RED ═══[/]\n\n"
            
            # Estadísticas de paquetes
            stats_text += "[bold yellow]📦 PAQUETES:[/]\n"
            stats_text += f"  • Enviados: [green]{net_io.packets_sent:,}[/]\n"
            stats_text += f"  • Recibidos: [cyan]{net_io.packets_recv:,}[/]\n\n"
            
            # Errores
            stats_text += "[bold red]⚠️  ERRORES:[/]\n"
            stats_text += f"  • Entrada: [red]{net_io.errin:,}[/]\n"
            stats_text += f"  • Salida: [red]{net_io.errout:,}[/]\n\n"
            
            # Paquetes descartados
            stats_text += "[bold yellow]🗑️  DESCARTADOS:[/]\n"
            stats_text += f"  • Entrada: [yellow]{net_io.dropin:,}[/]\n"
            stats_text += f"  • Salida: [yellow]{net_io.dropout:,}[/]\n\n"
            
            # Interfaces de red
            stats_text += "[bold cyan]📡 INTERFACES DE RED:[/]\n"
            for iface_name, iface_stats in net_if.items():
                status = "🟢" if iface_stats.isup else "🔴"
                speed = f"{iface_stats.speed} Mbps" if iface_stats.speed > 0 else "N/A"
                stats_text += f"  {status} [cyan]{iface_name}[/]: {speed}\n"
            
            stats_text += "\n[dim]Presiona 'r' para volver a las conexiones[/]"
            
            # Reemplazar la tabla de conexiones con las estadísticas
            try:
                conn_section = self.query_one("#connections-section", Vertical)
                # Limpiar contenido actual de forma segura
                for child in list(conn_section.children):
                    child.remove()
                # Agregar estadísticas
                conn_section.mount(Static(stats_text, id="detailed-stats"))
                self.notify("Mostrando estadísticas detalladas", severity="information")
            except Exception as inner_e:
                # Si falla, usar notificación como respaldo
                self.notify(f"Error: {inner_e}", severity="error")
            
        except Exception as e:
            self.notify(f"Error obteniendo estadísticas: {e}", severity="error")
    
    @staticmethod
    def format_bytes(bytes_value: float) -> str:
        """Formatea bytes a unidades legibles"""
        value = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024.0:
                return f"{value:.2f} {unit}"
            value /= 1024.0
        return f"{value:.2f} TB"


def main():
    """Función principal para ejecutar la aplicación"""
    app = NetworkMonitorApp()
    app.run()


if __name__ == "__main__":
    main()
