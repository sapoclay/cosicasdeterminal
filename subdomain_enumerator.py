from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, ProgressBar
from textual.binding import Binding
import requests
import socket
import ssl
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import time

class SubdomainEnumeratorApp(App):
    """Enumerador de subdominios"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        padding: 1 2;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .description {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    
    #input-container {
        height: auto;
        margin-bottom: 1;
    }
    
    #input-domain {
        width: 1fr;
        margin-right: 1;
    }
    
    #progress-container {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }
    
    #results-container {
        height: 1fr;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
        margin-top: 1;
    }
    
    .warning-box {
        background: $warning;
        color: $text;
        padding: 1;
        margin-bottom: 1;
        border: heavy $error;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("escape", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Static("🔍 ENUMERADOR DE SUBDOMINIOS", id="title")
            yield Static("Descubre subdominios de un dominio objetivo", classes="description")
            
            yield Static(
                "[yellow]⚠️ ADVERTENCIA:[/] Solo escanea dominios que te pertenezcan o con permiso explícito.\n"
                "El escaneo no autorizado puede ser ilegal.",
                classes="warning-box"
            )
            
            with Horizontal(id="input-container"):
                yield Input(placeholder="ejemplo.com", id="input-domain")
                yield Button("🔍 Enumerar", variant="primary", id="btn-enumerate")
            
            with Container(id="progress-container"):
                yield Static("Esperando dominio...", id="scan-status")
                yield ProgressBar(total=100, show_eta=False, id="scan-progress")
            
            with VerticalScroll(id="results-container"):
                yield Static("Escribe un dominio para comenzar la enumeración...", id="enum-results")
                
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-enumerate":
            self.enumerate_subdomains()

    def enumerate_subdomains(self):
        domain = self.query_one("#input-domain", Input).value.strip().lower()
        
        if not domain:
            self.query_one("#enum-results", Static).update(
                "[red]❌ Por favor escribe un dominio válido[/]"
            )
            return
        
        # Limpiar protocolo si existe
        if domain.startswith("http"):
            parsed = urlparse(domain)
            domain = parsed.netloc or parsed.path
        
        status_widget = self.query_one("#scan-status", Static)
        progress_bar = self.query_one("#scan-progress", ProgressBar)
        results_widget = self.query_one("#enum-results", Static)
        
        status_widget.update(f"🔍 Enumerando subdominios de {domain}...")
        results_widget.update("[cyan]Iniciando enumeración de subdominios...[/]")
        
        all_subdomains = set()
        
        # 1. Consultar crt.sh (certificados SSL)
        status_widget.update(f"📜 Consultando certificados SSL (crt.sh)...")
        progress_bar.update(progress=20)
        
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                certs = response.json()
                for cert in certs:
                    name = cert.get('name_value', '')
                    # Limpiar wildcard y añadir
                    for subdomain in name.split('\n'):
                        subdomain = subdomain.strip().replace('*.', '')
                        if subdomain.endswith(domain):
                            all_subdomains.add(subdomain)
        except Exception as e:
            pass
        
        status_widget.update(f"🔍 Consultando API de HackerTarget...")
        progress_bar.update(progress=40)
        
        # 2. Consultar HackerTarget API
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines:
                    if ',' in line:
                        subdomain = line.split(',')[0].strip()
                        if subdomain and subdomain.endswith(domain):
                            all_subdomains.add(subdomain)
        except Exception as e:
            pass
        
        status_widget.update(f"🌐 Probando subdominios comunes...")
        progress_bar.update(progress=60)
        
        # 3. DNS brute force con subdominios comunes
        common_subs = [
            'www', 'mail', 'ftp', 'smtp', 'pop', 'ns1', 'ns2', 'webmail',
            'admin', 'api', 'dev', 'test', 'staging', 'production', 'vpn',
            'blog', 'shop', 'store', 'mobile', 'portal', 'app', 'cdn',
            'images', 'static', 'assets', 'media', 'files', 'download',
            'upload', 'secure', 'login', 'dashboard', 'panel', 'cpanel'
        ]
        
        def check_subdomain(sub):
            try:
                full_domain = f"{sub}.{domain}"
                socket.gethostbyname(full_domain)
                return full_domain
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(check_subdomain, sub): sub for sub in common_subs}
            for future in futures:
                result = future.result()
                if result:
                    all_subdomains.add(result)
        
        progress_bar.update(progress=80)
        status_widget.update(f"🔎 Verificando subdominios encontrados...")
        
        # 4. Verificar cada subdominio
        verified_subdomains = []
        
        def verify_subdomain(subdomain):
            try:
                # Intentar resolver DNS
                ip = socket.gethostbyname(subdomain)
                
                # Intentar conexión HTTP/HTTPS
                http_status = None
                https_status = None
                
                try:
                    resp = requests.head(f"http://{subdomain}", timeout=3, allow_redirects=True)
                    http_status = resp.status_code
                except:
                    pass
                
                try:
                    resp = requests.head(f"https://{subdomain}", timeout=3, allow_redirects=True)
                    https_status = resp.status_code
                except:
                    pass
                
                return {
                    'subdomain': subdomain,
                    'ip': ip,
                    'http': http_status,
                    'https': https_status
                }
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(verify_subdomain, sub) for sub in all_subdomains]
            for future in futures:
                result = future.result()
                if result:
                    verified_subdomains.append(result)
        
        progress_bar.update(progress=100)
        status_widget.update(f"✅ Enumeración completada: {len(verified_subdomains)} subdominios encontrados")
        
        # Generar reporte
        if not verified_subdomains:
            results_widget.update(f"""
