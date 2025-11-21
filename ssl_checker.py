"""
Valida certificados, muestra fecha de expiración y cadena
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label
from textual.binding import Binding
import ssl
import socket
from datetime import datetime
from functools import partial


class SSLCheckerApp(App):
    """Aplicación de verificación de certificados SSL/TLS"""
    
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
    
    .input-section {
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
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
    
    #results-section {
        height: 1fr;
        border: solid $primary;
        padding: 1 2;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("c", "check", "Verificar"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compone la interfaz de usuario"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="title-section"):
                yield Static("🔒 VERIFICADOR DE CERTIFICADOS SSL/TLS", classes="title")
            
            with Vertical(classes="input-section"):
                yield Static("📝 Configuración", classes="section-title")
                
                with Horizontal(classes="input-group"):
                    yield Label("Host:", classes="input-label")
                    yield Input(placeholder="Ej: google.com", id="host-input")
                
                with Horizontal(classes="input-group"):
                    yield Label("Puerto:", classes="input-label")
                    yield Input(placeholder="443", value="443", id="port-input")
                
                with Horizontal(classes="input-group"):
                    yield Button("🔒 Verificar SSL", variant="primary", id="check-btn")
                    yield Button("🗑️ Limpiar", variant="warning", id="clear-btn")
            
            with ScrollableContainer(id="results-section"):
                yield Static("Ingresa un host para verificar su certificado SSL/TLS", id="results")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "check-btn":
            self.action_check()
        elif event.button.id == "clear-btn":
            self.clear_results()
    
    def action_check(self) -> None:
        """Verifica el certificado SSL"""
        host = self.query_one("#host-input", Input).value.strip()
        port_str = self.query_one("#port-input", Input).value
        
        if not host:
            self.notify("Por favor ingresa un host", severity="warning")
            return
        
        # Limpiar el host de protocolos y www
        host = host.replace('https://', '').replace('http://', '')
        host = host.replace('www.', '')
        # Eliminar trailing slash y path
        host = host.split('/')[0]
        
        try:
            port = int(port_str) if port_str else 443
        except ValueError:
            self.notify("Puerto inválido", severity="error")
            return
        
        results_widget = self.query_one("#results", Static)
        results_widget.update(f"⏳ Verificando certificado SSL de {host}:{port}...\n")
        
        worker_func = partial(self.check_ssl_certificate, host, port)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def check_ssl_certificate(self, host: str, port: int) -> dict:
        """Verifica el certificado SSL/TLS"""
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
                    
                    # Analizar certificado
                    result = {
                        'host': host,
                        'port': port,
                        'cert': cert,
                        'cipher': cipher,
                        'version': version,
                        'error': None
                    }
                    
                    return result
        
        except ssl.SSLError as e:
            return {'error': f"Error SSL: {str(e)}"}
        except socket.gaierror:
            return {'error': "No se pudo resolver el host"}
        except socket.timeout:
            return {'error': "Timeout de conexión"}
        except Exception as e:
            return {'error': f"Error: {str(e)}"}
    
    def on_worker_state_changed(self, event) -> None:
        """Se ejecuta cuando cambia el estado del worker"""
        if event.state.name == "SUCCESS":
            result = event.worker.result
            if result and result.get('error') is None:
                self.display_ssl_results(result)
            else:
                error_msg = result.get('error', 'Error desconocido') if result else 'Error desconocido'
                self.query_one("#results", Static).update(f"[red]❌ {error_msg}[/]\n\n💡 Verifica que:\n  • El host sea correcto (sin https:// ni www)\n  • El puerto sea el correcto (normalmente 443)\n  • El servidor tenga SSL/TLS configurado")
                self.notify("Error al verificar certificado", severity="error")
        elif event.state.name == "ERROR":
            self.query_one("#results", Static).update("[red]❌ Error al verificar certificado[/]")
            self.notify("Error al verificar certificado", severity="error")
    
    def display_ssl_results(self, result: dict) -> None:
        """Muestra los resultados de la verificación SSL"""
        cert = result['cert']
        
        output = f"[bold cyan]🔒 Información del certificado SSL/TLS[/]\n\n"
        output += f"Host:    [yellow]{result['host']}:{result['port']}[/]\n"
        output += f"Versión: [cyan]{result['version']}[/]\n\n"
        
        # Información del certificado
        output += f"[bold]📜 certificado:[/]\n\n"
        
        # Subject (para quién es el certificado)
        subject = dict(x[0] for x in cert['subject'])
        output += f"Emitido para:\n"
        if 'commonName' in subject:
            output += f"  CN: [green]{subject['commonName']}[/]\n"
        if 'organizationName' in subject:
            output += f"  O:  {subject['organizationName']}\n"
        if 'countryName' in subject:
            output += f"  C:  {subject['countryName']}\n"
        
        output += "\n"
        
        # Issuer (quién lo emitió)
        issuer = dict(x[0] for x in cert['issuer'])
        output += f"Emitido por:\n"
        if 'commonName' in issuer:
            output += f"  CN: [yellow]{issuer['commonName']}[/]\n"
        if 'organizationName' in issuer:
            output += f"  O:  {issuer['organizationName']}\n"
        
        output += "\n"
        
        # Fechas de validez
        not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        now = datetime.now()
        
        days_remaining = (not_after - now).days
        
        output += f"[bold]📅 Validez:[/]\n\n"
        output += f"Válido desde: {not_before.strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"Válido hasta: {not_after.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if days_remaining > 30:
            output += f"Estado:       [green]✓ Válido ({days_remaining} días restantes)[/]\n"
        elif days_remaining > 0:
            output += f"Estado:       [yellow]⚠ Expira pronto ({days_remaining} días restantes)[/]\n"
        else:
            output += f"Estado:       [red]✗ EXPIRADO (hace {abs(days_remaining)} días)[/]\n"
        
        output += "\n"
        
        # SANs (Subject Alternative Names)
        if 'subjectAltName' in cert:
            output += f"[bold]🌐 Nombres Alternativos (SANs):[/]\n\n"
            for san_type, san_value in cert['subjectAltName']:
                output += f"  • {san_value}\n"
            output += "\n"
        
        # Información del cifrado
        output += f"[bold]🔐 Cifrado:[/]\n\n"
        cipher = result['cipher']
        output += f"Cipher Suite: [cyan]{cipher[0]}[/]\n"
        output += f"Protocolo:    {cipher[1]}\n"
        output += f"Bits:         {cipher[2]}\n"
        
        output += "\n"
        
        # Serial Number
        if 'serialNumber' in cert:
            output += f"[bold]🔢 Número de Serie:[/]\n{cert['serialNumber']}\n"
        
        self.query_one("#results", Static).update(output)
        
        # Notificación según estado
        if days_remaining > 30:
            self.notify(f"✓ Certificado válido ({days_remaining} días)", severity="information")
        elif days_remaining > 0:
            self.notify(f"⚠ Certificado expira en {days_remaining} días", severity="warning")
        else:
            self.notify("✗ Certificado EXPIRADO", severity="error")
    
    def clear_results(self) -> None:
        """Limpia los resultados"""
        self.query_one("#host-input", Input).value = ""
        self.query_one("#port-input", Input).value = "443"
        self.query_one("#results", Static).update(
            "Ingresa un host para verificar su certificado SSL/TLS"
        )
        self.notify("Campos limpiados", severity="information")


def main():
    """Función principal"""
    app = SSLCheckerApp()
    app.run()


if __name__ == "__main__":
    main()
