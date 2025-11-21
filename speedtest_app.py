"""
Mide velocidad de subida, bajada, ping y jitter
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Static, ProgressBar
from textual.binding import Binding
import speedtest
from functools import partial
from datetime import datetime


class SpeedtestApp(App):
    """Aplicación de test de velocidad de Internet"""
    
    TITLE = "🚀 Test de Velocidad"
    
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
    
    #controls {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }
    
    .results-section {
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
    }
    
    .metric-card {
        border: solid $primary;
        padding: 1 2;
        height: auto;
        margin: 1;
    }
    
    .metric-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .metric-value {
        text-align: center;
        text-style: bold;
        color: $success;
    }
    
    Button {
        margin: 0 1;
    }
    
    #history-section {
        height: 1fr;
        border: solid $primary;
        padding: 1 2;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("t", "test", "Iniciar Test"),
    ]
    
    def __init__(self):
        super().__init__()
        self.history = []
        self.testing = False
    
    def compose(self) -> ComposeResult:
        """Compone la interfaz de usuario"""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="title-section"):
                yield Static("🚀 TEST DE VELOCIDAD DE INTERNET", classes="title")
            
            with Container(id="controls"):
                yield Button("🚀 Iniciar test", variant="success", id="test-btn")
                yield Button("📊 Ver historial", variant="primary", id="history-btn")
                yield Button("🗑️ Limpiar historial", variant="warning", id="clear-btn")
            
            with Vertical(classes="results-section"):
                yield Static("⏳ Preparando test...", id="status")
                yield ProgressBar(id="progress", show_eta=False)
            
            with Horizontal(classes="results-section"):
                with Vertical(classes="metric-card"):
                    yield Static("📥 DESCARGA", classes="metric-title")
                    yield Static("--- Mbps", id="download-value", classes="metric-value")
                
                with Vertical(classes="metric-card"):
                    yield Static("📤 SUBIDA", classes="metric-title")
                    yield Static("--- Mbps", id="upload-value", classes="metric-value")
                
                with Vertical(classes="metric-card"):
                    yield Static("⏱️ PING", classes="metric-title")
                    yield Static("--- ms", id="ping-value", classes="metric-value")
            
            with Vertical(classes="results-section"):
                yield Static("", id="server-info")
            
            with Vertical(id="history-section"):
                yield Static("Historial de Tests\n\nNo hay tests realizados aún", id="history")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Se ejecuta cuando la aplicación se monta"""
        self.query_one("#progress", ProgressBar).update(total=100, progress=0)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja eventos de botones"""
        if event.button.id == "test-btn":
            self.action_test()
        elif event.button.id == "history-btn":
            self.show_history()
        elif event.button.id == "clear-btn":
            self.clear_history()
    
    def action_test(self) -> None:
        """Inicia el test de velocidad"""
        if self.testing:
            self.notify("Ya hay un test en progreso", severity="warning")
            return
        
        self.testing = True
        self.query_one("#status", Static).update("⏳ Iniciando test de velocidad...")
        self.query_one("#download-value", Static).update("---")
        self.query_one("#upload-value", Static).update("---")
        self.query_one("#ping-value", Static).update("---")
        self.query_one("#server-info", Static).update("")
        
        worker_func = partial(self.run_speedtest)
        self.run_worker(worker_func, thread=True, exclusive=True)
    
    def run_speedtest(self) -> dict:
        """Ejecuta el test de velocidad"""
        try:
            st = speedtest.Speedtest()
            
            # Actualizar progreso
            self.call_from_thread(self.update_progress, 10, "Buscando mejor servidor...")
            st.get_best_server()
            
            self.call_from_thread(self.update_progress, 25, "Servidor encontrado. Midiendo descarga...")
            download_speed = st.download() / 1_000_000  # Convertir a Mbps
            
            self.call_from_thread(self.update_progress, 60, "Midiendo subida...")
            upload_speed = st.upload() / 1_000_000  # Convertir a Mbps
            
            self.call_from_thread(self.update_progress, 90, "Finalizando...")
            
            results = st.results.dict()
            
            result = {
                'download': download_speed,
                'upload': upload_speed,
                'ping': results['ping'],
                'server': results['server'],
                'client': results['client'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.call_from_thread(self.update_progress, 100, "✓ Test completado")
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def update_progress(self, progress: int, status: str) -> None:
        """Actualiza la barra de progreso y el estado"""
        self.query_one("#progress", ProgressBar).update(progress=progress)
        self.query_one("#status", Static).update(status)
    
    def on_worker_state_changed(self, event) -> None:
        """Se ejecuta cuando cambia el estado del worker"""
        if event.state.name == "SUCCESS":
            result = event.worker.result
            if result and 'error' not in result:
                self.display_results(result)
                self.history.append(result)
            else:
                error_msg = result.get('error', 'Error desconocido') if result else 'Error desconocido'
                self.query_one("#status", Static).update(f"[red]Error: {error_msg}[/]")
                self.notify("Error en el test de velocidad", severity="error")
            self.testing = False
        elif event.state.name == "ERROR":
            self.query_one("#status", Static).update("[red]Error al ejecutar test[/]")
            self.notify("Error en el test de velocidad", severity="error")
            self.testing = False
    
    def display_results(self, result: dict) -> None:
        """Muestra los resultados del test"""
        # Actualizar métricas
        self.query_one("#download-value", Static).update(f"{result['download']:.2f} Mbps")
        self.query_one("#upload-value", Static).update(f"{result['upload']:.2f} Mbps")
        self.query_one("#ping-value", Static).update(f"{result['ping']:.1f} ms")
        
        # Información del servidor
        server = result['server']
        client = result['client']
        
        server_info = f"[bold cyan]📡 Información del Test[/]\n\n"
        server_info += f"[bold]Servidor:[/]\n"
        server_info += f"  Proveedor: {server['sponsor']}\n"
        server_info += f"  Ubicación: {server['name']}, {server['country']}\n"
        server_info += f"  Distancia: {server['d']:.2f} km\n\n"
        server_info += f"[bold]Cliente:[/]\n"
        server_info += f"  IP: {client['ip']}\n"
        server_info += f"  ISP: {client['isp']}\n"
        server_info += f"  País: {client['country']}\n\n"
        server_info += f"Fecha: {result['timestamp']}\n"
        
        self.query_one("#server-info", Static).update(server_info)
        
        self.notify("✓ Test completado exitosamente", severity="information")
    
    def show_history(self) -> None:
        """Muestra el historial de tests"""
        if not self.history:
            self.notify("No hay historial de tests", severity="warning")
            return
        
        history_text = "[bold cyan]📊 Historial de Tests[/]\n\n"
        
        for i, test in enumerate(reversed(self.history), 1):
            history_text += f"[bold yellow]Test #{len(self.history) - i + 1}[/] - {test['timestamp']}\n"
            history_text += f"  📥 Descarga: {test['download']:.2f} Mbps\n"
            history_text += f"  📤 Subida:   {test['upload']:.2f} Mbps\n"
            history_text += f"  ⏱️  Ping:     {test['ping']:.1f} ms\n"
            history_text += f"  📍 Servidor: {test['server']['name']}\n\n"
        
        # Calcular promedios
        avg_download = sum(t['download'] for t in self.history) / len(self.history)
        avg_upload = sum(t['upload'] for t in self.history) / len(self.history)
        avg_ping = sum(t['ping'] for t in self.history) / len(self.history)
        
        history_text += f"[bold green]📊 Promedios ({len(self.history)} tests):[/]\n"
        history_text += f"  📥 Descarga: {avg_download:.2f} Mbps\n"
        history_text += f"  📤 Subida:   {avg_upload:.2f} Mbps\n"
        history_text += f"  ⏱️  Ping:     {avg_ping:.1f} ms\n"
        
        self.query_one("#history", Static).update(history_text)
        self.notify(f"Mostrando {len(self.history)} tests", severity="information")
    
    def clear_history(self) -> None:
        """Limpia el historial"""
        if not self.history:
            self.notify("El historial ya está vacío", severity="warning")
            return
        
        count = len(self.history)
        self.history.clear()
        self.query_one("#history", Static).update("Historial de tests\n\nNo hay tests realizados aún")
        self.notify(f"Historial limpiado ({count} tests eliminados)", severity="information")


def main():
    """Función principal"""
    app = SpeedtestApp()
    app.run()


if __name__ == "__main__":
    main()
