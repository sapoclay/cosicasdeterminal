"""
Verificador de Integridad de Archivos (FIM)
Detecta cambios no autorizados en archivos mediante hashing
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label, DirectoryTree, RichLog
from textual.binding import Binding
import hashlib
import os
import json
import datetime
import threading

class FileIntegrityMonitorApp(App):
    """Aplicación de FIM"""
    
    TITLE = "🛡️ Verificador de Integridad (FIM)"
    CSS = """
    Screen {
        background: $surface;
    }
    
    #left-pane {
        width: 40%;
        height: 100%;
        border-right: solid $primary;
    }
    
    #right-pane {
        width: 60%;
        height: 100%;
        padding: 1;
    }
    
    DirectoryTree {
        height: 70%;
        background: $surface;
    }
    
    RichLog {
        height: 1fr;
        border: solid $primary;
        background: $surface;
    }
    
    .controls {
        height: auto;
        margin: 1 0;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
    ]
    
    DB_FILE = ".fim_db.json"
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            with Vertical(id="left-pane"):
                yield Label("📂 Selecciona Carpeta a Monitorizar")
                yield DirectoryTree("/")
                
                with Vertical(classes="controls"):
                    yield Label("Carpeta Seleccionada:")
                    yield Input(id="selected-path", read_only=True)
                    yield Button("📸 Crear Línea Base (Baseline)", id="btn-baseline", variant="primary")
                    yield Button("🔍 Verificar Integridad", id="btn-verify", variant="warning")
            
            with Vertical(id="right-pane"):
                yield Label("📝 Registro de Eventos")
                yield RichLog(highlight=True, markup=True, id="log-output")
        
        yield Footer()
        
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.query_one("#selected-path", Input).value = str(event.path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        path = self.query_one("#selected-path", Input).value
        if not path:
            self.notify("Selecciona una carpeta primero", severity="warning")
            return
            
        if event.button.id == "btn-baseline":
            self.run_worker(lambda: self.create_baseline(path), thread=True)
        elif event.button.id == "btn-verify":
            self.run_worker(lambda: self.verify_integrity(path), thread=True)

    def calculate_hash(self, filepath):
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            return None

    def create_baseline(self, path):
        self.log_msg(f"[bold blue]Iniciando creación de línea base para: {path}[/]")
        
        file_hashes = {}
        count = 0
        
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    filepath = os.path.join(root, file)
                    # Skip our own DB file if it's in the path
                    if self.DB_FILE in filepath: continue
                    
                    file_hash = self.calculate_hash(filepath)
                    if file_hash:
                        file_hashes[filepath] = file_hash
                        count += 1
                        if count % 10 == 0:
                            self.app.call_from_thread(self.log_msg, f"Procesados {count} archivos...")
            
            # Save DB
            db_path = os.path.join(path, self.DB_FILE)
            with open(db_path, 'w') as f:
                json.dump(file_hashes, f, indent=4)
                
            self.app.call_from_thread(self.log_msg, f"[bold green]✅ Línea base creada con éxito. {count} archivos indexados.[/]")
            self.app.call_from_thread(self.notify, "Línea base creada")
            
        except Exception as e:
            self.app.call_from_thread(self.log_msg, f"[bold red]Error creando línea base: {e}[/]")

    def verify_integrity(self, path):
        self.log_msg(f"[bold yellow]Iniciando verificación de integridad para: {path}[/]")
        
        db_path = os.path.join(path, self.DB_FILE)
        if not os.path.exists(db_path):
            self.app.call_from_thread(self.notify, "No existe línea base. Crea una primero.", severity="error")
            self.app.call_from_thread(self.log_msg, "[red]Error: No se encontró archivo de base de datos (.fim_db.json)[/]")
            return
            
        try:
            with open(db_path, 'r') as f:
                stored_hashes = json.load(f)
                
            current_files = set()
            changes_found = False
            
            # Check for modifications and new files
            for root, dirs, files in os.walk(path):
                for file in files:
                    filepath = os.path.join(root, file)
                    if self.DB_FILE in filepath: continue
                    
                    current_files.add(filepath)
                    current_hash = self.calculate_hash(filepath)
                    
                    if filepath not in stored_hashes:
                        self.app.call_from_thread(self.log_msg, f"[bold red]🚨 NUEVO ARCHIVO DETECTADO: {filepath}[/]")
                        changes_found = True
                    elif stored_hashes[filepath] != current_hash:
                        self.app.call_from_thread(self.log_msg, f"[bold red]🚨 ARCHIVO MODIFICADO: {filepath}[/]")
                        changes_found = True
            
            # Check for deleted files
            for filepath in stored_hashes:
                if filepath not in current_files:
                    self.app.call_from_thread(self.log_msg, f"[bold red]🚨 ARCHIVO ELIMINADO: {filepath}[/]")
                    changes_found = True
            
            if not changes_found:
                self.app.call_from_thread(self.log_msg, f"[bold green]✅ Verificación completada. Sistema INTEGRO (Sin cambios).[/]")
            else:
                self.app.call_from_thread(self.log_msg, f"[bold red]⚠️ Verificación completada. SE DETECTARON CAMBIOS.[/]")
                
        except Exception as e:
            self.app.call_from_thread(self.log_msg, f"[bold red]Error en verificación: {e}[/]")

    def log_msg(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.query_one("#log-output", RichLog).write(f"[dim]{timestamp}[/] {msg}")

def main():
    app = FileIntegrityMonitorApp()
    app.run()

if __name__ == "__main__":
    main()
