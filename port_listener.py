"""
Escucha de Puertos (Mini-Netcat)
Escucha en puertos TCP/UDP y muestra los datos recibidos
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label, RichLog, RadioSet, RadioButton
from textual.binding import Binding
from textual.worker import Worker
import socket
import threading
import datetime

class PortListenerApp(App):
    """Aplicación de Escucha de Puertos"""
    
    TITLE = "👂 Escucha de Puertos"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #controls {
        height: auto;
        padding: 1;
        background: $panel;
        border-bottom: solid $primary;
    }
    
    .input-group {
        width: auto;
        height: auto;
        margin-right: 2;
    }
    
    Input {
        width: 15;
    }
    
    RichLog {
        height: 1fr;
        border: solid $primary;
        background: $surface;
    }
    
    #status {
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }
    
    RadioSet {
        layout: horizontal;
        background: $panel;
        border: none;
    }
    
    RadioButton {
        width: auto;
        padding: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("s", "toggle_listen", "Iniciar/Parar"),
        Binding("c", "clear_log", "Limpiar Log"),
    ]
    
    def __init__(self):
        super().__init__()
        self.listening = False
        self.server_socket = None
        self.worker = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="controls"):
            with Vertical(classes="input-group"):
                yield Label("Puerto:")
                yield Input(placeholder="8080", id="port-input", type="integer")
            
            with Vertical(classes="input-group"):
                yield Label("Protocolo:")
                with RadioSet(id="protocol-radio"):
                    yield RadioButton("TCP", value=True)
                    yield RadioButton("UDP")
            
            with Vertical(classes="input-group"):
                yield Label("Acciones:")
                with Horizontal():
                    yield Button("▶️ Iniciar", id="btn-start", variant="success")
                    yield Button("⏹️ Parar", id="btn-stop", variant="error", disabled=True)
                    yield Button("🗑️ Limpiar", id="btn-clear")
            
        yield RichLog(highlight=True, markup=True, id="log-output")
        yield Static("Listo", id="status")
        yield Footer()
        
    def on_unmount(self):
        self.listening = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except: pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start":
            self.start_listening()
        elif event.button.id == "btn-stop":
            self.stop_listening()
        elif event.button.id == "btn-clear":
            self.query_one("#log-output", RichLog).clear()

    def action_toggle_listen(self):
        if self.listening:
            self.stop_listening()
        else:
            self.start_listening()
            
    def action_clear_log(self):
        self.query_one("#log-output", RichLog).clear()

    def start_listening(self):
        if self.listening: return
        
        port_str = self.query_one("#port-input", Input).value
        if not port_str:
            self.notify("Especifica un puerto", severity="warning")
            return
            
        try:
            port = int(port_str)
            if port < 1 or port > 65535: raise ValueError
        except ValueError:
            self.notify("Puerto inválido (1-65535)", severity="error")
            return
            
        protocol_idx = self.query_one("#protocol-radio", RadioSet).pressed_index
        is_tcp = (protocol_idx == 0)
        
        self.listening = True
        self.query_one("#btn-start", Button).disabled = True
        self.query_one("#btn-stop", Button).disabled = False
        self.query_one("#port-input", Input).disabled = True
        self.query_one("#protocol-radio", RadioSet).disabled = True
        
        proto_str = "TCP" if is_tcp else "UDP"
        self.query_one("#status", Static).update(f"👂 Escuchando en {proto_str} :{port}...")
        self.log_msg(f"[bold green]Iniciando escucha en puerto {port} ({proto_str})...[/]")
        
        self.run_worker(lambda: self.listen_loop(port, is_tcp), thread=True)

    def stop_listening(self):
        self.listening = False
        if self.server_socket:
            try:
                # Force close to break accept/recv loop
                self.server_socket.close()
            except: pass
            self.server_socket = None
            
        # Schedule UI update on main thread
        self.app.call_from_thread(self._update_ui_stopped)
        self.app.call_from_thread(self.log_msg, "[bold red]Escucha detenida.[/]")

    def _update_ui_stopped(self):
        try:
            self.query_one("#btn-start", Button).disabled = False
            self.query_one("#btn-stop", Button).disabled = True
            self.query_one("#port-input", Input).disabled = False
            self.query_one("#protocol-radio", RadioSet).disabled = False
            self.query_one("#status", Static).update("⏹️ Detenido")
        except: pass

    def listen_loop(self, port, is_tcp):
        try:
            if is_tcp:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', port))
            
            if is_tcp:
                self.server_socket.listen(5)
                self.server_socket.settimeout(1.0) # Allow checking self.listening
                
                while self.listening:
                    try:
                        client_sock, addr = self.server_socket.accept()
                        self.log_msg(f"[bold cyan]Conexión entrante de {addr[0]}:{addr[1]}[/]")
                        
                        # Handle client in separate thread to not block accepting
                        threading.Thread(target=self.handle_tcp_client, args=(client_sock, addr), daemon=True).start()
                    except socket.timeout:
                        continue
                    except OSError:
                        break
            else:
                # UDP
                self.server_socket.settimeout(1.0)
                while self.listening:
                    try:
                        data, addr = self.server_socket.recvfrom(4096)
                        self.log_data(data, addr, "UDP")
                    except socket.timeout:
                        continue
                    except OSError:
                        break
                        
        except PermissionError:
            self.app.call_from_thread(self.notify, "Error: Permiso denegado (puerto < 1024 requiere root)", severity="error")
            self.app.call_from_thread(self.stop_listening)
        except Exception as e:
            if self.listening:
                self.app.call_from_thread(self.notify, f"Error: {e}", severity="error")
                self.app.call_from_thread(self.stop_listening)

    def handle_tcp_client(self, client_sock, addr):
        try:
            client_sock.settimeout(None)
            while self.listening:
                data = client_sock.recv(4096)
                if not data: break
                self.log_data(data, addr, "TCP")
        except:
            pass
        finally:
            client_sock.close()
            self.app.call_from_thread(self.log_msg, f"[bold yellow]Conexión cerrada: {addr[0]}:{addr[1]}[/]")

    def log_data(self, data, addr, proto):
        try:
            text = data.decode('utf-8', errors='replace')
            # Clean non-printable
            clean_text = ''.join(c if c.isprintable() or c in '\n\r\t' else '.' for c in text)
            
            msg = f"[blue]{addr[0]}:{addr[1]}[/] ({proto}) > [white]{clean_text.strip()}[/]"
            self.app.call_from_thread(self.log_msg, msg)
        except:
            pass

    def log_msg(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.query_one("#log-output", RichLog).write(f"[dim]{timestamp}[/] {msg}")

def main():
    app = PortListenerApp()
    app.run()

if __name__ == "__main__":
    main()
