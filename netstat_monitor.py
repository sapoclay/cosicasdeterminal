"""
Monitor de Conexiones (NetStat Monitor)
Muestra conexiones de red en tiempo real usando 'ss'
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, DataTable, Input, Label
from textual.binding import Binding
import subprocess
import time

class NetStatMonitorApp(App):
    """Aplicación de Monitor de Conexiones"""
    
    TITLE = "🕵️‍♂️ NetStat Monitor"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        padding: 1 2;
    }
    
    DataTable {
        height: 1fr;
        border: solid $primary;
    }
    
    #status-bar {
        height: auto;
        padding: 0 1;
        background: $panel;
        margin-bottom: 1;
    }
    
    .filter-input {
        width: 30;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "refresh_connections", "Recargar"),
        Binding("space", "toggle_auto_refresh", "Pausar/Reanudar"),
    ]
    
    def __init__(self):
        super().__init__()
        self.update_active = True
        self.timer = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with ScrollableContainer(id="main-container"):
            yield Static("🕵️‍♂️ MONITOR DE CONEXIONES DE RED", classes="title")
            
            with Horizontal(id="status-bar"):
                yield Button("🔄 Recargar", id="btn-refresh", variant="primary")
                yield Button("⏸️ Pausar", id="btn-pause", variant="warning")
                yield Label("  Filtro: ")
                yield Input(placeholder="Buscar...", id="filter-input", classes="filter-input")
            
            yield DataTable(zebra_stripes=True)
        
        yield Footer()
        
    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Proto", "Local Address", "Remote Address", "State", "PID/Program")
        self.refresh_connections()
        self.timer = self.set_interval(2.0, self.refresh_connections)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh":
            self.refresh_connections()
        elif event.button.id == "btn-pause":
            self.toggle_update_active()

    def action_refresh_connections(self):
        self.refresh_connections()
        
    def action_toggle_auto_refresh(self):
        self.toggle_update_active()

    def toggle_update_active(self):
        self.update_active = not self.update_active
        btn = self.query_one("#btn-pause", Button)
        if self.update_active:
            btn.label = "⏸️ Pausar"
            btn.variant = "warning"
            self.timer.resume()
        else:
            btn.label = "▶️ Reanudar"
            btn.variant = "success"
            self.timer.pause()

    def refresh_connections(self):
        if not self.update_active and self.sender != self.query_one("#btn-refresh"):
            return

        import platform
        system = platform.system()
        
        try:
            if system == "Linux":
                self._refresh_linux()
            elif system == "Windows":
                self._refresh_windows()
            elif system == "Darwin":
                self._refresh_macos()
            else:
                self.notify(f"Sistema no soportado: {system}", severity="error")
                
        except Exception as e:
            with open("netstat_debug.log", "a") as f:
                import traceback
                f.write(f"Error in refresh_connections: {e}\n")
                traceback.print_exc(file=f)
            self.notify(f"Error al obtener conexiones: {e}", severity="error")

    def _refresh_linux(self):
        # Use ss -tunap
        cmd = ['ss', '-tunap']
        result = subprocess.run(cmd, capture_output=True, text=True)
        self._parse_ss_output(result.stdout)

    def _refresh_windows(self):
        # Use netstat -ano
        cmd = ['netstat', '-ano']
        result = subprocess.run(cmd, capture_output=True, text=True)
        self._parse_netstat_windows(result.stdout)

    def _refresh_macos(self):
        # Use netstat -anv -p tcp (and udp separately or together if supported)
        # Simplified: netstat -anv
        cmd = ['netstat', '-anv']
        result = subprocess.run(cmd, capture_output=True, text=True)
        self._parse_netstat_macos(result.stdout)

    def _parse_ss_output(self, output):
        table = self.query_one(DataTable)
        table.clear()
        filter_text = self.query_one("#filter-input", Input).value.lower()
        
        lines = output.split('\n')
        start_idx = 1
        if len(lines) > 0 and "State" in lines[0]: start_idx = 1
        
        for line in lines[start_idx:]:
            if not line.strip(): continue
            parts = line.split()
            if len(parts) < 6: continue
            
            try:
                proto = parts[0]
                state = parts[1]
                local_addr = parts[4]
                remote_addr = parts[5]
                
                process_info = ""
                if "users:" in line:
                    try:
                        p_start = line.index("users:((") + 8
                        p_end = line.index("))", p_start)
                        process_info = line[p_start:p_end]
                    except:
                        process_info = parts[-1] if "users:" in parts[-1] else ""
                
                self._add_row_filtered(table, filter_text, proto, local_addr, remote_addr, state, process_info)
            except Exception as e:
                # Ignore malformed lines to prevent crash
                continue

    def _parse_netstat_windows(self, output):
        # Proto  Local Address          Foreign Address        State           PID
        # TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       984
        table = self.query_one(DataTable)
        table.clear()
        filter_text = self.query_one("#filter-input", Input).value.lower()
        
        lines = output.split('\n')
        for line in lines:
            if not line.strip() or "Active Connections" in line or "Proto" in line: continue
            parts = line.split()
            if len(parts) < 4: continue
            
            proto = parts[0]
            local_addr = parts[1]
            remote_addr = parts[2]
            state = parts[3]
            pid = parts[4] if len(parts) > 4 else ""
            
            # State is sometimes missing for UDP
            if proto == "UDP":
                pid = state
                state = "UDP"
            
            self._add_row_filtered(table, filter_text, proto, local_addr, remote_addr, state, f"PID: {pid}")

    def _parse_netstat_macos(self, output):
        # Proto Recv-Q Send-Q  Local Address          Foreign Address        (state)     rhiwat shiwat    pid   epid  state    options
        # tcp4       0      0  127.0.0.1.53068        127.0.0.1.53069        ESTABLISHED 131072 131072   6789      0 0x0102 0x00000004
        table = self.query_one(DataTable)
        table.clear()
        filter_text = self.query_one("#filter-input", Input).value.lower()
        
        lines = output.split('\n')
        for line in lines:
            if not line.strip() or "Proto" in line: continue
            parts = line.split()
            if len(parts) < 6: continue
            
            proto = parts[0]
            local_addr = parts[3]
            remote_addr = parts[4]
            state = parts[5]
            pid = parts[8] if len(parts) > 8 else "" # Rough guess for pid column in -anv
            
            self._add_row_filtered(table, filter_text, proto, local_addr, remote_addr, state, f"PID: {pid}")

    def _add_row_filtered(self, table, filter_text, proto, local, remote, state, proc):
        row = [proto, local, remote, state, proc]
        if filter_text:
            if not any(filter_text in str(c).lower() for c in row):
                return
        table.add_row(*row)

def main():
    app = NetStatMonitorApp()
    app.run()

if __name__ == "__main__":
    main()
