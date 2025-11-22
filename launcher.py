"""
Launcher - Menú principal para CosicasDeTerminal
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
from textual.screen import Screen
import subprocess
import sys
from about_screen import AboutScreen


class MainMenuScreen(Screen):
    """Pantalla del menú principal con categorías"""
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("escape", "app.pop_screen", "Volver", show=False),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with Container(id="content"):
                yield Static("🌐 COSICAS DE TERMINAL", id="title")
                yield Static("Selecciona una categoría de herramientas", id="subtitle")
                
                # Herramientas Básicas
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔧 Herramientas Básicas", 
                                   variant="primary", 
                                   classes="category-button",
                                   id="cat-basic")
                        yield Static(
                            "9 herramientas fundamentales de análisis y monitoreo de red",
                            classes="description"
                        )
                
                # Herramientas Avanzadas
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("⚙️ Herramientas avanzadas", 
                                   variant="success", 
                                   classes="category-button",
                                   id="cat-advanced")
                        yield Static(
                            "7 herramientas especializadas para diagnóstico y análisis profundo",
                            classes="description"
                        )
                
                # Herramientas de Seguridad
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔒 Herramientas de Seguridad", 
                                   variant="warning", 
                                   classes="category-button",
                                   id="cat-security")
                        yield Static(
                            "5 herramientas para análisis de seguridad y vulnerabilidades",
                            classes="description"
                        )
                
                # Diagnóstico y Privacidad
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔧 Diagnóstico y Privacidad", 
                                   variant="error", 
                                   classes="category-button",
                                   id="cat-diagnostic")
                        yield Static(
                            "4 herramientas avanzadas para diagnóstico y verificación de privacidad",
                            classes="description"
                        )
                
                # Botones de sistema
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("ℹ️ Acerca de", 
                                   variant="primary", 
                                   classes="app-button",
                                   id="btn-about")
                        yield Static(
                            "Información del programa y repositorio",
                            classes="description"
                        )
                    
                    with Vertical(classes="button-column"):
                        yield Button("❌ Salir", 
                                   variant="error", 
                                   classes="app-button",
                                   id="btn-quit")
                        yield Static(
                            "Cerrar la aplicación",
                            classes="description"
                        )
                
                yield Static(
                    "💡 25 herramientas profesionales de red y seguridad\n"
                    "Pulsa ESC para volver • Q para salir",
                    id="footer-info"
                )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja los eventos de los botones"""
        if event.button.id == "cat-basic":
            self.app.push_screen(BasicToolsScreen())
        elif event.button.id == "cat-advanced":
            self.app.push_screen(AdvancedToolsScreen())
        elif event.button.id == "cat-security":
            self.app.push_screen(SecurityToolsScreen())
        elif event.button.id == "cat-diagnostic":
            self.app.push_screen(DiagnosticToolsScreen())
        elif event.button.id == "btn-about":
            self.app.push_screen(AboutScreen())
        elif event.button.id == "btn-quit":
            self.app.exit()


