"""
Monitor de Latencia Geográfica
Prueba latencia a servidores en diferentes regiones del mundo
"""
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, DataTable
from textual.binding import Binding
import subprocess
import re
import time
from typing import Dict, List, Tuple, Optional, Any
from platform_utils import get_ping_command

class GeoLatencyMonitor(App):
    """Aplicación para monitorear latencia a diferentes regiones geográficas"""
    
    TITLE = "🌍 Monitor de Latencia Geográfica"
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
        padding: 1 2;
    }
    
    #info-section {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    #table-container {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    DataTable {
        height: 100%;
    }
    
    #controls {
        height: auto;
        padding: 1;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    
    #status {
        padding: 1;
        text-align: center;
        background: $primary 20%;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("t", "test_all", "Test Completo"),
        Binding("r", "refresh", "Actualizar"),
        Binding("b", "best", "Mejor Región"),
    ]
    
    # Servidores de prueba en diferentes regiones
    TEST_SERVERS = {
        "🇺🇸 América del Norte (Este)": "8.8.8.8",  # Google DNS NY
        "🇺🇸 América del Norte (Oeste)": "1.1.1.1",  # Cloudflare SF
        "🇧🇷 América del Sur": "200.160.2.3",  # Brasil (LACNIC)
        "🇬🇧 Europa (Oeste)": "1.0.0.1",  # Cloudflare Londres
        "🇩🇪 Europa (Centro)": "9.9.9.9",  # Quad9 Alemania
        "🇯🇵 Asia (Este)": "129.250.35.250",  # NTT Japón
        "🇸🇬 Asia (Sureste)": "208.67.222.222",  # OpenDNS Singapur
        "🇦🇺 Oceanía": "1.1.1.2",  # Cloudflare Sydney
    }
    
    def __init__(self):
        super().__init__()
        self.results: Dict[str, Dict] = {}
        self.testing = False
        self.region_to_row: Dict[str, int] = {}  # Mapeo región -> índice de fila
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="info-section"):
                yield Static(self.get_info_text(), id="info")
            with Container(id="table-container"):
                yield DataTable(id="results-table")
            yield Static("Listo para comenzar", id="status")
            with Horizontal(id="controls"):
                yield Button("🌍 Test Completo", id="test-btn", variant="primary")
                yield Button("🔄 Actualizar", id="refresh-btn", variant="default")
                yield Button("🏆 Mejor Región", id="best-btn", variant="success")
        yield Footer()
    
    def on_mount(self) -> None:
        """Al montar la aplicación"""
        table = self.query_one("#results-table", DataTable)
        table.add_columns("Región", "IP", "Latencia (ms)", "Estado", "Calidad")
        table.cursor_type = "row"
        
        # Inicializar tabla con servidores y guardar índice
        row_idx = 0
        for region, ip in self.TEST_SERVERS.items():
            table.add_row(region, ip, "—", "Pendiente", "—")
            self.region_to_row[region] = row_idx
            row_idx += 1
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clics en botones"""
        if event.button.id == "test-btn":
            self.test_all_regions()
        elif event.button.id == "refresh-btn":
            self.action_refresh()
        elif event.button.id == "best-btn":
            self.show_best_region()
    
    def action_test_all(self) -> None:
        """Ejecutar test completo"""
        self.test_all_regions()
    
    def action_refresh(self) -> None:
        """Actualizar resultados"""
        self.test_all_regions()
    
    def action_best(self) -> None:
        """Mostrar mejor región"""
        self.show_best_region()
    
    def get_info_text(self) -> str:
        """Texto informativo"""
        return """[bold cyan]Monitor de Latencia Geográfica[/]

Prueba tu latencia a servidores en diferentes regiones del mundo.
Útil para: gaming, remote work, elegir servidores VPN, diagnóstico de red.

[bold yellow]Cómo usar:[/]
• Presiona 't' o el botón "Test Completo" para iniciar
• Presiona 'b' o el botón "Mejor Región" para ver estadísticas
• Presiona 'q' para salir

