"""
Visor de Metadatos (Exif Viewer)
Extrae metadatos de imágenes y archivos
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label, DataTable, DirectoryTree
from textual.binding import Binding
from PIL import Image, ExifTags
import os
import datetime

class MetadataViewerApp(App):
    """Aplicación de Visor de Metadatos"""
    
    TITLE = "📷 Visor de Metadatos"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #left-pane {
        width: 30%;
        height: 100%;
        border-right: solid $primary;
    }
    
    #right-pane {
        width: 70%;
        height: 100%;
        padding: 1;
    }
    
    DirectoryTree {
        height: 100%;
        background: $surface;
    }
    
    DataTable {
        height: 1fr;
        border: solid $primary;
    }
    
    #file-info {
        height: auto;
        padding: 1;
        background: $panel;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            with Vertical(id="left-pane"):
                yield Label("📂 Explorador de Archivos")
                # Start at root to allow full navigation
                yield DirectoryTree("/")
            
            with Vertical(id="right-pane"):
                yield Static("Selecciona una imagen para ver sus metadatos", id="file-info")
                yield DataTable(zebra_stripes=True)
        
        yield Footer()
        
    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Etiqueta (Tag)", "Valor")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        file_path = event.path
        self.analyze_file(file_path)

    def analyze_file(self, file_path):
        table = self.query_one(DataTable)
        table.clear()
        
        self.query_one("#file-info", Static).update(f"Analizando: [bold cyan]{file_path}[/]")
        
        try:
            # Basic File Stats
            stats = os.stat(file_path)
            table.add_row("Archivo", os.path.basename(file_path))
            table.add_row("Tamaño", f"{stats.st_size / 1024:.2f} KB")
            table.add_row("Modificado", datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
            
            # Image Analysis
            try:
                img = Image.open(file_path)
                table.add_row("Formato", img.format)
                table.add_row("Modo", img.mode)
                table.add_row("Dimensiones", f"{img.width} x {img.height}")
                
                # Exif Data
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        # Truncate long values
                        str_val = str(value)
                        if len(str_val) > 50: str_val = str_val[:47] + "..."
                        table.add_row(str(tag_name), str_val)
                else:
                    table.add_row("Exif", "No encontrado o no soportado")
                    
            except Exception as e:
                # Not an image or error opening
                table.add_row("Error Imagen", str(e))
                
        except Exception as e:
            self.notify(f"Error accediendo al archivo: {e}", severity="error")

def main():
    app = MetadataViewerApp()
    app.run()

if __name__ == "__main__":
    main()