class BasicToolsScreen(Screen):
    """Pantalla de herramientas básicas"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Volver"),
        Binding("q", "app.pop_screen", "Volver"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with Container(id="content"):
                yield Static("🔧 HERRAMIENTAS BÁSICAS", id="title")
                yield Static("9 herramientas de análisis y monitorización", id="subtitle")
                
                # Fila 1
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔍 Escáner de red local", variant="primary", classes="app-button", id="btn-scanner")
                        yield Static("Escanea tu red local y descubre todos los dispositivos conectados", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("📊 Monitor de red", variant="success", classes="app-button", id="btn-monitor")
                        yield Static("Monitorea velocidad, conexiones activas y estadísticas en tiempo real", classes="description")
                
                # Fila 2
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🛠️ Diagnóstico", variant="warning", classes="app-button", id="btn-tools")
                        yield Static("Ping, Traceroute, DNS, Port Scanner, Whois y más", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("🌐 Verificador conectividad", variant="primary", classes="app-button", id="btn-connectivity")
                        yield Static("Verifica conectividad, DNS, latencia y detecta proxy/VPN", classes="description")
                
                # Fila 3
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("📡 Monitor de interfaces", variant="success", classes="app-button", id="btn-interface")
                        yield Static("Información detallada de todas las interfaces de red", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("🔌 Escáner puertos locales", variant="warning", classes="app-button", id="btn-localports")
                        yield Static("Escanea puertos locales en escucha e identifica procesos", classes="description")
                
                # Fila 4
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("📶 Analizador WiFi", variant="primary", classes="app-button", id="btn-wifi")
                        yield Static("Escanea redes WiFi disponibles con señal y seguridad", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("💾 Monitor de Uso de Red", variant="success", classes="app-button", id="btn-netusage")
                        yield Static("Monitorización en tiempo real de uso de red por proceso", classes="description")
                
                # Fila 5
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🖥️ Info sistema de red", variant="warning", classes="app-button", id="btn-sysinfo")
                        yield Static("Información completa del sistema de red y configuración", classes="description")
                    with Vertical(classes="button-column"):
                        pass
                
                yield Static("💡 Pulsa ESC para volver al menú principal", id="footer-info")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja los eventos de los botones"""
        actions = {
            "btn-scanner": "network_scanner.py",
            "btn-monitor": "network_monitor.py",
            "btn-tools": "network_tools.py",
            "btn-connectivity": "connectivity_checker.py",
            "btn-interface": "interface_monitor.py",
            "btn-localports": "local_port_scanner.py",
            "btn-wifi": "wifi_analyzer.py",
            "btn-netusage": "simple_network_monitor.py",
            "btn-sysinfo": "network_system_info.py",
        }
        
        if event.button.id in actions:
            self.app.suspend()
            subprocess.run([sys.executable, actions[event.button.id]])
            self.app.refresh()


class AdvancedToolsScreen(Screen):
    """Pantalla de herramientas avanzadas"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Volver"),
        Binding("q", "app.pop_screen", "Volver"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with Container(id="content"):
                yield Static("⚙️ HERRAMIENTAS AVANZADAS", id="title")
                yield Static("7 herramientas especializadas", id="subtitle")
                
                # Fila 1
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔢 Calculadora subredes", variant="primary", classes="app-button", id="btn-subnet")
                        yield Static("Calcula rangos IP, máscaras y divide redes en subredes", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("🔍 DNS avanzado", variant="success", classes="app-button", id="btn-dns")
                        yield Static("Consulta múltiples tipos de registros DNS y compara servidores", classes="description")
                
                # Fila 2
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔒 Verificador SSL/TLS", variant="primary", classes="app-button", id="btn-ssl")
                        yield Static("Valida certificados SSL, muestra fecha de expiración y cadena", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("🚀 Test de velocidad", variant="success", classes="app-button", id="btn-speedtest")
                        yield Static("Mide velocidad de subida, bajada, ping y jitter", classes="description")
                
                # Fila 3
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔍 Detector de Cambios", variant="warning", classes="app-button", id="btn-detector")
                        yield Static("Detecta cuando dispositivos se conectan o desconectan", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("🌍 Localizador GEOIP", variant="primary", classes="app-button", id="btn-geoip")
                        yield Static("Geolocalización de IPs y dominios con mapa de datos", classes="description")
                
                # Fila 4
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🕵️ Inspector HTTP", variant="success", classes="app-button", id="btn-http")
                        yield Static("Prueba APIs y analiza cabeceras HTTP/HTTPS", classes="description")
                    with Vertical(classes="button-column"):
                        pass
                
                yield Static("💡 Pulsa ESC para volver al menú principal", id="footer-info")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja los eventos de los botones"""
        actions = {
            "btn-subnet": "subnet_calculator.py",
            "btn-dns": "dns_advanced.py",
            "btn-ssl": "ssl_checker.py",
            "btn-speedtest": "speedtest_app.py",
            "btn-detector": "network_change_detector.py",
            "btn-geoip": "geoip_locator.py",
            "btn-http": "http_inspector.py",
        }
        
        if event.button.id in actions:
            self.app.suspend()
            subprocess.run([sys.executable, actions[event.button.id]])
            self.app.refresh()


