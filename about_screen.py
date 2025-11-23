from textual.screen import Screen
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll, Container
from textual.widgets import Static
import os

class AboutScreen(Screen):
    """Pantalla de información del programa"""
    
    CSS = """
    AboutScreen {
        align: center middle;
        background: 0%;
    }
    
    #about-container {
        width: 80;
        height: 80%;
        background: $surface;
        border: heavy $primary;
        overflow: hidden;
    }
    
    #scroll-content {
        width: 100%;
        height: 100%;
        padding: 1 2;
        overflow-y: auto;
    }
    
    .logo-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin-bottom: 1;
        padding-top: 1;
    }

    #logo-display {
        text-align: center;
        width: 100%;
    }
    
    #about-content {
        width: 100%;
        height: auto;
        text-align: center;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Cerrar"),
        Binding("q", "close", "Cerrar"),
        Binding("enter", "close", "Cerrar"),
        Binding("space", "close", "Cerrar"),
    ]
    
    def compose(self) -> ComposeResult:
        # Texto de información
        about_text = """
[bold cyan]╔═══════════════════════════════════════════════╗[/]
[bold cyan]║        📋 ACERCA DE ESTE PROGRAMA 📋          ║[/]
[bold cyan]╚═══════════════════════════════════════════════╝[/]

[bold green]CosicasDeTerminal - Cosas para hacer cosas[/]

[bold blue]Descripción:[/]
  Suite de utilidades para administración,
  diagnóstico y monitorización de redes.

[bold blue]Características:[/]
  [cyan]Análisis de Red:[/]
  • Escáner de red y monitor de tráfico
  • Verificador de conectividad y DNS
  • Monitor de interfaces de red
  • Escáner de puertos locales
  • Analizador WiFi y uso de red
  • Info completa del sistema de red
  
  [cyan]Herramientas Avanzadas:[/]
  • Calculadora IP Universal (IPv4/IPv6)
  • Verificador SSL/TLS y test de velocidad
  • Detector de cambios en la red
  • Localizador GeoIP para IPs y dominios
  • Inspector HTTP/API para pruebas de endpoints
  • Analizador de Paquetes (Sniffer) en tiempo real
  • Escucha de Puertos (TCP/UDP) para diagnóstico
  • Cambiador de MAC y Crypto Tool (Base64/Hash)
  • Extractor de Metadatos (Exif) de imágenes
  • Analizador de vulnerabilidades de puertos
  • Generador y analizador de contraseñas seguras
  
  [cyan]Seguridad:[/]
  • Analizador de seguridad web
  • Enumerador de subdominios
  
  [cyan]Diagnóstico y Privacidad:[/]
  • Verificador de fugas (DNS/IPv6/WebRTC/VPN)
  • Troubleshooter (diagnóstico automático)
  • Monitor de latencia geográfica
  • Monitor de latencia geográfica
  • Visor de logs (Soporte CLI/SSH/Cross-platform)
  • Wake on LAN y Gestor Conexiones (SSH/FTP)
  
[bold yellow]32 herramientas profesionales en una suite[/]

[bold blue]Tecnologías:[/]
  • Python 3.12+
  • Textual TUI Framework
  • psutil, netifaces, requests

[bold blue]Repositorio:[/]
  [yellow]https://github.com/sapoclay/cosicasdeterminal[/]

[bold green]Desarrollado con ☕ y 🚬  para quien lo necesite por entreunosyceros.net[/]

[dim]Pulsa cualquier tecla para volver...[/]"""

        with Container(id="about-container"):
            with VerticalScroll(id="scroll-content"):
                # Intentar cargar imagen
                logo_path = "img/logo.png"
                logo_shown = False
                
                if os.path.exists(logo_path):
                    # Generar ASCII art usando Pillow
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(logo_path)
                        aspect_ratio = img.height / img.width
                        new_width = 50
                        new_height = int(aspect_ratio * new_width * 0.55)
                        img = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
                        img = img.convert('L')
                        
                        ascii_chars = '@%#*+=-:. '
                        ascii_art = []
                        for y in range(img.height):
                            line = ""
                            for x in range(img.width):
                                pixel_value = img.getpixel((x, y))
                                # Asegurar que pixel sea un entero
                                if isinstance(pixel_value, (tuple, list)):
                                    pixel = int(pixel_value[0])
                                else:
                                    pixel = int(pixel_value) if pixel_value is not None else 0
                                char_index = min(pixel * len(ascii_chars) // 256, len(ascii_chars) - 1)
                                line += ascii_chars[char_index]
                            ascii_art.append(line)
                        
                        logo_ascii = '\n'.join(ascii_art)
                        with Container(classes="logo-container"):
                            yield Static(f"[cyan]{logo_ascii}[/]", id="logo-display")
                        logo_shown = True
                    except Exception:
                        pass
                
                if not logo_shown:
                    # Logo de texto fallback
                    text_logo = """
[bold cyan]    ╔═══════════════════════════════════╗
    ║   🌐  COSICAS DE TERMINAL  🌐   ║
    ╚═══════════════════════════════════╝[/]
"""
                    with Container(classes="logo-container"):
                        yield Static(text_logo, id="logo-display")
                
                yield Static(about_text, id="about-content")
    
    def on_mount(self) -> None:
        """Asegurar foco al montar"""
        self.focus()
    
    def action_close(self) -> None:
        """Cierra la pantalla de about"""
        self.dismiss()