[bold yellow]Interpretación:[/]
• [green]< 50ms[/]: Excelente
• [yellow]50-100ms[/]: Buena
• [red]100-200ms[/]: Regular
• [red]> 200ms[/]: Mala"""
    
    def test_all_regions(self) -> None:
        """Prueba todas las regiones"""
        if self.testing:
            return
        
        self.testing = True
        self.results.clear()
        
        status = self.query_one("#status", Static)
        table = self.query_one("#results-table", DataTable)
        
        for region, ip in self.TEST_SERVERS.items():
            status.update(f"[cyan]Probando:[/] {region}...")
            self.refresh()  # Forzar actualización de la UI
            
            # Realizar ping
            latency, packet_loss = self.ping_server(ip)
            
            # Calcular estado y calidad
            if latency is None:
                state = "[red]Error[/]"
                quality = "—"
                quality_text = "Sin respuesta"
            else:
                if packet_loss > 50:
                    state = "[red]Inestable[/]"
                elif packet_loss > 0:
                    state = "[yellow]Pérdida[/]"
                else:
                    state = "[green]OK[/]"
                
                # Determinar calidad
                if latency < 50:
                    quality = "[green]⭐⭐⭐⭐⭐[/]"
                    quality_text = "Excelente"
                elif latency < 100:
                    quality = "[yellow]⭐⭐⭐⭐[/]"
                    quality_text = "Buena"
                elif latency < 200:
                    quality = "[yellow]⭐⭐⭐[/]"
                    quality_text = "Regular"
                elif latency < 300:
                    quality = "[red]⭐⭐[/]"
                    quality_text = "Mala"
                else:
                    quality = "[red]⭐[/]"
                    quality_text = "Muy Mala"
            
            # Guardar resultados
            self.results[region] = {
                'ip': ip,
                'latency': latency,
                'packet_loss': packet_loss,
                'quality_text': quality_text,
                'state': state,
                'quality': quality
            }
            
            # Regenerar tabla completa con resultados actualizados
            table.clear()
            for r, ip_addr in self.TEST_SERVERS.items():
                if r in self.results:
                    res = self.results[r]
                    lat_str = f"{res['latency']:.1f}" if res['latency'] is not None else "—"
                    table.add_row(r, ip_addr, lat_str, res['state'], res['quality'])
                else:
                    table.add_row(r, ip_addr, "—", "Pendiente", "—")
            
            self.refresh()  # Forzar actualización de la UI después de cada test
            
            time.sleep(0.1)  # Pequeña pausa entre tests
        
        status.update("[green]✅ Test completado[/]")
        self.refresh()  # Actualizar estado final
        self.testing = False
    
    def ping_server(self, ip: str, count: int = 4) -> Tuple[Optional[float], float]:
        """
        Hace ping a un servidor y devuelve (latencia_promedio, pérdida_paquetes)
        """
        try:
            cmd = get_ping_command(ip, count=count)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return None, 100.0
            
            output = result.stdout
            
            # Parsear latencia (buscar patrones comunes)
            latency = None
            packet_loss = 0.0
            
            # Patrón para Windows: "Average = XXXms"
            avg_match = re.search(r'Average\s*=\s*(\d+)ms', output)
            if avg_match:
                latency = float(avg_match.group(1))
            
            # Patrón para Linux/Mac: "rtt min/avg/max/mdev = x/x/x/x ms"
            rtt_match = re.search(r'rtt\s+min/avg/max/mdev\s+=\s+[\d.]+/([\d.]+)', output)
            if rtt_match:
                latency = float(rtt_match.group(1))
            
            # Si no se encontró con los patrones anteriores, buscar "time=" en cada línea
            if latency is None:
                times = re.findall(r'time[<=]\s*([\d.]+)\s*ms', output, re.IGNORECASE)
                if times:
                    latency = sum(float(t) for t in times) / len(times)
            
            # Parsear pérdida de paquetes
            loss_match = re.search(r'(\d+)%\s+(?:packet\s+)?loss', output, re.IGNORECASE)
            if loss_match:
                packet_loss = float(loss_match.group(1))
            
            return latency, packet_loss
            
        except subprocess.TimeoutExpired:
            return None, 100.0
        except Exception as e:
            return None, 100.0
    
    def show_best_region(self) -> None:
        """Muestra la mejor región"""
        if not self.results:
            status = self.query_one("#status", Static)
            status.update("[yellow]⚠️  Ejecuta el test primero[/]")
            return
        
        # Filtrar regiones con latencia válida
        valid_results = {
            region: data for region, data in self.results.items()
            if data['latency'] is not None
        }
        
        if not valid_results:
            status = self.query_one("#status", Static)
            status.update("[red]❌ No hay resultados válidos[/]")
            return
        
        # Encontrar la mejor región
        best_region = min(valid_results.items(), key=lambda x: x[1]['latency'])
        worst_region = max(valid_results.items(), key=lambda x: x[1]['latency'])
        
        region_name, data = best_region
        worst_name, worst_data = worst_region
        
        # Calcular promedio
        avg_latency = sum(d['latency'] for d in valid_results.values()) / len(valid_results)
        
        # Mostrar resumen
        info = self.query_one("#info", Static)
        summary = f"""[bold cyan]═══ RESUMEN DE RESULTADOS ═══[/]

[bold green]🏆 Mejor región:[/] {region_name}
   • Latencia: {data['latency']:.1f} ms
   • Calidad: {data['quality_text']}
   • IP: {data['ip']}

[bold red]🐌 Peor región:[/] {worst_name}
   • Latencia: {worst_data['latency']:.1f} ms
   • Calidad: {worst_data['quality_text']}
   • IP: {worst_data['ip']}

[bold yellow]📊 Estadísticas:[/]
   • Latencia promedio: {avg_latency:.1f} ms
   • Regiones probadas: {len(valid_results)}/{len(self.TEST_SERVERS)}
   • Diferencia mejor/peor: {worst_data['latency'] - data['latency']:.1f} ms

[bold cyan]💡 Recomendación:[/]
Para mejor rendimiento, usa servicios/servidores en {region_name}"""
        
        info.update(summary)
        
        status = self.query_one("#status", Static)
        status.update(f"[green]🏆 Mejor región: {region_name} ({data['latency']:.1f} ms)[/]")


if __name__ == "__main__":
    app = GeoLatencyMonitor()
    app.run()