class SecurityToolsScreen(Screen):
    """Pantalla de herramientas de seguridad"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Volver"),
        Binding("q", "app.pop_screen", "Volver"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with Container(id="content"):
                yield Static("🔒 HERRAMIENTAS DE SEGURIDAD", id="title")
                yield Static("5 herramientas de análisis de seguridad", id="subtitle")
                
                # Fila 1
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🛡️ Vulnerabilidades", variant="warning", classes="app-button", id="btn-vuln")
                        yield Static("Detecta puertos y configuraciones inseguras", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("🔐 Generador Contraseñas", variant="primary", classes="app-button", id="btn-password")
                        yield Static("Genera y analiza contraseñas seguras con cálculo de entropía", classes="description")
                
                # Fila 2
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔍 Seguridad Web", variant="success", classes="app-button", id="btn-websec")
                        yield Static("Analiza cabeceras de seguridad HTTP de sitios web", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("📊 Ancho de Banda", variant="warning", classes="app-button", id="btn-bandwidth")
                        yield Static("Monitorea qué procesos están usando la red", classes="description")
                
                # Fila 3
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🌐 Enumerador Subdominios", variant="primary", classes="app-button", id="btn-subdomain")
                        yield Static("Descubre subdominios usando certificados y DNS", classes="description")
                    with Vertical(classes="button-column"):
                        pass
                
                yield Static("💡 Presiona ESC para volver al menú principal", id="footer-info")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja los eventos de los botones"""
        actions = {
            "btn-vuln": "vuln_port_scanner.py",
            "btn-password": "password_generator.py",
            "btn-websec": "web_security_analyzer.py",
            "btn-bandwidth": "bandwidth_analyzer.py",
            "btn-subdomain": "subdomain_enumerator.py",
        }
        
        if event.button.id in actions:
            self.app.suspend()
            subprocess.run([sys.executable, actions[event.button.id]])
            self.app.refresh()


class DiagnosticToolsScreen(Screen):
    """Pantalla de herramientas de diagnóstico y privacidad"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Volver"),
        Binding("q", "app.pop_screen", "Volver"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with Container(id="content"):
                yield Static("🔧 DIAGNÓSTICO Y PRIVACIDAD", id="title")
                yield Static("4 herramientas avanzadas de diagnóstico", id="subtitle")
                
                # Fila 1
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🔒 Verificador de Fugas", variant="error", classes="app-button", id="btn-leak")
                        yield Static("Detecta fugas DNS, IPv6, WebRTC y verifica VPN", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("🔧 Troubleshooter", variant="warning", classes="app-button", id="btn-troubleshoot")
                        yield Static("Diagnóstico automático de problemas de red con soluciones", classes="description")
                
                # Fila 2
                with Horizontal(classes="button-row"):
                    with Vertical(classes="button-column"):
                        yield Button("🌍 Latencia Geográfica", variant="primary", classes="app-button", id="btn-geolatency")
                        yield Static("Prueba latencia a diferentes regiones del mundo", classes="description")
                    with Vertical(classes="button-column"):
                        yield Button("📋 Visor de Logs", variant="success", classes="app-button", id="btn-logviewer")
                        yield Static("Explora y busca archivos de logs del sistema", classes="description")
                
                yield Static("💡 Pulsa ESC para volver al menú principal", id="footer-info")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja los eventos de los botones"""
        actions = {
            "btn-leak": "leak_tester.py",
            "btn-troubleshoot": "network_troubleshooter.py",
            "btn-geolatency": "geo_latency_monitor.py",
            "btn-logviewer": "log_viewer.py",
        }
        
        if event.button.id in actions:
            self.app.suspend()
            subprocess.run([sys.executable, actions[event.button.id]])
            self.app.refresh()


class NetworkLauncherApp(App):
    """Aplicación launcher para CosicasDeTerminal"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #content {
        width: 100%;
        height: auto;
        padding: 2 4;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #subtitle {
        text-align: center;
        color: $text;
        margin-bottom: 2;
    }
    
    .button-row {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    
    .button-column {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }
    
    .app-button {
        width: 100%;
        margin-bottom: 1;
        height: 3;
    }
    
    .category-button {
        width: 100%;
        margin-bottom: 1;
        height: 4;
    }
    
    #footer-info {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
        margin-bottom: 2;
    }
    
    .description {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
        padding: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
    ]
    
    def on_mount(self) -> None:
        """Al montar, mostrar el menú principal"""
        self.push_screen(MainMenuScreen())


def main():
    """Función principal"""
    app = NetworkLauncherApp()
    app.run()


if __name__ == "__main__":
    main()
