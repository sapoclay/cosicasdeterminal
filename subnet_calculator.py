"""
Calcula rangos IP, máscaras y divide redes en subredes
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label
from textual.binding import Binding
import ipaddress


class SubnetCalculatorApp(App):
    """Aplicación de calculadora de subredes"""
    
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
        width: 20;
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
        """Compone la interfaz de usuario"""
        yield Header()
        
        with ScrollableContainer(id="main-container"):
            with Vertical(id="title-section"):
                yield Static("🔢 CALCULADORA DE SUBREDES", classes="title")
            
            # Sección de entrada
            with Vertical(classes="section"):
                yield Static("📝 Datos de Entrada", classes="section-title")
                
                with Horizontal(classes="input-group"):
                    yield Label("Dirección IP:", classes="input-label")
                    yield Input(placeholder="Ej: 192.168.1.0", id="ip-input")
                
                with Horizontal(classes="input-group"):
                    yield Label("Máscara (CIDR o decimal):", classes="input-label")
                    yield Input(placeholder="Ej: 24 o 255.255.255.0", id="mask-input")
                
                with Horizontal(classes="input-group"):
                    yield Button("🔍 Calcular", variant="primary", id="calc-btn")
                    yield Button("🗑️ Limpiar", variant="warning", id="clear-btn")
            
            # Sección de resultados - Información básica
            with Vertical(classes="section"):
                yield Static("📊 Información de red", classes="section-title")
                yield Static("Escribe una dirección IP y máscara para ver los resultados", 
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
            
            # Conversión de máscaras
            with Vertical(classes="section"):
                yield Static("🔄 Conversión de máscaras", classes="section-title")
                yield Static("", id="mask-conversion", classes="result-box")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "calc-btn":
            self.calculate_network()
        elif event.button.id == "clear-btn":
            self.clear_all()
        elif event.button.id == "divide-btn":
            self.divide_subnets()
    
    def action_calculate(self) -> None:
        """Acción de teclado para calcular"""
        self.calculate_network()
    
    def calculate_network(self) -> None:
        """Calcula la información de la red"""
        try:
            ip_input = self.query_one("#ip-input", Input).value
            mask_input = self.query_one("#mask-input", Input).value
            
            if not ip_input or not mask_input:
                self.notify("Por favor escribe la IP y máscara", severity="warning")
                return
            
            # Procesar máscara
            if mask_input.count('.') == 3:
                # Es una máscara decimal, convertir a CIDR
                mask_obj = ipaddress.IPv4Address(mask_input)
                cidr = bin(int(mask_obj)).count('1')
            else:
                cidr = int(mask_input)
            
            # Crear objeto de red
            network = ipaddress.IPv4Network(f"{ip_input}/{cidr}", strict=False)
            
            # Calcular información
            num_hosts = network.num_addresses - 2  # Excluir red y broadcast
            if num_hosts < 0:
                num_hosts = 0
            
            # Construir resultado
            result = f"[bold cyan]📡 Información de Red[/]\n\n"
            result += f"Dirección de Red:    [yellow]{network.network_address}[/]\n"
            result += f"Primera IP utilizable: [green]{network.network_address + 1}[/]\n"
            result += f"Última IP utilizable:  [green]{network.network_address + network.num_addresses - 2}[/]\n"
            result += f"Dirección Broadcast:  [red]{network.broadcast_address}[/]\n"
            result += f"Máscara de Red:      [cyan]{network.netmask}[/]\n"
            result += f"Máscara Wildcard:    [cyan]{network.hostmask}[/]\n"
            result += f"CIDR:               /{cidr}\n"
            result += f"Total de IPs:       {network.num_addresses}\n"
            result += f"IPs Utilizables:    {num_hosts}\n"
            result += f"Clase:              {self.get_ip_class(network.network_address)}\n"
            
            # Si es privada
            if network.is_private:
                result += f"Tipo:               [green]Red Privada[/]\n"
            else:
                result += f"Tipo:               [yellow]Red Pública[/]\n"
            
            self.query_one("#basic-results", Static).update(result)
            
            # Actualizar conversión de máscaras
            self.update_mask_conversion(network)
            
            self.notify("Cálculo completado", severity="information")
            
        except ValueError as e:
            self.notify(f"Error: {str(e)}", severity="error")
            self.query_one("#basic-results", Static).update(
                f"[red]Error: Dirección IP o máscara inválida[/]\n{str(e)}"
            )
    
    def get_ip_class(self, ip: ipaddress.IPv4Address) -> str:
        """Determina la clase de una dirección IP"""
        first_octet = int(str(ip).split('.')[0])
        if first_octet < 128:
            return "A (0-127)"
        elif first_octet < 192:
            return "B (128-191)"
        elif first_octet < 224:
            return "C (192-223)"
        elif first_octet < 240:
            return "D (224-239) - Multicast"
        else:
            return "E (240-255) - Experimental"
    
    def update_mask_conversion(self, network: ipaddress.IPv4Network) -> None:
        """Actualiza la sección de conversión de máscaras"""
        result = f"[bold cyan]🔄 Conversiones[/]\n\n"
        result += f"Notación CIDR:       /{network.prefixlen}\n"
        result += f"Máscara decimal:     {network.netmask}\n"
        result += f"Máscara hexadecimal: {hex(int(network.netmask))}\n"
        result += f"Máscara binaria:     {bin(int(network.netmask))[2:].zfill(32)}\n"
        result += f"Wildcard decimal:    {network.hostmask}\n"
        result += f"Bits de red:         {network.prefixlen}\n"
        result += f"Bits de host:        {32 - network.prefixlen}\n"
        
        self.query_one("#mask-conversion", Static).update(result)
    
    def divide_subnets(self) -> None:
        """Divide la red en subredes"""
        try:
            ip_input = self.query_one("#ip-input", Input).value
            mask_input = self.query_one("#mask-input", Input).value
            subnets_input = self.query_one("#subnets-input", Input).value
            
            if not ip_input or not mask_input or not subnets_input:
                self.notify("Por favor completa todos los campos", severity="warning")
                return
            
            num_subnets = int(subnets_input)
            if num_subnets < 2:
                self.notify("Debe haber al menos 2 subredes", severity="warning")
                return
            
            # Procesar máscara
            if mask_input.count('.') == 3:
                mask_obj = ipaddress.IPv4Address(mask_input)
                cidr = bin(int(mask_obj)).count('1')
            else:
                cidr = int(mask_input)
            
            network = ipaddress.IPv4Network(f"{ip_input}/{cidr}", strict=False)
            
            # Calcular nuevo prefixlen
            import math
            bits_needed = math.ceil(math.log2(num_subnets))
            new_prefixlen = network.prefixlen + bits_needed
            
            if new_prefixlen > 32:
                self.notify("No se puede dividir en tantas subredes", severity="error")
                return
            
            # Obtener subredes
            subnets = list(network.subnets(prefixlen_diff=bits_needed))
            
            # Construir resultado
            result = f"[bold cyan]✂️ División en {len(subnets)} Subredes[/]\n"
            result += f"Nueva máscara: /{new_prefixlen} ({ipaddress.IPv4Network(f'0.0.0.0/{new_prefixlen}').netmask})\n\n"
            
            for i, subnet in enumerate(subnets[:num_subnets], 1):
                hosts = subnet.num_addresses - 2
                if hosts < 0:
                    hosts = 0
                result += f"[yellow]Subred {i}:[/]\n"
                result += f"  Red: {subnet.network_address}/{new_prefixlen}\n"
                result += f"  Rango: {subnet.network_address + 1} - {subnet.broadcast_address - 1}\n"
                result += f"  Broadcast: {subnet.broadcast_address}\n"
                result += f"  Hosts: {hosts}\n\n"
            
            self.query_one("#subnets-results", Static).update(result)
            self.notify(f"Red dividida en {len(subnets)} subredes", severity="information")
            
        except ValueError as e:
            self.notify(f"Error: {str(e)}", severity="error")
        except Exception as e:
            self.notify(f"Error al dividir: {str(e)}", severity="error")
    
    def clear_all(self) -> None:
        """Limpia todos los campos"""
        self.query_one("#ip-input", Input).value = ""
        self.query_one("#mask-input", Input).value = ""
        self.query_one("#subnets-input", Input).value = ""
        self.query_one("#basic-results", Static).update(
            "Escribe una dirección IP y máscara para ver los resultados"
        )
        self.query_one("#subnets-results", Static).update("")
        self.query_one("#mask-conversion", Static).update("")
        self.notify("Campos limpiados", severity="information")


def main():
    """Función principal"""
    app = SubnetCalculatorApp()
    app.run()


if __name__ == "__main__":
    main()
