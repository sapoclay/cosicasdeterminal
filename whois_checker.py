from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Input, Label, Static, TextArea, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
import subprocess
import socket
import threading

class WhoisCheckerApp(App):
    """Herramienta de WHOIS y Reputación IP"""
    
    TITLE = "🌍 Whois & Reputación IP"
    CSS = """
    Screen {
        background: $surface;
    }
    
    .input-box {
        height: auto;
        padding: 1;
        background: $panel;
        margin-bottom: 1;
    }
    
    #whois-input, #rep-input {
        width: 1fr;
    }
    
    Button {
        width: auto;
        min-width: 15;
        margin-left: 1;
    }
    
    TextArea {
        height: 1fr;
        border: solid $secondary;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with TabbedContent():
            with TabPane("🌍 WHOIS Lookup", id="tab-whois"):
                with Horizontal(classes="input-box"):
                    yield Label("Dominio/IP: ")
                    yield Input(placeholder="google.com", id="whois-input")
                    yield Button("🔍 Consultar", id="btn-whois", variant="primary")
                
                yield TextArea(id="whois-output", read_only=True)
                
            with TabPane("🚫 Reputación IP (Blacklists)", id="tab-rep"):
                with Horizontal(classes="input-box"):
                    yield Label("Dominio/IP: ")
                    yield Input(placeholder="1.2.3.4 o dominio.com", id="rep-input")
                    yield Button("🛡️ Verificar", id="btn-rep", variant="warning")
                
                yield TextArea(id="rep-output", read_only=True)
        
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-whois":
            target = self.query_one("#whois-input", Input).value
            if target:
                self.query_one("#whois-output", TextArea).text = "⏳ Consultando WHOIS..."
                self.run_worker(lambda: self._perform_whois(target), thread=True)
        elif event.button.id == "btn-rep":
            target = self.query_one("#rep-input", Input).value
            if target:
                self.query_one("#rep-output", TextArea).text = "⏳ Verificando listas negras (esto puede tardar)..."
                self.run_worker(lambda: self._perform_reputation(target), thread=True)

    def _perform_whois(self, target):
        try:
            # Try system 'whois' command
            result = subprocess.run(['whois', target], capture_output=True, text=True)
            output = result.stdout
            if result.stderr:
                output += "\nErrors:\n" + result.stderr
                
            if not output.strip():
                output = "No se obtuvo respuesta. Asegúrate de tener 'whois' instalado."
                
            self.app.call_from_thread(self._update_whois, output)
        except FileNotFoundError:
             self.app.call_from_thread(self._update_whois, "Error: El comando 'whois' no está instalado en el sistema.")
        except Exception as e:
             self.app.call_from_thread(self._update_whois, f"Error: {e}")

    def _update_whois(self, text):
        self.query_one("#whois-output", TextArea).text = text

    def _perform_reputation(self, target):
        # Resolve domain if needed
        ip = target
        try:
            # Check if it's a valid IP
            socket.inet_aton(target)
        except socket.error:
            # Not an IP, try to resolve
            try:
                self.app.call_from_thread(self._update_rep, f"Resolviendo {target}...")
                ip = socket.gethostbyname(target)
            except socket.gaierror:
                self.app.call_from_thread(self._update_rep, f"Error: No se pudo resolver el dominio '{target}'")
                return

        # Common DNSBLs
        blacklists = [
            "zen.spamhaus.org",
            "bl.spamcop.net",
            "b.barracudacentral.org",
            "dnsbl.sorbs.net",
            "spam.dnsbl.sorbs.net",
            "all.s5h.net",
            "virbl.dnsbl.bit.nl"
        ]
        
        results = f"Resultados de reputación para {target} ({ip}):\n\n"
        listed_count = 0
        
        for bl in blacklists:
            try:
                # Reverse IP for DNS query: 1.2.3.4 -> 4.3.2.1.zen.spamhaus.org
                rev_ip = '.'.join(reversed(ip.split('.')))
                query = f"{rev_ip}.{bl}"
                
                socket.gethostbyname(query)
                results += f"❌ LISTADA en {bl}\n"
                listed_count += 1
            except socket.gaierror:
                results += f"✅ Limpia en {bl}\n"
            except Exception as e:
                results += f"⚠️ Error consultando {bl}: {e}\n"
        
        if listed_count == 0:
            results += "\n✨ ¡La IP parece limpia en las listas consultadas!"
        else:
            results += f"\n⚠️ ¡Cuidado! La IP está listada en {listed_count} listas negras."
            
        self.app.call_from_thread(self._update_rep, results)

    def _update_rep(self, text):
        self.query_one("#rep-output", TextArea).text = text

if __name__ == "__main__":
    WhoisCheckerApp().run()
