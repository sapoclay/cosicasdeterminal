"""
Herramienta Criptográfica (Crypto Tool)
Codificador, Decodificador y Hashing
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, TextArea, Select, Label
from textual.binding import Binding
import base64
import hashlib
import codecs
import urllib.parse
import html

class CryptoToolApp(App):
    """Aplicación de Herramientas Criptográficas"""
    
    TITLE = "🔐 Crypto Tool"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        padding: 1 2;
    }
    
    .section {
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
    }
    
    TextArea {
        height: 10;
        border: solid $primary;
    }
    
    .controls {
        height: auto;
        margin: 1 0;
        align: center middle;
    }
    
    Select {
        width: 30;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("c", "clear", "Limpiar"),
    ]
    
    OPERATIONS = [
        ("b64_enc", "Base64 Encode"),
        ("b64_dec", "Base64 Decode"),
        ("hex_enc", "Hex Encode"),
        ("hex_dec", "Hex Decode"),
        ("url_enc", "URL Encode"),
        ("url_dec", "URL Decode"),
        ("html_enc", "HTML Entities Encode"),
        ("html_dec", "HTML Entities Decode"),
        ("rot13", "ROT13"),
        ("md5", "MD5 Hash"),
        ("sha1", "SHA1 Hash"),
        ("sha256", "SHA256 Hash"),
        ("sha512", "SHA512 Hash"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with ScrollableContainer(id="main-container"):
            yield Static("🔐 DECODIFICADOR UNIVERSAL & HASHING", classes="title")
            
            # Entrada
            with Vertical(classes="section"):
                yield Label("Entrada:")
                yield TextArea(id="input-text")
            
            # Controles
            with Horizontal(classes="controls"):
                yield Select(self.OPERATIONS, prompt="Selecciona Operación", id="op-select")
                yield Button("🚀 Procesar", variant="primary", id="btn-process")
                yield Button("🔄 Intercambiar", id="btn-swap")
                yield Button("🗑️ Limpiar", variant="error", id="btn-clear")
            
            # Salida
            with Vertical(classes="section"):
                yield Label("Salida:")
                yield TextArea(id="output-text", read_only=True)
        
        yield Footer()
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-process":
            self.process_text()
        elif event.button.id == "btn-clear":
            self.query_one("#input-text", TextArea).text = ""
            self.query_one("#output-text", TextArea).text = ""
        elif event.button.id == "btn-swap":
            out_text = self.query_one("#output-text", TextArea).text
            self.query_one("#input-text", TextArea).text = out_text
            self.query_one("#output-text", TextArea).text = ""

    def process_text(self):
        text = self.query_one("#input-text", TextArea).text
        op = self.query_one("#op-select", Select).value
        
        if not text:
            self.notify("Escribe algo en la entrada", severity="warning")
            return
        if not op:
            self.notify("Selecciona una operación", severity="warning")
            return
            
        try:
            result = ""
            b_text = text.encode('utf-8')
            
            if op == "b64_enc":
                result = base64.b64encode(b_text).decode('utf-8')
            elif op == "b64_dec":
                result = base64.b64decode(b_text).decode('utf-8')
            elif op == "hex_enc":
                result = b_text.hex()
            elif op == "hex_dec":
                result = bytes.fromhex(text).decode('utf-8')
            elif op == "url_enc":
                result = urllib.parse.quote(text)
            elif op == "url_dec":
                result = urllib.parse.unquote(text)
            elif op == "html_enc":
                result = html.escape(text)
            elif op == "html_dec":
                result = html.unescape(text)
            elif op == "rot13":
                result = codecs.encode(text, 'rot_13')
            elif op == "md5":
                result = hashlib.md5(b_text).hexdigest()
            elif op == "sha1":
                result = hashlib.sha1(b_text).hexdigest()
            elif op == "sha256":
                result = hashlib.sha256(b_text).hexdigest()
            elif op == "sha512":
                result = hashlib.sha512(b_text).hexdigest()
                
            self.query_one("#output-text", TextArea).text = result
            self.notify("Procesado correctamente")
            
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            self.query_one("#output-text", TextArea).text = f"Error: {str(e)}"

def main():
    app = CryptoToolApp()
    app.run()

if __name__ == "__main__":
    main()
