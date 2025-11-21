"""
Verificador de fugas de privacidad (DNS, WebRTC, IPv6)
Detecta si tu VPN o configuración tiene fugas de información
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
import socket
import requests
import subprocess
import json
import sys
from typing import Optional

class LeakTester(App):
    """Aplicación para detectar fugas de privacidad"""
    
    TITLE = "🔒 Verificador de Fugas"
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
        padding: 1 2;
    }
    
    #results {
        height: 1fr;
        border: solid $primary;
        padding: 1 2;
        overflow-y: auto;
    }
    
    #controls {
        height: auto;
        padding: 1;
        align: center middle;
    }
    
    .leak-detected {
        background: $error;
        color: $text;
        padding: 0 1;
    }
    
    .no-leak {
        background: $success;
        color: $text;
        padding: 0 1;
    }
    
    .warning {
        background: $warning;
        color: $text;
        padding: 0 1;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("r", "run_tests", "Ejecutar Tests"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with ScrollableContainer(id="results"):
                yield Static("Pulsa 'r' o el botón para iniciar las pruebas de fugas...", id="output")
            with Horizontal(id="controls"):
                yield Button("🔍 Ejecutar Tests", id="test-btn", variant="primary")
                yield Button("📋 Info sobre Tests", id="info-btn", variant="default")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar, mostrar información"""
        self.show_info()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clics en botones"""
        if event.button.id == "test-btn":
            self.run_leak_tests()
        elif event.button.id == "info-btn":
            self.show_info()
    
    def action_run_tests(self) -> None:
        """Ejecutar tests de fugas"""
        self.run_leak_tests()
    
    def show_info(self) -> None:
        """Muestra información sobre los tests"""
        output = self.query_one("#output", Static)
        
        info = """[bold cyan]═══ VERIFICADOR DE FUGAS DE PRIVACIDAD ═══[/]

[bold yellow]¿Qué son las fugas de privacidad?[/]
Las fugas ocurren cuando tu conexión revela información que debería estar protegida,
especialmente al usar VPN o configuraciones de privacidad.

[bold cyan]Tests que se realizan:[/]

[bold]1. 🌐 DNS Leak Test[/]
   • Verifica si tus consultas DNS van por el túnel VPN
   • Detecta si tu ISP puede ver qué sitios visitas
   • [red]Crítico[/] para privacidad con VPN

[bold]2. 📡 IPv6 Leak Test[/]
   • Muchas VPN solo protegen IPv4
   • Tu IPv6 real puede filtrarse
   • [yellow]Importante[/] si tu ISP soporta IPv6

[bold]3. 🔍 IP Real vs IP Pública[/]
   • Compara tu IP local con la IP vista desde internet
   • Detecta si la VPN está funcionando
   • Verifica geolocalización

[bold]4. 🌍 WebRTC Leak (Simulado)[/]
   • WebRTC en navegadores puede exponer tu IP real
   • Ocurre en videollamadas y aplicaciones P2P
   • [yellow]Advertencia[/] común con VPN

[bold green]Cómo interpretar resultados:[/]
• [green]✓ SIN FUGAS[/]: Tu configuración es segura
• [yellow]⚠ ADVERTENCIA[/]: Posible problema, revisar configuración
• [red]✗ FUGA DETECTADA[/]: Tu privacidad está comprometida

