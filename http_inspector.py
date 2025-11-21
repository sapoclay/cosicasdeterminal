from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, Label, RadioSet, RadioButton, TabbedContent, TabPane
from textual.binding import Binding
import requests
import time
import json

class HTTPInspectorApp(App):
    """Herramienta para inspeccionar peticiones HTTP"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        padding: 1 2;
    }
    
    #header-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #controls-container {
        height: auto;
        background: $panel;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    #url-row {
        height: auto;
        margin-bottom: 1;
        align: center middle;
    }
    
    #input-url {
        width: 1fr;
        margin-right: 1;
    }
    
    #method-row {
        height: auto;
        align: center middle;
    }
    
    #method-selector {
        layout: horizontal;
        height: auto;
    }
    
    RadioButton {
        width: auto;
        margin-right: 2;
    }
    
    #status-bar {
        background: $panel;
        padding: 1;
        margin-bottom: 1;
        text-align: center;
        text-style: bold;
    }
    
    .content-area {
        padding: 1;
    }
    
    #json-output {
        color: $text;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("escape", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Static("🕵️ INSPECTOR HTTP/API", id="header-title")
            
            with Vertical(id="controls-container"):
                with Horizontal(id="url-row"):
                    yield Label("URL: ", classes="label")
                    yield Input(placeholder="https://api.ejemplo.com/v1/data", id="input-url")
                    yield Button("Enviar petición", variant="primary", id="btn-send")
                
                with Horizontal(id="method-row"):
                    yield Label("Método: ", classes="label")
                    with RadioSet(id="method-selector"):
                        yield RadioButton("GET", value=True)
                        yield RadioButton("POST")
                        yield RadioButton("HEAD")
                        yield RadioButton("OPTIONS")
                        yield RadioButton("PUT")
                        yield RadioButton("DELETE")

            yield Static("Listo para enviar petición...", id="status-bar")

            with TabbedContent():
                with TabPane("Resumen", id="tab-summary"):
                    yield VerticalScroll(Static("Los detalles de la respuesta aparecerán aquí.", id="summary-content", classes="content-area"))
                
                with TabPane("Headers", id="tab-headers"):
                    yield VerticalScroll(Static("", id="headers-content", classes="content-area"))
                
                with TabPane("Cuerpo (Body)", id="tab-body"):
                    yield VerticalScroll(Static("", id="body-content", classes="content-area"))
                    
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-send":
            self.send_request()
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-url":
            self.send_request()

    def send_request(self):
        url = self.query_one("#input-url", Input).value.strip()
        if not url:
            self.query_one("#status-bar", Static).update("[red]❌ Error: La URL no puede estar vacía[/]")
            return
        
        if not url.startswith("http"):
            url = "https://" + url
            self.query_one("#input-url", Input).value = url
            
        method_radio = self.query_one("#method-selector", RadioSet).pressed_button
        method = str(method_radio.label) if method_radio else "GET"
        
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(f"⏳ Enviando petición {method} a {url}...")
        
        try:
            start_time = time.time()
            # Headers básicos para simular un navegador y evitar bloqueos simples
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NetworkTools/1.0; +http://github.com/sapoclay)'
            }
            
            response = requests.request(method, url, headers=headers, timeout=15)
            elapsed = (time.time() - start_time) * 1000
            
            # Determinar color del estado
            if 200 <= response.status_code < 300:
                status_color = "green"
                status_icon = "✅"
            elif 300 <= response.status_code < 400:
                status_color = "yellow"
                status_icon = "⚠️"
            else:
                status_color = "red"
                status_icon = "❌"
            
            status_text = f"[{status_color}]{status_icon} Status: {response.status_code} {response.reason}[/] | ⏱️ Tiempo: {elapsed:.0f}ms | 📦 Tamaño: {len(response.content)} bytes"
            status_bar.update(status_text)
            
            # Actualizar Resumen
            summary = f"""
[bold underline]Detalles de la petición[/]
[bold]URL:[/bold] {url}
[bold]Método:[/bold] {method}
[bold]Tiempo:[/bold] {elapsed:.2f} ms

[bold underline]Detalles de la Respuesta[/]
[bold]Estado:[/bold] [{status_color}]{response.status_code} {response.reason}[/]
[bold]Codificación:[/bold] {response.encoding}
[bold]Content-Type:[/bold] {response.headers.get('Content-Type', 'N/A')}
[bold]Tamaño:[/bold] {len(response.content)} bytes
            """
            self.query_one("#summary-content", Static).update(summary)
            
            # Actualizar Headers
            headers_text = ""
            for k, v in response.headers.items():
                headers_text += f"[bold cyan]{k}:[/] [white]{v}[/]\n"
            self.query_one("#headers-content", Static).update(headers_text)
            
            # Actualizar Body
            content_type = response.headers.get('Content-Type', '').lower()
            body_text = ""
            
            if 'json' in content_type:
                try:
                    json_obj = response.json()
                    body_text = f"```json\n{json.dumps(json_obj, indent=2)}\n```"
                except:
                    body_text = response.text
            elif 'html' in content_type or 'xml' in content_type:
                # Truncar si es muy largo para evitar congelar la UI
                if len(response.text) > 50000:
                    body_text = f"[yellow]⚠️ El contenido es muy largo ({len(response.text)} caracteres). Mostrando los primeros 5000...[/]\n\n"
                    body_text += f"```html\n{response.text[:5000]}\n...```"
                else:
                    body_text = f"```html\n{response.text}\n```"
            else:
                if len(response.text) > 10000:
                    body_text = f"[yellow]⚠️ Contenido truncado...[/]\n{response.text[:10000]}"
                else:
                    body_text = response.text
                    
            self.query_one("#body-content", Static).update(body_text)

        except requests.exceptions.RequestException as e:
            status_bar.update(f"[bold red]❌ Error de conexión:[/bold red] {str(e)}")
            self.query_one("#summary-content", Static).update(f"[red]No se pudo completar la petición a {url}[/]\n\nError: {str(e)}")
            self.query_one("#headers-content", Static).update("")
            self.query_one("#body-content", Static).update("")

if __name__ == "__main__":
    HTTPInspectorApp().run()
