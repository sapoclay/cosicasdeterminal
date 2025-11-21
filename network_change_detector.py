"""
Monitorea dispositivos que se conectan/desconectan de la red
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, DataTable, Label, Select
from textual.binding import Binding
import socket
import subprocess
import netifaces
import ipaddress
from datetime import datetime
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from platform_utils import get_ping_fast_command


class NetworkChangeDetectorApp(App):
    """Aplicación de detección de cambios en la red"""
    
    TITLE = "🔔 Detector de Cambios en Red"
    
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
    
    #interface-selector {
        height: auto;
        width: 100%;
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    .selector-label {
        width: 20;
        content-align: left middle;
    }
    
    Select {
        width: 1fr;
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
    
    #devices-section {
        height: 1fr;
        border: solid $primary;
    }
    
    #events-section {
        height: 15;
        border: solid $warning;
        padding: 1 2;
    }
    
    Button {
        margin: 0 1;
    }
    
    DataTable {
        height: 100%;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("s", "scan", "Escanear"),
        Binding("m", "monitor", "Monitorear"),
    ]
    
    def __init__(self):
        super().__init__()
        self.known_devices = {}  # {ip: {hostname, mac, first_seen, last_seen, status}}
        self.monitoring = False
        self.events = []
        self.scan_interval = 30  # segundos
        self.selected_interface = None  # Interfaz seleccionada
    
    def compose(self) -> ComposeResult:
        """Compone la interfaz de usuario"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="title-section"):
                yield Static("🔍 DETECTOR DE CAMBIOS EN RED", classes="title")
            
            with Horizontal(id="interface-selector"):
                yield Label("Interfaz de Red:", classes="selector-label")
                yield Select([], id="interface-select")
                yield Button("🔄 Cambiar", variant="success", id="change-interface-btn")
            
            with Horizontal(id="controls"):
                yield Button("🔍 Escanear ahora", variant="primary", id="scan-btn")
                yield Button("▶️ Iniciar monitoreo", variant="success", id="monitor-btn")
                yield Button("⏸️ Detener", variant="warning", id="stop-btn")
                yield Button("🗑️ Limpiar", variant="default", id="clear-btn")
            
            with Container(id="stats-section"):
                yield Static(self.get_stats_text(), id="stats")
            
            with Container(id="devices-section"):
                yield DataTable(id="devices-table")
            
            with ScrollableContainer(id="events-section"):
                yield Static("[bold cyan]📋 Eventos recientes[/]\n\nNo hay eventos registrados", 
                           id="events", classes="section-title")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Se ejecuta cuando la aplicación se monta"""
        table = self.query_one("#devices-table", DataTable)
        table.add_columns("Estado", "IP", "Hostname", "MAC", "Primera Vez", "Última Vez")
        table.cursor_type = "row"
        self.populate_interfaces()
    
    def populate_interfaces(self) -> None:
        """Llena el selector con las interfaces de red disponibles"""
        try:
            interfaces = netifaces.interfaces()
            interface_options = []
            
            # Obtener interfaz predeterminada
            default_interface = None
            try:
                gateways = netifaces.gateways()
                default_info = gateways.get('default', {})
                default_gateway = default_info.get(netifaces.AF_INET) if isinstance(default_info, dict) else None
                if default_gateway:
                    default_interface = default_gateway[1]
            except:
                pass
            
            # Construir lista de interfaces con información
            for iface in interfaces:
                try:
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        ip = addrs[netifaces.AF_INET][0].get('addr', '')
                        if ip and not ip.startswith('127.'):
                            label = f"{iface} ({ip})"
                            if iface == default_interface:
                                label += " [Predeterminada]"
                            interface_options.append((label, iface))
                except:
                    continue
            
            # Si no hay interfaces con IP, mostrar todas
            if not interface_options:
                interface_options = [(iface, iface) for iface in interfaces]
            
            # Actualizar el selector
            select = self.query_one("#interface-select", Select)
            select.set_options(interface_options)
            
            # Seleccionar la predeterminada si existe
            if default_interface and any(opt[1] == default_interface for opt in interface_options):
                select.value = default_interface
                self.selected_interface = default_interface
            
        except Exception as e:
            self.notify(f"Error al obtener interfaces: {str(e)}", severity="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "scan-btn":
            self.action_scan()
        elif event.button.id == "monitor-btn":
            self.action_monitor()
        elif event.button.id == "stop-btn":
            self.stop_monitoring()
        elif event.button.id == "clear-btn":
            self.clear_data()
        elif event.button.id == "change-interface-btn":
            self.change_interface()
    
    def change_interface(self) -> None:
        """Cambia la interfaz de red seleccionada"""
        try:
            select = self.query_one("#interface-select", Select)
            selected_interface = str(select.value)
            
            if not selected_interface or selected_interface == "NoSelection":
                self.notify("Por favor selecciona una interfaz", severity="warning")
                return
            
            self.selected_interface = selected_interface
            self.notify(f"Interfaz cambiada a: {selected_interface}", severity="information")
            
            # Si está monitoreando, reiniciar con nueva interfaz
            if self.monitoring:
                self.notify("Reiniciando monitoreo con nueva interfaz...", severity="information")
                self.monitoring = False
                self.action_monitor()
            
        except Exception as e:
            self.notify(f"Error al cambiar interfaz: {str(e)}", severity="error")
    
    def action_scan(self) -> None:
        """Realiza un escaneo de la red"""
        if self.monitoring:
            self.notify("El monitoreo automático está activo", severity="information")
            return
        
        self.query_one("#stats", Static).update("⏳ Escaneando red...")
        
        worker_func = partial(self.scan_network)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def action_monitor(self) -> None:
        """Inicia el monitoreo continuo"""
        if self.monitoring:
            self.notify("El monitoreo ya está activo", severity="warning")
            return
        
        self.monitoring = True
        self.notify(f"Monitoreo iniciado (cada {self.scan_interval}s)", severity="information")
        self.scan_network_periodically()
    
    def stop_monitoring(self) -> None:
        """Detiene el monitoreo"""
        self.monitoring = False
        self.notify("Monitoreo detenido", severity="warning")
        self.query_one("#stats", Static).update(self.get_stats_text())
    
    def scan_network_periodically(self) -> None:
        """Escanea la red periódicamente"""
        if not self.monitoring:
            return
        
        worker_func = partial(self.scan_network)
        self.run_worker(worker_func, thread=True)
        
        # Programar próximo escaneo
        self.set_timer(self.scan_interval, self.scan_network_periodically)
    
    def scan_network(self) -> list:
        """Escanea la red en busca de dispositivos"""
        try:
            # Usar interfaz seleccionada o predeterminada
            if self.selected_interface:
                interface = self.selected_interface
            else:
                # Obtener interfaz predeterminada
                gateways = netifaces.gateways()
                default_info = gateways.get('default', {})
                default_gateway = default_info.get(netifaces.AF_INET) if isinstance(default_info, dict) else None
                
                if not default_gateway:
                    return []
                
                interface = default_gateway[1]
            
            addrs = netifaces.ifaddresses(interface)
            ip_info = addrs.get(netifaces.AF_INET, [{}])[0]
            local_ip = ip_info.get('addr')
            netmask = ip_info.get('netmask')
            
            if not local_ip or not netmask:
                return []
            
            network = ipaddress.IPv4Network(f"{local_ip}/{netmask}", strict=False)
            
            # Limitar a /24
            if network.num_addresses > 256:
                network = ipaddress.IPv4Network(f"{str(network.network_address)}/24", strict=False)
            
            devices = []
            
            def check_host(ip: str):
                try:
                    result = subprocess.run(
                        get_ping_fast_command(ip),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2
                    )
                    
                    if result.returncode == 0:
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                        except:
                            hostname = "Desconocido"
                        
                        mac = self.get_mac_address(ip)
                        
                        return {
                            'ip': ip,
                            'hostname': hostname,
                            'mac': mac
                        }
                except:
                    pass
                return None
            
            # Escanear en paralelo
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(check_host, str(ip)): ip for ip in network.hosts()}
                
                for future in as_completed(futures):
                    device = future.result()
                    if device:
                        devices.append(device)
            
            return devices
            
        except Exception as e:
            self.call_from_thread(self.notify, f"Error: {str(e)}", severity="error")
            return []
    
    def get_mac_address(self, ip: str) -> str:
        """Obtiene la dirección MAC de una IP"""
        try:
            import re
            arp_output = subprocess.check_output(['arp', '-n', ip], text=True)
            mac_match = re.search(r'(([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})', arp_output)
            if mac_match:
                return mac_match.group(1)
        except:
            pass
        return "N/A"
    
    def on_worker_state_changed(self, event) -> None:
        """Se ejecuta cuando cambia el estado del worker"""
        if event.state.name == "SUCCESS":
            devices = event.worker.result
            if devices:
                self.process_scan_results(devices)
        elif event.state.name == "ERROR":
            if not self.monitoring:
                self.notify("Error al escanear la red", severity="error")
    
    def process_scan_results(self, devices: list) -> None:
        """Procesa los resultados del escaneo y detecta cambios"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_ips = {d['ip'] for d in devices}
        
        # Detectar nuevos dispositivos
        for device in devices:
            ip = device['ip']
            
            if ip not in self.known_devices:
                # Nuevo dispositivo
                self.known_devices[ip] = {
                    'hostname': device['hostname'],
                    'mac': device['mac'],
                    'first_seen': now,
                    'last_seen': now,
                    'status': 'online'
                }
                self.add_event(f"🟢 Nuevo dispositivo conectado: {ip} ({device['hostname']})", "new")
            else:
                # Dispositivo conocido
                old_status = self.known_devices[ip]['status']
                self.known_devices[ip]['last_seen'] = now
                self.known_devices[ip]['status'] = 'online'
                
                if old_status == 'offline':
                    # Dispositivo reconectado
                    self.add_event(f"🔵 Dispositivo reconectado: {ip} ({device['hostname']})", "reconnect")
        
        # Detectar dispositivos desconectados
        for ip, info in self.known_devices.items():
            if ip not in current_ips and info['status'] == 'online':
                info['status'] = 'offline'
                self.add_event(f"🔴 Dispositivo desconectado: {ip} ({info['hostname']})", "disconnect")
        
        # Actualizar tabla
        self.update_devices_table()
        
        # Actualizar estadísticas
        self.query_one("#stats", Static).update(self.get_stats_text())
        
        if not self.monitoring:
            self.notify(f"Escaneo completado: {len(devices)} dispositivos activos", severity="information")
    
    def update_devices_table(self) -> None:
        """Actualiza la tabla de dispositivos"""
        table = self.query_one("#devices-table", DataTable)
        table.clear()
        
        # Ordenar por estado (online primero) y luego por IP
        sorted_devices = sorted(
            self.known_devices.items(),
            key=lambda x: (x[1]['status'] != 'online', x[0])
        )
        
        for ip, info in sorted_devices:
            status_icon = "🟢" if info['status'] == 'online' else "🔴"
            table.add_row(
                status_icon,
                ip,
                info['hostname'][:30],
                info['mac'],
                info['first_seen'],
                info['last_seen']
            )
    
    def add_event(self, message: str, event_type: str) -> None:
        """Agrega un evento a la lista"""
        now = datetime.now().strftime('%H:%M:%S')
        event = f"[{now}] {message}"
        self.events.insert(0, event)  # Agregar al inicio
        
        # Mantener solo los últimos 20 eventos
        if len(self.events) > 20:
            self.events = self.events[:20]
        
        # Actualizar widget de eventos
        events_text = "[bold cyan]📋 Eventos Recientes[/]\n\n"
        events_text += "\n".join(self.events)
        
        self.query_one("#events", Static).update(events_text)
        
        # Notificar solo eventos importantes
        if event_type in ['new', 'disconnect']:
            self.notify(message, severity="information")
    
    def get_stats_text(self) -> str:
        """Genera el texto de estadísticas"""
        total = len(self.known_devices)
        online = sum(1 for d in self.known_devices.values() if d['status'] == 'online')
        offline = total - online
        
        status = "🔄 Monitoreando..." if self.monitoring else "⏸️ Detenido"
        
        stats = f"[bold cyan]📊 Estadísticas[/]\n\n"
        stats += f"Estado:               {status}\n"
        stats += f"Total de dispositivos: [yellow]{total}[/]\n"
        stats += f"Online:               [green]{online}[/]\n"
        stats += f"Offline:              [red]{offline}[/]\n"
        stats += f"Eventos registrados:  {len(self.events)}\n"
        
        if self.monitoring:
            stats += f"Intervalo de escaneo: {self.scan_interval}s"
        
        return stats
    
    def clear_data(self) -> None:
        """Limpia los datos almacenados"""
        count = len(self.known_devices)
        self.known_devices.clear()
        self.events.clear()
        
        table = self.query_one("#devices-table", DataTable)
        table.clear()
        
        self.query_one("#events", Static).update(
            "[bold cyan]📋 Eventos Recientes[/]\n\nNo hay eventos registrados"
        )
        self.query_one("#stats", Static).update(self.get_stats_text())
        
        self.notify(f"Datos limpiados ({count} dispositivos eliminados)", severity="information")


def main():
    """Función principal"""
    app = NetworkChangeDetectorApp()
    app.run()


if __name__ == "__main__":
    main()
