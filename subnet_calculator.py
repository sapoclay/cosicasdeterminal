"""
Calculadora Universal de Subredes (IPv4 / IPv6)
Calcula rangos, máscaras, formatos y divide redes
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label
from textual.binding import Binding
import ipaddress
import math

class SubnetCalculatorApp(App):
    """Aplicación de calculadora de subredes universal"""
    
    TITLE = "🧮 Calculadora IP Universal"
    
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
    
    .section {
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .input-group {
        height: auto;
        margin-bottom: 1;
    }
    
    .input-label {
        width: 25;
        content-align: left middle;
    }
    
    Input {
        width: 1fr;
    }
    
    Button {
        margin: 0 1;
    }
    
    .result-box {
        border: solid $primary;
        padding: 1 2;
        height: auto;
        background: $panel;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("c", "calculate", "Calcular"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with ScrollableContainer(id="main-container"):
            with Vertical(id="title-section"):
                yield Static("🔢 CALCULADORA IP UNIVERSAL (v4/v6)", classes="title")
            
            # Sección de entrada
            with Vertical(classes="section"):
                yield Static("📝 Datos de Entrada", classes="section-title")
                
                with Horizontal(classes="input-group"):
                    yield Label("Dirección IP:", classes="input-label")
                    yield Input(placeholder="Ej: 192.168.1.0 o 2001:db8::1", id="ip-input")
                
                with Horizontal(classes="input-group"):
                    yield Label("Prefijo/Máscara:", classes="input-label")
                    yield Input(placeholder="Ej: 24, 255.255.255.0 o 64", id="mask-input")
                
                with Horizontal(classes="input-group"):
                    yield Button("🔍 Calcular", variant="primary", id="calc-btn")
                    yield Button("🗑️ Limpiar", variant="warning", id="clear-btn")
            
            # Sección de resultados - Información básica
            with Vertical(classes="section"):
                yield Static("📊 Información de red", classes="section-title")
                yield Static("Escribe una dirección IP para ver los resultados", 
                           id="basic-results", classes="result-box")
            
            # Sección de división de subredes
            with Vertical(classes="section"):
                yield Static("✂️ División de subredes", classes="section-title")
                
                with Horizontal(classes="input-group"):
                    yield Label("Número de subredes:", classes="input-label")
                    yield Input(placeholder="Ej: 4", id="subnets-input")
                
                with Horizontal(classes="input-group"):
                    yield Button("✂️ Dividir", variant="success", id="divide-btn")
                
                yield Static("", id="subnets-results", classes="result-box")
            
            # Conversión y Formatos
            with Vertical(classes="section"):
                yield Static("🔄 Formatos y Conversiones", classes="section-title")
                yield Static("", id="formats", classes="result-box")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "calc-btn":
            self.calculate_network()
        elif event.button.id == "clear-btn":
            self.clear_all()
        elif event.button.id == "divide-btn":
            self.divide_subnets()
    
    def calculate_network(self) -> None:
        try:
            ip_input = self.query_one("#ip-input", Input).value.strip()
            mask_input = self.query_one("#mask-input", Input).value.strip()
            
            if not ip_input:
                self.notify("Por favor escribe la IP", severity="warning")
                return
            
            # Auto-detect default prefix if empty
            if not mask_input:
                if ':' in ip_input: mask_input = "64"
                else: mask_input = "24"
            
            # Procesar máscara IPv4 si es decimal
            if '.' in mask_input and ':' not in mask_input and mask_input.count('.') == 3:
                mask_obj = ipaddress.IPv4Address(mask_input)
                cidr = bin(int(mask_obj)).count('1')
                mask_input = str(cidr)
            
            # Crear objeto de red (Universal)
            network = ipaddress.ip_network(f"{ip_input}/{mask_input}", strict=False)
            ip_obj = ipaddress.ip_address(ip_input)
            version = network.version
            
            # Construir resultado
            result = f"[bold cyan]📡 Información de Red (IPv{version})[/]\n\n"
            result += f"Dirección IP:       [yellow]{ip_obj}[/]\n"
            result += f"Red (Prefijo):      [green]{network.network_address}[/]\n"
            
            if version == 4:
                num_hosts = network.num_addresses - 2
                if num_hosts < 0: num_hosts = 0
                result += f"Primera IP:         [green]{network.network_address + 1}[/]\n"
                result += f"Última IP:          [green]{network.network_address + network.num_addresses - 2}[/]\n"
                result += f"Broadcast:          [red]{network.broadcast_address}[/]\n"
                result += f"Máscara:            [cyan]{network.netmask}[/]\n"
                result += f"Wildcard:           [cyan]{network.hostmask}[/]\n"
            else:
                result += f"Primera IP:         {network.network_address}\n"
                result += f"Última IP:          {network.broadcast_address}\n"
            
            result += f"CIDR:               /{network.prefixlen}\n"
            result += f"Total IPs:          {network.num_addresses}\n"
            
            # Tipos
            types = []
            if ip_obj.is_private: types.append("Privada")
            if ip_obj.is_global: types.append("Global")
            if ip_obj.is_multicast: types.append("Multicast")
            if ip_obj.is_loopback: types.append("Loopback")
            if ip_obj.is_link_local: types.append("Link-Local")
            result += f"Tipo:               [magenta]{', '.join(types) or 'Unicast'}[/]\n"
            
            self.query_one("#basic-results", Static).update(result)
            
            # Actualizar formatos
            self.update_formats(ip_obj, network)
            self.notify("Cálculo completado")
            
        except ValueError as e:
            self.notify(f"Error: {str(e)}", severity="error")
            self.query_one("#basic-results", Static).update(f"[red]Error:[/]\n{str(e)}")

    def update_formats(self, ip_obj, network):
        fmt = f"[bold cyan]🔄 Representaciones[/]\n\n"
        
        if network.version == 6:
            fmt += f"Comprimida:         {ip_obj.compressed}\n"
            fmt += f"Expandida:          {ip_obj.exploded}\n"
            fmt += f"Hexadecimal:        {hex(int(ip_obj))}\n"
        else:
            fmt += f"Binario:            {bin(int(ip_obj))[2:].zfill(32)}\n"
            fmt += f"Hexadecimal:        {hex(int(ip_obj))}\n"
            fmt += f"Integer:            {int(ip_obj)}\n"
            
        fmt += f"\n[bold cyan]🔍 Reverse DNS[/]\n"
        fmt += f"PTR:                {ip_obj.reverse_pointer}\n"
        
        self.query_one("#formats", Static).update(fmt)

    def divide_subnets(self) -> None:
        try:
            ip_input = self.query_one("#ip-input", Input).value.strip()
            mask_input = self.query_one("#mask-input", Input).value.strip()
            subnets_input = self.query_one("#subnets-input", Input).value.strip()
            
            if not ip_input or not subnets_input:
                self.notify("Faltan datos", severity="warning")
                return
                
            # Auto-detect mask
            if not mask_input:
                if ':' in ip_input: mask_input = "64"
                else: mask_input = "24"
            
            # Fix IPv4 mask
            if '.' in mask_input and ':' not in mask_input and mask_input.count('.') == 3:
                mask_obj = ipaddress.IPv4Address(mask_input)
                mask_input = str(bin(int(mask_obj)).count('1'))

            network = ipaddress.ip_network(f"{ip_input}/{mask_input}", strict=False)
            num_subnets = int(subnets_input)
            
            if num_subnets < 2:
                self.notify("Mínimo 2 subredes", severity="warning")
                return

            # Calculate bits needed
            bits_needed = math.ceil(math.log2(num_subnets))
            new_prefixlen = network.prefixlen + bits_needed
            max_bits = 128 if network.version == 6 else 32
            
            if new_prefixlen > max_bits:
                self.notify(f"Imposible dividir: /{new_prefixlen} excede /{max_bits}", severity="error")
                return
            
            subnets = list(network.subnets(prefixlen_diff=bits_needed))
            
            result = f"[bold cyan]✂️ División en {len(subnets)} Subredes (IPv{network.version})[/]\n"
            result += f"Nueva máscara: /{new_prefixlen}\n\n"
            
            limit = 50 # Limit output to avoid UI lag
            for i, subnet in enumerate(subnets[:limit], 1):
                result += f"[yellow]Subred {i}:[/]\n"
                result += f"  Red: {subnet.network_address}/{new_prefixlen}\n"
                if network.version == 4:
                    result += f"  Rango: {subnet.network_address + 1} - {subnet.broadcast_address - 1}\n"
                    result += f"  Broadcast: {subnet.broadcast_address}\n"
                else:
                    result += f"  Inicio: {subnet.network_address}\n"
                    result += f"  Fin: {subnet.broadcast_address}\n"
                result += "\n"
                
            if len(subnets) > limit:
                result += f"[red]... y {len(subnets) - limit} subredes más (ocultas)[/]"
                
            self.query_one("#subnets-results", Static).update(result)
            self.notify(f"Dividido en {len(subnets)} subredes")
            
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def clear_all(self):
        self.query_one("#ip-input", Input).value = ""
        self.query_one("#mask-input", Input).value = ""
        self.query_one("#subnets-input", Input).value = ""
        self.query_one("#basic-results", Static).update("Esperando datos...")
        self.query_one("#subnets-results", Static).update("")
        self.query_one("#formats", Static).update("")
        self.notify("Campos limpiados")

def main():
    app = SubnetCalculatorApp()
    app.run()

if __name__ == "__main__":
    main()