[bold yellow]⚠️ NO SE ENCONTRARON SUBDOMINIOS[/]

Dominio analizado: [cyan]{domain}[/]

Posibles razones:
• El dominio no tiene subdominios públicos
• Los subdominios están protegidos contra enumeración
• El dominio no existe o no es accesible

[dim]Fuentes consultadas: crt.sh, HackerTarget, DNS brute-force[/]
            """)
        else:
            # Ordenar por subdominio
            verified_subdomains.sort(key=lambda x: x['subdomain'])
            
            output = f"""
[bold green]✅ ENUMERACIÓN COMPLETADA[/]

Dominio objetivo: [cyan]{domain}[/]
Subdominios encontrados: [bold]{len(verified_subdomains)}[/]

[bold underline]Subdominios Descubiertos:[/]

"""
            
            for item in verified_subdomains:
                subdomain = item['subdomain']
                ip = item['ip']
                http = item['http']
                https = item['https']
                
                # Determinar estado
                if https and (https == 200 or https == 301 or https == 302):
                    status = f"[green]HTTPS:{https}[/]"
                    icon = "🔒"
                elif http and (http == 200 or http == 301 or http == 302):
                    status = f"[yellow]HTTP:{http}[/]"
                    icon = "🔓"
                else:
                    status = "[dim]Sin respuesta web[/]"
                    icon = "📍"
                
                output += f"{icon} [bold cyan]{subdomain}[/]\n"
                output += f"   IP: {ip} | {status}\n\n"
            
            # Análisis de seguridad
            http_only = sum(1 for x in verified_subdomains if x['http'] and not x['https'])
            https_enabled = sum(1 for x in verified_subdomains if x['https'])
            
            output += "\n[bold underline]Análisis de Seguridad:[/]\n\n"
            
            if http_only > 0:
                output += f"[yellow]⚠️ {http_only} subdominios solo accesibles por HTTP (inseguro)[/]\n"
            
            if https_enabled > 0:
                output += f"[green]✅ {https_enabled} subdominios con HTTPS habilitado[/]\n"
            
            output += f"""
[bold cyan]💡 USOS DE ESTA INFORMACIÓN:[/]

[bold]Para defensores:[/]
• Identifica subdominios olvidados o no documentados
• Detecta servicios expuestos innecesariamente
• Verifica que todos usen HTTPS
• Busca subdominios abandonados (subdomain takeover)

[bold]Recomendaciones:[/]
• Asegura que todos los subdominios usen HTTPS
• Elimina subdominios no utilizados
• Mantén un inventario actualizado de subdominios
• Monitorea certificados SSL para detectar nuevos subdominios

[dim]Herramientas avanzadas: subfinder, amass, sublist3r, dnsrecon[/]
            """
            
            results_widget.update(output)

if __name__ == "__main__":
    SubdomainEnumeratorApp().run()
