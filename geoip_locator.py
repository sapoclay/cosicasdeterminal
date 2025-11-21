from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, Label
from textual.binding import Binding
import requests
import json

class GeoIPLocatorApp(App):
    """Aplicación para geolocalización de IPs"""
    
    TITLE = "🌍 Localizador GeoIP"
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        padding: 2 4;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #input-container {
        height: auto;
        margin-bottom: 2;
        align: center middle;
    }
    
    .description {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    
    #input-target {
        width: 60%;
    }
    
    #btn-lookup {
        margin-left: 2;
    }
    
    #results-container {
        height: 1fr;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
        margin-top: 1;
    }
    
    .result-line {
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("escape", "quit", "Salir"),
        Binding("enter", "lookup", "Buscar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Static("🌍 LOCALIZADOR GEOIP", id="title")
            yield Static("Obtén información geográfica de cualquier IP pública o dominio", classes="description")
            
            with Horizontal(id="input-container"):
                yield Input(placeholder="Ej: 8.8.8.8 o google.com", id="input-target")
                yield Button("🔍 Localizar", variant="primary", id="btn-lookup")
            
            with VerticalScroll(id="results-container"):
                yield Static("Escribe una IP o dominio arriba y pulsa Intro...", id="results-content")
                
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-lookup":
            self.lookup_ip()
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.lookup_ip()

    def lookup_ip(self):
        target = self.query_one("#input-target", Input).value.strip()
        if not target:
            return
            
        results_widget = self.query_one("#results-content", Static)
        results_widget.update("⏳ Consultando base de datos de geolocalización...")
        
        try:
            # Usamos ip-api.com (gratuito para uso no comercial, sin API key)
            # Protocolo HTTP para evitar problemas de certificados en algunos entornos, o HTTPS si es posible
            url = f"http://ip-api.com/json/{target}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get("status") == "fail":
                results_widget.update(f"[bold red]❌ Error:[/bold red] {data.get('message', 'Consulta fallida')}")
                return

            # Formatear salida
            output = f"""
[bold cyan]📍 Resultados para: {data.get('query')}[/]

[bold white]Ubicación geográfica[/]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[green]País:[/green]        {data.get('country')} ({data.get('countryCode')})
[green]Región:[/green]      {data.get('regionName')} ({data.get('region')})
[green]Ciudad:[/green]      {data.get('city')}
[green]Código Postal:[/green] {data.get('zip')}
[green]Coordenadas:[/green]   {data.get('lat')}, {data.get('lon')}
[green]Zona Horaria:[/green]  {data.get('timezone')}

[bold white]Información de Red[/]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[green]ISP:[/green]         {data.get('isp')}
[green]Organización:[/green] {data.get('org')}
[green]ASN:[/green]          {data.get('as')}

[dim]Datos proporcionados por ip-api.com[/]
            """
            results_widget.update(output)
            
        except Exception as e:
            results_widget.update(f"[bold red]❌ Error de conexión:[/bold red] {str(e)}\nVerifica tu conexión a internet.")

if __name__ == "__main__":
    GeoIPLocatorApp().run()
