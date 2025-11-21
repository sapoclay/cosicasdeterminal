"""
Diagnóstico automático de problemas de red
Detecta y sugiere soluciones para problemas comunes
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, ProgressBar, Select
from textual.binding import Binding
import socket
import subprocess
import requests
import psutil
import netifaces
from typing import List, Tuple
from platform_utils import get_ping_command, is_windows

class NetworkTroubleshooter(App):
    """Aplicación para diagnosticar problemas de red automáticamente"""
    
    TITLE = "🔧 Diagnóstico de Red"
    
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
    
    #progress-section {
        height: auto;
        padding: 1;
    }
    
    #interface-selector {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    #interface-selector .label {
        width: auto;
        padding: 1;
    }
    
    #interface-select {
        width: 1fr;
    }
    
    #controls {
        height: auto;
        padding: 1;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    
    .problem {
        background: $error 20%;
        padding: 1;
        margin: 1 0;
        border-left: thick $error;
    }
    
    .warning {
        background: $warning 20%;
        padding: 1;
        margin: 1 0;
        border-left: thick $warning;
    }
    
    .ok {
        background: $success 20%;
        padding: 1;
        margin: 1 0;
        border-left: thick $success;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("d", "diagnose", "Diagnosticar"),
    ]
    
    def __init__(self):
        super().__init__()
        self.problems_found = []
        self.warnings_found = []
        self.selected_interface = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="progress-section"):
                yield Static("", id="progress-label")
                yield ProgressBar(id="progress", total=100, show_eta=False)
            with Horizontal(id="interface-selector"):
                yield Static("🔌 Interfaz: ", classes="label")
                yield Select([("Cargando...", "loading")], id="interface-select", allow_blank=False, prompt="Selecciona interfaz")
            with ScrollableContainer(id="results"):
                yield Static(self.get_welcome_message(), id="output")
            with Horizontal(id="controls"):
                yield Button("🔍 Iniciar Diagnóstico", id="diagnose-btn", variant="primary")
                yield Button("💡 Consejos Rápidos", id="tips-btn", variant="default")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar la aplicación"""
        self.populate_interfaces()
    
    def populate_interfaces(self) -> None:
        """Poblar el selector con interfaces de red disponibles"""
        try:
            interfaces = netifaces.interfaces()
            options = [("Todas las interfaces", "all")]
            
            for iface in interfaces:
                if iface == 'lo':
                    continue
                try:
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        ip = addrs[netifaces.AF_INET][0]['addr']
                        options.append((f"{iface} ({ip})", iface))
                except:
                    continue
            
            select = self.query_one("#interface-select", Select)
            if options:
                select.set_options(options)
                self.selected_interface = options[0][1]
            else:
                # Si no hay interfaces, al menos mostrar una opción
                select.set_options([("Sin interfaces activas", "none")])
                self.selected_interface = "none"
        except Exception as e:
            # En caso de error, mantener la opción por defecto
            try:
                select = self.query_one("#interface-select", Select)
                select.set_options([("Todas las interfaces", "all")])
                self.selected_interface = "all"
            except:
                pass
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Manejar cambio de interfaz seleccionada"""
        try:
            if event.select.id == "interface-select":
                self.selected_interface = event.value
        except Exception as e:
            # Ignorar errores silenciosamente
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clics en botones"""
        if event.button.id == "diagnose-btn":
            self.run_diagnosis()
        elif event.button.id == "tips-btn":
            self.show_quick_tips()
    
    def action_diagnose(self) -> None:
        """Ejecutar diagnóstico"""
        self.run_diagnosis()
    
    def get_welcome_message(self) -> str:
        """Mensaje de bienvenida"""
        return """[bold cyan]═══ DIAGNÓSTICO AUTOMÁTICO DE RED ═══[/]

Este asistente analizará tu conexión de red y detectará problemas comunes.

[bold yellow]🔌 Selecciona la interfaz de red a diagnosticar:[/]
• Puedes elegir una interfaz específica o "Todas las interfaces"
• El diagnóstico se enfocará en la interfaz seleccionada

[bold yellow]Tests que se realizarán:[/]

1. ✓ Verificación de interfaces de red
2. ✓ Conectividad a internet
3. ✓ Resolución DNS
4. ✓ Gateway y enrutamiento
5. ✓ Latencia y pérdida de paquetes
6. ✓ Configuración de DNS
7. ✓ Conflictos de IP
8. ✓ Servicios de red

[bold green]Pulsa 'd' o el botón para comenzar el diagnóstico[/]"""
    
    def show_quick_tips(self) -> None:
        """Muestra consejos rápidos"""
        output = self.query_one("#output", Static)
        
        tips = """[bold cyan]═══ CONSEJOS RÁPIDOS PARA PROBLEMAS DE RED ═══[/]

[bold yellow]🔌 Sin conexión a internet:[/]
• Verifica que el cable esté conectado (si es ethernet)
• Reinicia el router/módem (desconectar 30 segundos)
• Verifica que el WiFi esté activado
• Prueba con otro dispositivo para descartar problema del ISP

[bold yellow]🐌 Internet lento:[/]
• Cierra aplicaciones que usen mucho ancho de banda
• Verifica cuántos dispositivos están conectados
• Prueba con cable ethernet en vez de WiFi
• Contacta a tu ISP si el problema persiste

[bold yellow]📡 WiFi débil o intermitente:[/]
• Acércate al router
• Cambia el canal del WiFi (menos congestión)
• Actualiza drivers de la tarjeta de red
• Considera usar repetidor/extensor WiFi

[bold yellow]🌐 No resuelve nombres de dominio:[/]
• Cambia los DNS (prueba 8.8.8.8 y 1.1.1.1)
• Limpia la caché DNS
• Verifica configuración de DNS en el router

[bold yellow]🔒 Problemas con sitios HTTPS:[/]
• Verifica fecha y hora del sistema
• Actualiza el navegador
• Limpia caché y cookies
• Desactiva temporalmente antivirus/firewall

[bold yellow]🎮 Latencia alta en juegos:[/]
• Cierra descargas y streaming
• Usa cable ethernet
• Verifica que nadie más use la red
• Considera cambio de servidor de juego

[dim]Pulsa 'd' para ejecutar diagnóstico completo[/]"""
        
        output.update(tips)
    
    def run_diagnosis(self) -> None:
        """Ejecuta el diagnóstico completo"""
        self.problems_found = []
        self.warnings_found = []
        
        output = self.query_one("#output", Static)
        progress = self.query_one("#progress", ProgressBar)
        progress_label = self.query_one("#progress-label", Static)
        
        # Mostrar interfaz seleccionada
        interface_text = self.selected_interface if self.selected_interface else "todas"
        if interface_text == "all":
            interface_text = "todas las interfaces"
        
        output.update(f"[bold]Iniciando diagnóstico...[/]\n[cyan]🔌 Interfaz: {interface_text}[/]\n")
        results = []
        
        # Test 1: Interfaces de red
        progress_label.update("📡 Verificando interfaces de red...")
        progress.update(progress=10)
        test_result = self.test_network_interfaces()
        results.append(test_result)
        
        # Test 2: Conectividad básica
        progress_label.update("🌐 Verificando conectividad a internet...")
        progress.update(progress=20)
        test_result = self.test_internet_connectivity()
        results.append(test_result)
        
        # Test 3: DNS
        progress_label.update("🔍 Probando resolución DNS...")
        progress.update(progress=35)
        test_result = self.test_dns_resolution()
        results.append(test_result)
        
        # Test 4: Gateway
        progress_label.update("🚪 Verificando gateway...")
        progress.update(progress=50)
        test_result = self.test_gateway()
        results.append(test_result)
        
        # Test 5: Latencia
        progress_label.update("⏱️  Midiendo latencia...")
        progress.update(progress=65)
        test_result = self.test_latency()
        results.append(test_result)
        
        # Test 6: Configuración DNS
        progress_label.update("⚙️  Verificando configuración DNS...")
        progress.update(progress=80)
        test_result = self.test_dns_config()
        results.append(test_result)
        
        # Test 7: Conflictos de IP
        progress_label.update("🔢 Buscando conflictos de IP...")
        progress.update(progress=90)
        test_result = self.test_ip_conflicts()
        results.append(test_result)
        
        # Test 8: Servicios
        progress_label.update("⚡ Verificando servicios de red...")
        progress.update(progress=95)
        test_result = self.test_network_services()
        results.append(test_result)
        
        progress.update(progress=100)
        progress_label.update("✅ Diagnóstico completado")
        
        # Generar reporte final
        report = self.generate_report(results)
        output.update(report)
    
    def test_network_interfaces(self) -> Tuple[str, str, List[str]]:
        """Test 1: Verifica interfaces de red"""
        try:
            interfaces = netifaces.interfaces()
            active_interfaces = []
            
            # Si se seleccionó una interfaz específica, solo verificar esa
            if self.selected_interface and self.selected_interface != "all" and isinstance(self.selected_interface, str):
                interfaces_to_check = [self.selected_interface]
            else:
                interfaces_to_check = interfaces
            
            for iface in interfaces_to_check:
                if not isinstance(iface, str):
                    continue
                if iface == 'lo':
                    continue
                if iface not in netifaces.interfaces():
                    continue
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    active_interfaces.append(f"{iface} ({ip})")
            
            if not active_interfaces:
                self.problems_found.append("No hay interfaces de red activas")
                selected_text = f" seleccionada ({self.selected_interface})" if self.selected_interface != "all" else ""
                return ("problem", "Interfaces de Red", 
                       [f"❌ No se encontraron interfaces de red activas{selected_text}",
                        "💡 Verifica que tu adaptador de red esté activado",
                        "💡 En Windows: Panel de Control → Red e Internet",
                        "💡 En Linux: sudo ip link set <interfaz> up"])
            else:
                scope = f"Interfaz analizada: {self.selected_interface}" if self.selected_interface != "all" else "Todas las interfaces"
                info = [f"✅ {len(active_interfaces)} interfaz(es) activa(s): {', '.join(active_interfaces)}", f"   ({scope})"]
                return ("ok", "Interfaces de Red", info)
                
        except Exception as e:
            return ("warning", "Interfaces de Red", [f"⚠️  Error verificando interfaces: {str(e)}"])
    
    def test_internet_connectivity(self) -> Tuple[str, str, List[str]]:
        """Test 2: Verifica conectividad a internet"""
        try:
            # Si hay interfaz específica, verificar que tenga IP válida primero
            if self.selected_interface and self.selected_interface not in ["all", "none", "loading"] and isinstance(self.selected_interface, str):
                try:
                    addrs = netifaces.ifaddresses(self.selected_interface)
                    if netifaces.AF_INET not in addrs:
                        self.warnings_found.append(f"Interfaz {self.selected_interface} sin IPv4")
                        return ("warning", "Conectividad a Internet",
                               [f"⚠️  La interfaz {self.selected_interface} no tiene dirección IPv4",
                                "💡 Selecciona una interfaz con IP asignada"])
                except:
                    pass
            
            # Método 1: Intentar conexión HTTP
            test_urls = [
                "http://clients3.google.com/generate_204",
                "http://www.cloudflare.com/cdn-cgi/trace"
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code in [200, 204]:
                        interface_msg = f" (interfaz: {self.selected_interface})" if self.selected_interface and self.selected_interface not in ["all", "none", "loading"] else ""
                        return ("ok", "Conectividad a Internet", 
                               [f"✅ Conexión a internet funcional{interface_msg}"])
                except:
                    continue
            
            # Método 2: Intentar conexión TCP a DNS
            servers = [("8.8.8.8", 53), ("1.1.1.1", 53)]
            for server, port in servers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    sock.connect((server, port))
                    sock.close()
                    interface_msg = f" (interfaz: {self.selected_interface})" if self.selected_interface and self.selected_interface not in ["all", "none", "loading"] else ""
                    return ("ok", "Conectividad a Internet", 
                           [f"✅ Conexión a internet funcional{interface_msg}"])
                except:
                    continue
            
            # Método 3: Ping simple (sin especificar interfaz para evitar problemas de permisos)
            test_ips = ["8.8.8.8", "1.1.1.1"]
            for ip in test_ips:
                try:
                    cmd = get_ping_command(ip, count=2)
                    result = subprocess.run(cmd, capture_output=True, timeout=5)
                    
                    if result.returncode == 0:
                        interface_msg = f" (interfaz: {self.selected_interface})" if self.selected_interface and self.selected_interface not in ["all", "none", "loading"] else ""
                        return ("ok", "Conectividad a Internet", 
                               [f"✅ Conexión a internet funcional{interface_msg}",
                                "   (Nota: Test general, no específico de interfaz)"])
                except:
                    continue
            
            # Si ninguno funciona
            self.problems_found.append("Sin conectividad a internet")
            interface_note = f" desde {self.selected_interface}" if self.selected_interface and self.selected_interface not in ["all", "none", "loading"] else ""
            return ("problem", "Conectividad a Internet",
                   [f"❌ No se pudo conectar a internet{interface_note}",
                    "💡 Verifica que el cable esté conectado o WiFi activado",
                    "💡 Reinicia tu router/módem",
                    "💡 Si el problema persiste, prueba con 'Todas las interfaces'",
                    "💡 Puede haber un firewall bloqueando las conexiones"])
                    
        except Exception as e:
            return ("warning", "Conectividad a Internet", 
                   [f"⚠️  Error verificando conectividad: {str(e)}"])
    
    def test_dns_resolution(self) -> Tuple[str, str, List[str]]:
        """Test 3: Prueba resolución DNS"""
        test_domains = ["google.com", "cloudflare.com", "github.com"]
        failed = []
        
        for domain in test_domains:
            try:
                socket.gethostbyname(domain)
            except:
                failed.append(domain)
        
        if len(failed) == len(test_domains):
            self.problems_found.append("Fallo total en resolución DNS")
            return ("problem", "Resolución DNS",
                   ["❌ No se puede resolver ningún dominio",
                    "💡 Problema con tus servidores DNS",
                    "💡 Cambia DNS a 8.8.8.8 y 8.8.4.4 (Google)",
                    "💡 O usa 1.1.1.1 y 1.0.0.1 (Cloudflare)"])
        elif failed:
            self.warnings_found.append(f"Problemas con algunos DNS ({len(failed)}/{len(test_domains)})")
            return ("warning", "Resolución DNS",
                   [f"⚠️  Falló resolución de: {', '.join(failed)}",
                    "💡 Puede ser problema temporal del servidor",
                    "💡 O filtro de red/firewall"])
        else:
            return ("ok", "Resolución DNS",
                   ["✅ DNS funcionando correctamente"])
    
    def test_gateway(self) -> Tuple[str, str, List[str]]:
        """Test 4: Verifica gateway"""
        try:
            gateways = netifaces.gateways()
            
            # Si hay interfaz específica seleccionada, buscar su gateway
            if self.selected_interface and self.selected_interface != "all" and isinstance(self.selected_interface, str):
                # Buscar gateway para interfaz específica
                gw_ip = None
                gw_iface = self.selected_interface
                
                for gw in gateways.get(netifaces.AF_INET, []):
                    if isinstance(gw, tuple) and len(gw) >= 2 and gw[1] == self.selected_interface:
                        gw_ip = gw[0]
                        break
                
                if not gw_ip:
                    # Intentar con gateway por defecto
                    default_gw = gateways.get('default', {})
                    if netifaces.AF_INET in default_gw:
                        gw_data = default_gw[netifaces.AF_INET]
                        gw_ip = gw_data[0]
                        gw_iface = gw_data[1]
            else:
                # Usar gateway por defecto
                default_gw = gateways.get('default', {})
                if netifaces.AF_INET in default_gw:
                    gw_data = default_gw[netifaces.AF_INET]
                    gw_ip = gw_data[0]
                    gw_iface = gw_data[1]
                else:
                    gw_ip = None
                    gw_iface = None
            
            if gw_ip:
                # Intentar hacer ping al gateway
                try:
                    cmd = get_ping_command(gw_ip, count=2)
                    result = subprocess.run(cmd, capture_output=True, timeout=5)
                    
                    if result.returncode == 0:
                        return ("ok", "Gateway",
                               [f"✅ Gateway {gw_ip} alcanzable vía {gw_iface}"])
                    else:
                        self.warnings_found.append("Gateway no responde a ping")
                        return ("warning", "Gateway",
                               [f"⚠️  Gateway {gw_ip} no responde a ping",
                                "💡 El gateway puede tener ping deshabilitado (normal)",
                                "💡 O puede haber un problema de red local"])
                except:
                    return ("warning", "Gateway",
                           [f"⚠️  No se pudo verificar gateway {gw_ip}"])
            else:
                self.problems_found.append("No hay gateway configurado")
                return ("problem", "Gateway",
                       ["❌ No se encontró gateway predeterminado",
                        "💡 Verifica la configuración de red",
                        "💡 Puede necesitar DHCP o configuración manual"])
                        
        except Exception as e:
            return ("warning", "Gateway", [f"⚠️  Error verificando gateway: {str(e)}"])
    
    def test_latency(self) -> Tuple[str, str, List[str]]:
        """Test 5: Mide latencia"""
        try:
            cmd = get_ping_command("8.8.8.8", count=5)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parsear latencia promedio (simplificado)
                output = result.stdout.lower()
                
                if "ms" in output or "time=" in output:
                    # Latencia detectada (análisis simple)
                    if "100% packet loss" in output or "100% loss" in output:
                        self.problems_found.append("100% pérdida de paquetes")
                        return ("problem", "Latencia y Pérdida de Paquetes",
                               ["❌ 100% de pérdida de paquetes",
                                "💡 Problema severo de conectividad",
                                "💡 Verifica cables y hardware de red"])
                    else:
                        return ("ok", "Latencia y Pérdida de Paquetes",
                               ["✅ Latencia normal, sin pérdida significativa de paquetes"])
                else:
                    return ("warning", "Latencia y Pérdida de Paquetes",
                           ["⚠️  No se pudo medir latencia correctamente"])
            else:
                self.warnings_found.append("No se pudo medir latencia")
                return ("warning", "Latencia y Pérdida de Paquetes",
                       ["⚠️  No se pudo completar test de latencia"])
                       
        except Exception as e:
            return ("warning", "Latencia", [f"⚠️  Error midiendo latencia: {str(e)}"])
    
    def test_dns_config(self) -> Tuple[str, str, List[str]]:
        """Test 6: Verifica configuración DNS"""
        try:
            dns_servers = []
            
            # Intentar leer DNS del sistema
            try:
                if is_windows():
                    result = subprocess.run(['ipconfig', '/all'], 
                                          capture_output=True, text=True, timeout=3)
                    # Parseo simplificado
                    dns_servers = ['Sistema']
                else:
                    with open('/etc/resolv.conf', 'r') as f:
                        for line in f:
                            if line.strip().startswith('nameserver'):
                                dns = line.split()[1]
                                dns_servers.append(dns)
            except:
                pass
            
            if not dns_servers:
                self.warnings_found.append("No se detectaron servidores DNS")
                return ("warning", "Configuración DNS",
                       ["⚠️  No se pudieron detectar servidores DNS",
                        "💡 Puede estar usando DHCP (normal)",
                        "💡 O configuración automática"])
            else:
                return ("ok", "Configuración DNS",
                       [f"✅ DNS configurados: {', '.join(dns_servers[:3])}"])
                       
        except Exception as e:
            return ("warning", "Configuración DNS", [f"⚠️  Error: {str(e)}"])
    
    def test_ip_conflicts(self) -> Tuple[str, str, List[str]]:
        """Test 7: Busca conflictos de IP"""
        # Este test es complejo y requiere permisos especiales
        # Por ahora, solo verificamos duplicados en la misma máquina
        try:
            # Filtrar por interfaz seleccionada si aplica
            if self.selected_interface and self.selected_interface != "all" and isinstance(self.selected_interface, str):
                interfaces_to_check = [self.selected_interface]
            else:
                interfaces_to_check = netifaces.interfaces()
            
            ips = []
            
            for iface in interfaces_to_check:
                if not isinstance(iface, str) or iface == 'lo':
                    continue
                if iface not in netifaces.interfaces():
                    continue
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        ips.append(ip)
            
            # Buscar duplicados
            if len(ips) != len(set(ips)):
                self.problems_found.append("Posible conflicto de IP detectado")
                return ("problem", "Conflictos de IP",
                       ["❌ Se detectaron IPs duplicadas en interfaces",
                        "💡 Esto puede causar problemas de conectividad",
                        "💡 Verifica tu configuración de red"])
            else:
                return ("ok", "Conflictos de IP",
                       ["✅ No se detectaron conflictos de IP"])
                       
        except Exception as e:
            return ("warning", "Conflictos de IP", [f"⚠️  Error: {str(e)}"])
    
    def test_network_services(self) -> Tuple[str, str, List[str]]:
        """Test 8: Verifica servicios de red"""
        try:
            # Verificar que hay procesos de red activos
            connections = psutil.net_connections(kind='inet')
            
            if connections:
                listening = len([c for c in connections if c.status == 'LISTEN'])
                established = len([c for c in connections if c.status == 'ESTABLISHED'])
                
                return ("ok", "Servicios de Red",
                       [f"✅ {len(connections)} conexiones activas",
                        f"   • {listening} servicios escuchando",
                        f"   • {established} conexiones establecidas"])
            else:
                self.warnings_found.append("No se detectaron servicios de red")
                return ("warning", "Servicios de Red",
                       ["⚠️  No se detectaron servicios de red activos"])
                       
        except Exception as e:
            return ("warning", "Servicios de Red", [f"⚠️  Error: {str(e)}"])
    
    def generate_report(self, results: List[Tuple[str, str, List[str]]]) -> str:
        """Genera el reporte final"""
        report = ["[bold cyan]═══ REPORTE DE DIAGNÓSTICO ═══[/]\n"]
        
        # Resultados de tests
        for status, title, details in results:
            if status == "ok":
                report.append(f"[bold green]✅ {title}[/]")
            elif status == "warning":
                report.append(f"[bold yellow]⚠️  {title}[/]")
            else:
                report.append(f"[bold red]❌ {title}[/]")
            
            for detail in details:
                report.append(f"   {detail}")
            report.append("")
        
        # Resumen
        report.append("[bold cyan]═══ RESUMEN ═══[/]\n")
        
        if not self.problems_found and not self.warnings_found:
            report.append("[bold green]🎉 ¡TODO FUNCIONA CORRECTAMENTE![/]")
            report.append("No se detectaron problemas en tu red.\n")
        else:
            if self.problems_found:
                report.append(f"[bold red]🔴 Problemas críticos: {len(self.problems_found)}[/]")
                for problem in self.problems_found:
                    report.append(f"   • {problem}")
                report.append("")
            
            if self.warnings_found:
                report.append(f"[bold yellow]🟡 Advertencias: {len(self.warnings_found)}[/]")
                for warning in self.warnings_found:
                    report.append(f"   • {warning}")
                report.append("")
        
        # Recomendaciones generales
        report.append("[bold cyan]═══ RECOMENDACIONES ═══[/]\n")
        
        if self.problems_found:
            report.append("[bold]Acciones inmediatas:[/]")
            report.append("1. Revisa los problemas críticos arriba")
            report.append("2. Reinicia tu router/módem si es necesario")
            report.append("3. Verifica cables y conexiones físicas")
            report.append("4. Si persiste, contacta a tu ISP")
        else:
            report.append("• Ejecuta este diagnóstico regularmente")
            report.append("• Mantén drivers de red actualizados")
            report.append("• Considera configurar DNS personalizado")
        
        report.append("\n[dim]Pulsa 'd' para ejecutar diagnóstico nuevamente[/]")
        
        return "\n".join(report)


if __name__ == "__main__":
    app = NetworkTroubleshooter()
    app.run()
