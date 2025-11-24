from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, DataTable, DirectoryTree, Label, Static
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
import re
import os

class LogAnalyzerApp(App):
    """Herramienta de análisis de logs para detectar patrones de ataque"""
    
    TITLE = "🛡️ Analizador de Logs (Mini-SIEM)"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #tree-view {
        width: 30%;
        height: 100%;
        dock: left;
        border-right: solid $primary;
        background: $panel;
    }
    
    #right-pane {
        width: 70%;
        height: 100%;
        padding: 1;
    }
    
    #data-table {
        height: 1fr;
        border: solid $secondary;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
        margin-bottom: 1;
    }
    
    .info-box {
        height: auto;
        padding: 1;
        background: $surface-lighten-1;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Container(
            DirectoryTree("/", id="tree-view"),
            Vertical(
                Static("🛡️ Analizador de Logs (Mini-SIEM)", classes="title"),
                Static("Selecciona un archivo de log en el panel izquierdo para analizarlo en busca de amenazas.", classes="info-box", id="status-msg"),
                DataTable(id="data-table", zebra_stripes=True),
                id="right-pane"
            ),
        )
        
        yield Footer()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Línea", "Tipo de Amenaza", "Contenido Detectado")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        self.analyze_file(event.path)

    def analyze_file(self, path):
        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#status-msg", Static)
        
        status.update(f"⏳ Analizando: {os.path.basename(path)}...")
        
        patterns = {
            "SQL Injection": r"(UNION SELECT|OR '1'='1|--|#|\/\*|\*\/|WAITFOR DELAY|SLEEP\()",
            "XSS": r"(<script>|javascript:|onerror=|onload=|alert\()",
            "Path Traversal": r"(\.\./|\.\.\\|/etc/passwd|c:\\windows|boot\.ini)",
            "Command Injection": r"(;|\||&&|\$\(|`|eval\()",
            "Brute Force": r"(Failed password|Invalid user|Authentication failure|Login failed)",
            "Sensitive Info": r"(API_KEY|password=|passwd=|secret=|token=)",
        }
        
        count = 0
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line: continue
                    
                    found = False
                    for threat_type, pattern in patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            # Truncate long lines
                            content = (line[:97] + '...') if len(line) > 100 else line
                            table.add_row(str(i), threat_type, content)
                            count += 1
                            found = True
                            # Don't break, a line might have multiple threats
            
            if count == 0:
                status.update(f"✅ Análisis completado: {os.path.basename(path)}\nNo se encontraron amenazas obvias.")
            else:
                status.update(f"⚠️ Análisis completado: {os.path.basename(path)}\nSe detectaron {count} posibles amenazas.")
            
        except Exception as e:
            self.notify(f"Error al leer archivo: {e}", severity="error")
            status.update(f"❌ Error: {e}")

if __name__ == "__main__":
    LogAnalyzerApp().run()
