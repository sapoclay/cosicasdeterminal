from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, ProgressBar
from textual.binding import Binding
import socket
import requests
import json
from concurrent.futures import ThreadPoolExecutor
import time

class VulnPortScannerApp(App):
    """Analizador de puertos con detección de vulnerabilidades"""
    
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
    
    #input-host {
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
    
    # Puertos comunes con información de vulnerabilidades .. los más conocidos
    COMMON_PORTS = {
        21: {"service": "FTP", "risk": "HIGH", "reason": "Protocolo sin cifrado, contraseñas en texto plano"},
        22: {"service": "SSH", "risk": "MEDIUM", "reason": "Seguro si está actualizado, vulnerable a fuerza bruta"},
        23: {"service": "Telnet", "risk": "CRITICAL", "reason": "Protocolo obsoleto sin cifrado, NUNCA debería estar expuesto"},
        25: {"service": "SMTP", "risk": "MEDIUM", "reason": "Puede ser usado para spam o phishing si no está configurado"},
        53: {"service": "DNS", "risk": "MEDIUM", "reason": "Puede ser abusado para amplificación DDoS"},
        80: {"service": "HTTP", "risk": "MEDIUM", "reason": "Sin cifrado, datos transmitidos en texto plano"},
        110: {"service": "POP3", "risk": "HIGH", "reason": "Sin cifrado, contraseñas en texto plano"},
        143: {"service": "IMAP", "risk": "HIGH", "reason": "Sin cifrado, contraseñas en texto plano"},
        443: {"service": "HTTPS", "risk": "LOW", "reason": "Seguro si usa TLS actualizado"},
        445: {"service": "SMB", "risk": "HIGH", "reason": "Vulnerable a EternalBlue y otros exploits"},
        3306: {"service": "MySQL", "risk": "HIGH", "reason": "Base de datos no debería estar expuesta públicamente"},
        3389: {"service": "RDP", "risk": "HIGH", "reason": "Vulnerable a BlueKeep y ataques de fuerza bruta"},
        5432: {"service": "PostgreSQL", "risk": "HIGH", "reason": "Base de datos no debería estar expuesta públicamente"},
        5900: {"service": "VNC", "risk": "HIGH", "reason": "Cifrado débil, vulnerable a ataques"},
        6379: {"service": "Redis", "risk": "HIGH", "reason": "Sin autenticación por defecto, RCE posible"},
        8080: {"service": "HTTP-Proxy", "risk": "MEDIUM", "reason": "Panel de administración expuesto"},
        8443: {"service": "HTTPS-Alt", "risk": "LOW", "reason": "Alternativa segura a puerto 443"},
        27017: {"service": "MongoDB", "risk": "CRITICAL", "reason": "Frecuentemente sin autenticación, datos expuestos"},
    }

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Static("🛡️ ANALIZADOR DE VULNERABILIDADES DE PUERTOS", id="title")
            yield Static("Escanea puertos comunes y detecta configuraciones inseguras", classes="description")
            
            yield Static(
                "[yellow]⚠️ ADVERTENCIA:[/] Escanear sistemas sin autorización parece ser ilegal.\n"
                "Usa esta herramienta solo en tus propios sistemas o con permiso explícito.",
                classes="warning-box"
            )
            
            with Horizontal(id="input-container"):
                yield Input(placeholder="IP o dominio (ej: 192.168.1.1 o ejemplo.com)", id="input-host")
                yield Button("🔍 Escanear", variant="primary", id="btn-scan")
            
            with Container(id="progress-container"):
                yield Static("Esperando objetivo...", id="scan-status")
                yield ProgressBar(total=100, show_eta=False, id="scan-progress")
            
            with VerticalScroll(id="results-container"):
                yield Static("Escribe una IP o dominio para comenzar el análisis de seguridad...", id="scan-results")
                
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-scan":
            self.scan_ports()

    def scan_ports(self):
        host = self.query_one("#input-host", Input).value.strip()
        if not host:
            self.query_one("#scan-results", Static).update("[red]❌ Por favor escribe una IP o dominio válido[/]")
            return
        
        # Resolver el host
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            self.query_one("#scan-results", Static).update(f"[red]❌ No se pudo resolver el host: {host}[/]")
            return
        
        status_widget = self.query_one("#scan-status", Static)
        progress_bar = self.query_one("#scan-progress", ProgressBar)
        results_widget = self.query_one("#scan-results", Static)
        
        status_widget.update(f"🔍 Escaneando {host} ({ip})...")
        results_widget.update("[cyan]Iniciando escaneo de seguridad...[/]")
        
        # Escanear puertos
        ports_to_scan = list(self.COMMON_PORTS.keys())
        total_ports = len(ports_to_scan)
        progress_bar.update(total=total_ports, progress=0)
        
        open_ports = []
        
        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip, port))
                sock.close()
                return port if result == 0 else None
            except:
                return None
        
        # Escanear en paralelo
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(check_port, port): port for port in ports_to_scan}
            completed = 0
            
            for future in futures:
                result = future.result()
                if result:
                    open_ports.append(result)
                completed += 1
                progress_bar.update(progress=completed)
                status_widget.update(f"🔍 Escaneando {host} ({ip})... {completed}/{total_ports} puertos verificados")
        
        # Generar reporte
        if not open_ports:
            results_widget.update(f"""
[bold green]✅ ESCANEO COMPLETADO - SIN PUERTOS ABIERTOS[/]

Host: [cyan]{host}[/] ({ip})
Puertos escaneados: {total_ports}
Puertos abiertos: [bold green]0[/]

[dim]No se encontraron puertos comunes abiertos. Esto es generalmente una buena señal de seguridad.[/]
[dim]Nota: Este escaneo solo verifica puertos comunes. Un escaneo completo requeriría más tiempo.[/]
            """)
        else:
            # Calcular nivel de riesgo general
            risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for port in open_ports:
                risk = self.COMMON_PORTS[port]["risk"]
                risk_counts[risk] += 1
            
            # Determinar color general
            if risk_counts["CRITICAL"] > 0:
                overall_color = "red"
                overall_icon = "🔴"
                overall_risk = "CRÍTICO"
            elif risk_counts["HIGH"] > 0:
                overall_color = "yellow"
                overall_icon = "🟠"
                overall_risk = "ALTO"
            elif risk_counts["MEDIUM"] > 0:
                overall_color = "yellow"
                overall_icon = "🟡"
                overall_risk = "MEDIO"
            else:
                overall_color = "green"
                overall_icon = "🟢"
                overall_risk = "BAJO"
            
            output = f"""
[bold {overall_color}]{overall_icon} ESCANEO COMPLETADO - RIESGO {overall_risk}[/]

Host: [cyan]{host}[/] ({ip})
Puertos escaneados: {total_ports}
Puertos abiertos: [bold]{len(open_ports)}[/]

[bold underline]Resumen de Riesgos:[/]
• Críticos: [{risk_counts['CRITICAL']}] puertos
• Altos: [{risk_counts['HIGH']}] puertos
• Medios: [{risk_counts['MEDIUM']}] puertos
• Bajos: [{risk_counts['LOW']}] puertos

[bold underline]Detalles de puertos abiertos:[/]

"""
            
            # Ordenar por nivel de riesgo
            risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            sorted_ports = sorted(open_ports, key=lambda p: risk_order[self.COMMON_PORTS[p]["risk"]])
            
            for port in sorted_ports:
                info = self.COMMON_PORTS[port]
                
                if info["risk"] == "CRITICAL":
                    risk_color = "red"
                    risk_icon = "🔴"
                elif info["risk"] == "HIGH":
                    risk_color = "red"
                    risk_icon = "🟠"
                elif info["risk"] == "MEDIUM":
                    risk_color = "yellow"
                    risk_icon = "🟡"
                else:
                    risk_color = "green"
                    risk_icon = "🟢"
                
                output += f"""
[bold]Puerto {port}/TCP[/] - [{risk_color}]{risk_icon} {info['risk']}[/]
  Servicio: [cyan]{info['service']}[/]
  Riesgo: {info['reason']}

"""
            
            # Recomendaciones
            output += """
[bold red]🔒 RECOMENDACIONES DE SEGURIDAD:[/]

"""
            if risk_counts["CRITICAL"] > 0:
                output += "🔴 [bold red]CRÍTICO:[/] Cierra inmediatamente puertos críticos (Telnet, MongoDB sin auth)\n"
            if risk_counts["HIGH"] > 0:
                output += "🟠 [bold yellow]URGENTE:[/] Revisa y asegura puertos de alto riesgo con firewall/VPN\n"
            if risk_counts["MEDIUM"] > 0:
                output += "🟡 [bold yellow]IMPORTANTE:[/] Considera cerrar puertos innecesarios o usar cifrado\n"
            
            output += """
[bold]Mejores prácticas:[/]
• Solo expón puertos absolutamente necesarios
• Usa firewall para restringir acceso por IP
• Implementa VPN para servicios internos
• Mantén software actualizado
• Usa cifrado (TLS/SSL) siempre que sea posible
• Deshabilita servicios no usados

[dim]Escaneo de seguridad básico completado. Para análisis profundo considera usar Nmap.[/]
            """
            
            results_widget.update(output)
        
        status_widget.update(f"✅ Escaneo completado: {len(open_ports)} puertos abiertos encontrados")

if __name__ == "__main__":
    VulnPortScannerApp().run()
