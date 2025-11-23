"""
Analizador de Paquetes de Red (Sniffer)
Requiere permisos de ROOT/ADMINISTRADOR
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, DataTable, Label
from textual.binding import Binding
from textual.worker import Worker
import socket
import struct
import textwrap
import time
import os
import sys
import threading

class PacketSnifferApp(App):
    """Aplicación de Sniffer de Paquetes"""
    
    TITLE = "🦈 Analizador de Paquetes"
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
    
    DataTable {
        height: 1fr;
        border: solid $primary;
    }
    
    #status {
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }
    
    .stat-box {
        width: 1fr;
        content-align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("s", "toggle_capture", "Iniciar/Parar"),
        Binding("c", "clear_table", "Limpiar"),
    ]
    
    def __init__(self):
        super().__init__()
        self.capturing = False
        self.packet_count = 0
        self.sniffer_socket = None
        self.worker = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="controls"):
            yield Button("▶️ Iniciar", id="btn-start", variant="success")
            yield Button("⏹️ Detener", id="btn-stop", variant="error", disabled=True)
            yield Button("🗑️ Limpiar", id="btn-clear")
            yield Label("   Total Paquetes: 0", id="lbl-count", classes="stat-box")
            
        yield DataTable(cursor_type="row")
        yield Static("Listo (Requiere ROOT/Sudo)", id="status")
        yield Footer()
        
    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Hora", "Protocolo", "Origen", "Destino", "Longitud", "Info")
        
        # Check permissions
        if os.name != 'nt' and os.geteuid() != 0:
            self.notify("⚠️ Se requieren permisos de ROOT para capturar paquetes", severity="error", timeout=10)
            self.query_one("#status", Static).update("⚠️ ERROR: No tienes permisos de root. Ejecuta con sudo.")
            self.query_one("#btn-start", Button).disabled = True

    def action_toggle_capture(self):
        if self.capturing:
            self.stop_capture()
        else:
            self.start_capture()
            
    def action_clear_table(self):
        self.query_one(DataTable).clear()
        self.packet_count = 0
        self.query_one("#lbl-count", Label).update(f"   Total Paquetes: {self.packet_count}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start":
            self.start_capture()
        elif event.button.id == "btn-stop":
            self.stop_capture()
        elif event.button.id == "btn-clear":
            self.action_clear_table()

    def start_capture(self):
        if self.capturing: return
        
        try:
            # Setup socket
            if os.name == 'nt':
                self.notify("Windows requiere drivers especiales (Npcap) para raw sockets. Funcionalidad limitada.", severity="warning")
                # Windows raw socket setup is complex and often restricted
                self.sniffer_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                self.sniffer_socket.bind((self.get_local_ip(), 0))
                self.sniffer_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                self.sniffer_socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            else:
                # Linux/Unix
                self.sniffer_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
            
            self.capturing = True
            self.query_one("#btn-start", Button).disabled = True
            self.query_one("#btn-stop", Button).disabled = False
            self.query_one("#status", Static).update("🦈 Capturando paquetes...")
            
            # Start worker thread
            self.run_worker(self.capture_loop, thread=True)
            self.notify("Captura iniciada")
            
        except PermissionError:
            self.notify("Error: Permiso denegado. Usa sudo.", severity="error")
        except Exception as e:
            self.notify(f"Error al iniciar socket: {e}", severity="error")

    def stop_capture(self):
        self.capturing = False
        if self.sniffer_socket:
            if os.name == 'nt':
                try:
                    self.sniffer_socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
                except: pass
            self.sniffer_socket.close()
            self.sniffer_socket = None
            
        self.query_one("#btn-start", Button).disabled = False
        self.query_one("#btn-stop", Button).disabled = True
        self.query_one("#status", Static).update("⏹️ Captura detenida")
        self.notify("Captura detenida")

    def capture_loop(self):
        while self.capturing and self.sniffer_socket:
            try:
                raw_data, addr = self.sniffer_socket.recvfrom(65535)
                self.parse_packet(raw_data)
            except Exception as e:
                if self.capturing:
                    self.app.call_from_thread(self.notify, f"Error captura: {e}", severity="error")
                break

    def parse_packet(self, raw_data):
        try:
            # Ethernet Header (First 14 bytes)
            eth_len = 14
            eth_header = raw_data[:eth_len]
            eth = struct.unpack('!6s6sH', eth_header)
            eth_protocol = socket.ntohs(eth[2])
            
            # Parse IP packets (Protocol 8)
            if eth_protocol == 8:
                # IP Header
                ip_header = raw_data[eth_len:20+eth_len]
                iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
                
                version_ihl = iph[0]
                ihl = version_ihl & 0xF
                iph_length = ihl * 4
                
                protocol = iph[6]
                s_addr = socket.inet_ntoa(iph[8])
                d_addr = socket.inet_ntoa(iph[9])
                
                # Protocol names
                proto_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
                proto_name = proto_map.get(protocol, str(protocol))
                
                # Add to table (thread safe)
                timestamp = time.strftime("%H:%M:%S")
                self.app.call_from_thread(
                    self.add_packet_to_table,
                    timestamp, proto_name, s_addr, d_addr, str(len(raw_data)), "IPv4 Packet"
                )
                
        except Exception:
            pass

    def add_packet_to_table(self, *args):
        table = self.query_one(DataTable)
        table.add_row(*args)
        self.packet_count += 1
        self.query_one("#lbl-count", Label).update(f"   Total Paquetes: {self.packet_count}")
        
        # Auto scroll
        if self.packet_count % 5 == 0:
            table.scroll_end(animate=False)

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

def main():
    app = PacketSnifferApp()
    app.run()

if __name__ == "__main__":
    main()