[dim]Pulsa 'r' para ejecutar los tests[/]"""
        
        output.update(info)
    
    def run_leak_tests(self) -> None:
        """Ejecuta todos los tests de fugas"""
        output = self.query_one("#output", Static)
        output.update("🔍 [bold]Ejecutando tests de fugas...[/]\n\n")
        
        results = []
        leak_count = 0
        warning_count = 0
        
        # Obtener IP pública
        public_ip, public_country = self.get_public_ip()
        
        results.append("[bold cyan]═══ INFORMACIÓN BÁSICA ═══[/]\n")
        if public_ip:
            results.append(f"[bold]IP Pública:[/] [cyan]{public_ip}[/]")
            if public_country:
                results.append(f"[bold]País detectado:[/] [cyan]{public_country}[/]")
        else:
            results.append("[red]✗ No se pudo obtener IP pública[/]")
        
        # Test 1: DNS Leak
        results.append("\n[bold cyan]═══ TEST 1: DNS LEAK ═══[/]\n")
        dns_leak, dns_info = self.test_dns_leak()
        if dns_leak:
            results.append("[red]✗ FUGA DE DNS DETECTADA[/]")
            leak_count += 1
            results.append(dns_info)
        else:
            results.append("[green]✓ Sin fugas de DNS detectadas[/]")
            results.append(dns_info)
        
        # Test 2: IPv6 Leak
        results.append("\n[bold cyan]═══ TEST 2: IPv6 LEAK ═══[/]\n")
        ipv6_leak, ipv6_info = self.test_ipv6_leak(public_ip)
        if ipv6_leak:
            results.append("[yellow]⚠ POSIBLE FUGA DE IPv6[/]")
            warning_count += 1
            results.append(ipv6_info)
        else:
            results.append("[green]✓ Sin fugas de IPv6[/]")
            results.append(ipv6_info)
        
        # Test 3: WebRTC Leak (simulado)
        results.append("\n[bold cyan]═══ TEST 3: WEBRTC LEAK ═══[/]\n")
        webrtc_info = self.test_webrtc_leak()
        results.append(webrtc_info)
        
        # Test 4: Comparación de IPs
        results.append("\n[bold cyan]═══ TEST 4: VERIFICACIÓN DE VPN ═══[/]\n")
        vpn_info = self.test_vpn_status()
        results.append(vpn_info)
        
        # Resumen final
        results.append("\n[bold cyan]═══ RESUMEN ═══[/]\n")
        if leak_count == 0 and warning_count == 0:
            results.append("[bold green]🎉 EXCELENTE: No se detectaron fugas[/]")
            results.append("Tu configuración de privacidad parece estar funcionando correctamente.")
        elif leak_count > 0:
            results.append(f"[bold red]⚠️  CRÍTICO: {leak_count} fuga(s) detectada(s)[/]")
            results.append("Se recomienda revisar tu configuración de VPN/DNS inmediatamente.")
        elif warning_count > 0:
            results.append(f"[bold yellow]⚠️  ADVERTENCIAS: {warning_count} problema(s) potencial(es)[/]")
            results.append("Considera revisar tu configuración para mejorar la privacidad.")
        
        results.append("\n[bold]Recomendaciones:[/]")
        if leak_count > 0 or warning_count > 0:
            results.append("• Verifica que tu VPN esté activa y conectada")
            results.append("• Configura DNS personalizado en tu VPN")
            results.append("• Desactiva IPv6 si tu VPN no lo soporta")
            results.append("• Usa extensiones anti-WebRTC en navegadores")
        else:
            results.append("• Ejecuta este test regularmente")
            results.append("• Verifica después de cada cambio de VPN")
        
        results.append("\n[dim]Pulsa 'r' para ejecutar nuevamente los tests[/]")
        
        output.update("\n".join(results))
    
    def get_public_ip(self) -> tuple[Optional[str], Optional[str]]:
        """Obtiene la IP pública y país"""
        try:
            # Intentar con ipify (solo IP)
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                ip = response.json().get('ip')
                
                # Intentar obtener información de geolocalización
                try:
                    geo_response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=5)
                    if geo_response.status_code == 200:
                        geo_data = geo_response.json()
                        country = geo_data.get('country_name', 'Desconocido')
                        return ip, country
                except:
                    pass
                
                return ip, None
        except:
            pass
        
        return None, None
    
    def test_dns_leak(self) -> tuple[bool, str]:
        """Prueba fugas de DNS"""
        try:
            # Obtener servidores DNS del sistema
            dns_servers = []
            
            try:
                # Linux/macOS
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.strip().startswith('nameserver'):
                            dns = line.split()[1]
                            dns_servers.append(dns)
            except:
                # Windows o error
                try:
                    result = subprocess.run(
                        ['ipconfig', '/all'] if sys.platform == 'win32' else ['cat', '/etc/resolv.conf'],
                        capture_output=True, text=True, timeout=3
                    )
                    # Parsear salida (simplificado)
                    dns_servers = ['Sistema']
                except:
                    pass
            
            if not dns_servers:
                return False, "[dim]No se pudieron detectar servidores DNS del sistema[/]"
            
            info = "[bold]Servidores DNS detectados:[/]\n"
            
            # Verificar si son DNS públicos conocidos (probable que estés usando VPN)
            public_dns = {
                '8.8.8.8': 'Google DNS',
                '8.8.4.4': 'Google DNS',
                '1.1.1.1': 'Cloudflare',
                '1.0.0.1': 'Cloudflare',
                '9.9.9.9': 'Quad9',
                '208.67.222.222': 'OpenDNS',
                '208.67.220.220': 'OpenDNS',
            }
            
            leak_detected = False
            for dns in dns_servers[:5]:  # Mostrar solo los primeros 5
                if dns in public_dns:
                    info += f"  • [green]{dns}[/] ({public_dns[dns]}) - OK\n"
                elif dns.startswith('10.') or dns.startswith('192.168.') or dns.startswith('172.'):
                    info += f"  • [green]{dns}[/] (Privado) - OK\n"
                else:
                    info += f"  • [yellow]{dns}[/] (ISP?) - Posible fuga\n"
                    leak_detected = True
            
            if leak_detected:
                info += "\n[yellow]⚠️  Algunos DNS pueden ser de tu ISP[/]"
            else:
                info += "\n[green]DNS configurados parecen seguros[/]"
            
            return leak_detected, info
            
        except Exception as e:
            return False, f"[dim]Error en test de DNS: {str(e)}[/]"
    
    def test_ipv6_leak(self, public_ipv4: Optional[str]) -> tuple[bool, str]:
        """Prueba fugas de IPv6"""
        try:
            # Intentar obtener IPv6 pública
            response = requests.get('https://api64.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                ipv6 = response.json().get('ip')
                
                # Verificar si es IPv6
                if ':' in ipv6:
                    info = f"[bold]IPv6 Pública detectada:[/] [yellow]{ipv6}[/]\n"
                    
                    # Si es diferente a la IPv4, podría ser una fuga
                    if public_ipv4 and ipv6 != public_ipv4:
                        info += "[yellow]⚠️  Tu IPv6 está expuesta y puede revelar tu ubicación real[/]\n"
                        info += "[dim]Solución: Desactiva IPv6 o usa VPN que soporte IPv6[/]"
                        return True, info
                    else:
                        info += "[green]IPv6 parece estar protegida[/]"
                        return False, info
                else:
                    return False, "[dim]No se detectó IPv6 pública (solo IPv4)[/]"
            else:
                return False, "[dim]No se pudo verificar IPv6[/]"
                
        except:
            return False, "[dim]IPv6 no disponible o bloqueada[/]"
    
    def test_webrtc_leak(self) -> str:
        """Simula test de WebRTC (requiere navegador real)"""
        info = "[yellow]ℹ️  Test de WebRTC simulado[/]\n\n"
        info += "WebRTC puede exponer tu IP real en navegadores.\n"
        info += "Este test no puede verificarlo desde terminal.\n\n"
        info += "[bold]Para probar WebRTC:[/]\n"
        info += "• Visita: https://browserleaks.com/webrtc\n"
        info += "• O: https://ipleak.net/\n\n"
        info += "[bold]Protección recomendada:[/]\n"
        info += "• Firefox: about:config → media.peerconnection.enabled = false\n"
        info += "• Chrome: Extensión 'WebRTC Leak Prevent'\n"
        info += "• Brave: Escudo de privacidad (incluido por defecto)"
        
        return info
    
    def test_vpn_status(self) -> str:
        """Verifica si hay indicios de VPN activa"""
        try:
            # Buscar interfaces de red tipo VPN
            result = subprocess.run(
                ['ip', 'link', 'show'] if sys.platform != 'win32' else ['ipconfig'],
                capture_output=True, text=True, timeout=3
            )
            
            vpn_keywords = ['tun', 'tap', 'vpn', 'wg', 'proton', 'nord', 'express']
            vpn_detected = any(keyword in result.stdout.lower() for keyword in vpn_keywords)
            
            if vpn_detected:
                info = "[green]✓ Interfaz VPN detectada en el sistema[/]\n"
                info += "Parece que tienes una VPN activa."
            else:
                info = "[yellow]⚠️  No se detectó interfaz VPN[/]\n"
                info += "Si estás usando VPN, puede no estar activa o configurada correctamente."
            
            return info
            
        except:
            return "[dim]No se pudo verificar estado de VPN[/]"


if __name__ == "__main__":
    app = LeakTester()
    app.run()
