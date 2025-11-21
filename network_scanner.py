"""
Escanea y muestra dispositivos conectados a la red local
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, DataTable, Label, Select
from textual.binding import Binding
import socket
import netifaces
import psutil
from datetime import datetime
import subprocess
import re
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from platform_utils import get_ping_fast_command, get_arp_mac, is_windows


class DeviceInfo(Static):
    """Widget para mostrar información de un dispositivo"""
    
    def __init__(self, ip: str, hostname: str, mac: str, status: str):
        super().__init__()
        self.ip = ip
        self.hostname = hostname
        self.mac = mac
        self.status = status
        self.update_display()
    
    def update_display(self):
        """Actualiza la visualización del dispositivo"""
        status_icon = "🟢" if self.status == "online" else "🔴"
        hostname_text = self.hostname if self.hostname != "Desconocido" else "[dim]Desconocido[/]"
        
        content = f"{status_icon} [bold cyan]{self.ip}[/]\n"
        content += f"   Hostname: {hostname_text}\n"
        content += f"   MAC: [yellow]{self.mac}[/]"
        
        self.update(content)


class NetworkInfo(Static):
    """Widget para mostrar información de la red"""
    
    def __init__(self):
        super().__init__()
        self.interface = None
        self.network_range = None
        self.update_network_info()
    
    def update_network_info(self, interface: str | None = None):
        """Actualiza la información de la red"""
        try:
            # Si no se especifica interfaz, usar la predeterminada
            if interface is None:
                gateways = netifaces.gateways()
                default_info = gateways.get('default', {})
                default_gateway = default_info.get(netifaces.AF_INET) if isinstance(default_info, dict) else None
                
                if default_gateway:
                    interface = default_gateway[1]
                    gateway_ip = default_gateway[0]
                else:
                    interface = "N/A"
                    gateway_ip = "N/A"
            else:
                # Obtener gateway para la interfaz específica
                try:
                    gateways = netifaces.gateways()
                    gateway_ip = None
                    gw_list = gateways.get(netifaces.AF_INET, [])
                    for gw_info in gw_list:
                        if isinstance(gw_info, (list, tuple)) and len(gw_info) >= 2:
                            if gw_info[1] == interface:
                                gateway_ip = gw_info[0]
                                break
                    if gateway_ip is None:
                        gateway_ip = "N/A"
                except:
                    gateway_ip = "N/A"
            
            self.interface = interface
            
            # Obtener IP local
            addrs = netifaces.ifaddresses(interface) if interface != "N/A" else {}
            ip_info = addrs.get(netifaces.AF_INET, [{}])[0]
            local_ip = ip_info.get('addr', 'N/A')
            netmask = ip_info.get('netmask', 'N/A')
            
            # Calcular rango de red
            if local_ip != 'N/A' and netmask != 'N/A':
                network = ipaddress.IPv4Network(f"{local_ip}/{netmask}", strict=False)
                network_range = str(network)
            else:
                network_range = "N/A"
            
            content = f"[bold]📡 INFORMACIÓN DE RED[/]\n\n"
            content += f"Interfaz: [cyan]{interface}[/]\n"
            content += f"IP Local: [green]{local_ip}[/]\n"
            content += f"Máscara: {netmask}\n"
            content += f"Gateway: [yellow]{gateway_ip}[/]\n"
            content += f"Rango: {network_range}\n"
            
            self.network_range = network_range
            self.update(content)
            
        except Exception as e:
            self.update(f"[red]Error al obtener información de red: {e}[/]")
            self.network_range = None


class NetworkScannerApp(App):
    """Aplicación de escaneo de red local"""
    
    TITLE = "📶 Escáner de Red"
    
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
    }
    
    #info-section {
        height: auto;
        width: 100%;
        border: solid $accent;
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
    
    #devices-section {
        height: 1fr;
        width: 100%;
        border: solid $primary;
        padding: 1 2;
    }
    
    #status-bar {
        height: 3;
        width: 100%;
        background: $panel;
        padding: 1 2;
        content-align: center middle;
    }
    
    DeviceInfo {
        width: 100%;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("s", "scan", "Escanear"),
        Binding("r", "refresh", "Refrescar"),
    ]
    
    def __init__(self):
        super().__init__()
        self.devices = []
        self.scanning = False
    
    def compose(self) -> ComposeResult:
        """Compone la interfaz de usuario"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="header-section"):
                yield Static("🔍 ESCÁNER DE RED LOCAL", classes="title")
            
            yield NetworkInfo()
            
            with Horizontal(id="interface-selector"):
                yield Label("Interfaz de Red:", classes="selector-label")
                yield Select([], id="interface-select")
                yield Button("🔄 Cambiar", variant="success", id="change-interface-btn")
            
            with Horizontal(id="controls"):
                yield Button("🔍 Escanear Red", variant="primary", id="scan-btn")
                yield Button("🔄 Refrescar", variant="success", id="refresh-btn")
                yield Button("🗑️ Limpiar", variant="warning", id="clear-btn")
            
            with ScrollableContainer(id="devices-section"):
                yield Static("Presiona 'Escanear Red' para comenzar", id="devices-placeholder")
            
            yield Static("Dispositivos encontrados: 0 | Estado: Listo", id="status-bar")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Se ejecuta cuando la aplicación se monta"""
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
            
        except Exception as e:
            self.notify(f"Error al obtener interfaces: {str(e)}", severity="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "scan-btn":
            self.action_scan()
        elif event.button.id == "refresh-btn":
            self.action_refresh()
        elif event.button.id == "clear-btn":
            self.clear_devices()
        elif event.button.id == "change-interface-btn":
            self.change_interface()
    
    def action_scan(self) -> None:
        """Inicia el escaneo de la red"""
        if self.scanning:
            self.notify("Ya hay un escaneo en progreso", severity="warning")
            return
        
        self.scanning = True
        self.clear_devices()
        
        # Actualizar status
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update("Estado: 🔄 Escaneando red...")
        
        self.notify("Iniciando escaneo de red...", severity="information")
        
        # Obtener información de red
        net_info = self.query_one(NetworkInfo)
        network_range = net_info.network_range
        
        if not network_range or network_range == "N/A":
            self.notify("No se pudo determinar el rango de red", severity="error")
            self.scanning = False
            return
        
        # Escanear red en un thread separado
        from functools import partial
        worker_func = partial(self.scan_network, network_range)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def scan_network(self, network_range: str) -> list:
        """Escanea la red en busca de dispositivos activos"""
        devices = []
        network = ipaddress.IPv4Network(network_range)
        
        # Limitar a redes /24 o más pequeñas
        if network.num_addresses > 256:
            network = ipaddress.IPv4Network(f"{str(network.network_address)}/24", strict=False)
        
        def check_host(ip: str):
            """Verifica si un host está activo"""
            try:
                # Ping rápido (multiplataforma)
                result = subprocess.run(
                    get_ping_fast_command(ip),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2
                )
                
                if result.returncode == 0:
                    # Intentar obtener hostname
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        hostname = "Desconocido"
                    
                    # Intentar obtener MAC (multiplataforma)
                    mac = get_arp_mac(ip) or "Desconocido"
                    
                    return {
                        'ip': ip,
                        'hostname': hostname,
                        'mac': mac,
                        'status': 'online'
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
                    # Actualizar UI en tiempo real
                    self.call_from_thread(self.add_device_to_ui, device)
        
        return devices
    
    def add_device_to_ui(self, device: dict) -> None:
        """Agrega un dispositivo a la UI"""
        # Eliminar placeholder si existe
        try:
            placeholder = self.query_one("#devices-placeholder")
            placeholder.remove()
        except:
            pass
        
        # Agregar dispositivo
        devices_section = self.query_one("#devices-section")
        device_widget = DeviceInfo(
            device['ip'],
            device['hostname'],
            device['mac'],
            device['status']
        )
        self.devices.append(device_widget)
        devices_section.mount(device_widget)
        
        # Actualizar contador
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(f"Dispositivos encontrados: {len(self.devices)} | Estado: 🔄 Escaneando...")
    
    def on_worker_state_changed(self, event) -> None:
        """Se ejecuta cuando cambia el estado del worker"""
        if event.state.name == "SUCCESS":
            self.scanning = False
            status_bar = self.query_one("#status-bar", Static)
            status_bar.update(f"Dispositivos encontrados: {len(self.devices)} | Estado: ✅ Completado")
            self.notify(f"Escaneo completado. {len(self.devices)} dispositivos encontrados", severity="information")
        elif event.state.name == "ERROR":
            self.scanning = False
            status_bar = self.query_one("#status-bar", Static)
            status_bar.update(f"Dispositivos encontrados: {len(self.devices)} | Estado: ❌ Error")
            self.notify("Error durante el escaneo", severity="error")
    
    def change_interface(self) -> None:
        """Cambia la interfaz de red seleccionada"""
        try:
            select = self.query_one("#interface-select", Select)
            selected_interface = str(select.value)
            
            if not selected_interface or selected_interface == "NoSelection":
                self.notify("Por favor selecciona una interfaz", severity="warning")
                return
            
            # Actualizar información de red
            net_info = self.query_one(NetworkInfo)
            net_info.update_network_info(selected_interface)
            
            self.notify(f"Interfaz cambiada a: {selected_interface}", severity="information")
            
        except Exception as e:
            self.notify(f"Error al cambiar interfaz: {str(e)}", severity="error")
    
    def action_refresh(self) -> None:
        """Refresca la información de red"""
        try:
            select = self.query_one("#interface-select", Select)
            selected_interface = str(select.value) if select.value != "NoSelection" else None
            
            net_info = self.query_one(NetworkInfo)
            net_info.update_network_info(selected_interface)
            
            # Refrescar lista de interfaces por si cambió algo
            self.populate_interfaces()
            
            self.notify("Información de red actualizada", severity="information")
        except Exception as e:
            self.notify(f"Error al refrescar: {str(e)}", severity="error")
    
    def clear_devices(self) -> None:
        """Limpia la lista de dispositivos"""
        devices_section = self.query_one("#devices-section")
        
        # Remover todos los dispositivos
        for device in self.devices:
            device.remove()
        
        self.devices.clear()
        
        # Agregar placeholder solo si no existe
        try:
            self.query_one("#devices-placeholder")
        except:
            devices_section.mount(Static("Presiona 'Escanear Red' para comenzar", id="devices-placeholder"))
        
        # Actualizar status
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update("Dispositivos encontrados: 0 | Estado: Listo")


def main():
    """Función principal para ejecutar la aplicación"""
    app = NetworkScannerApp()
    app.run()


if __name__ == "__main__":
    main()
