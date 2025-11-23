#!/usr/bin/env python3
"""
Permite navegar, buscar y visualizar archivos de log de forma multiplataforma
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Button, Input, Static, Label, DirectoryTree, ListView, ListItem
from textual.binding import Binding
from textual.message import Message
from rich.text import Text
from pathlib import Path
from datetime import datetime
import log_utils
import subprocess
import shutil
import platform
import os


class LogFileList(ListView):
    """Lista personalizada de archivos de log"""
    
    class LoadRequested(Message):
        """Mensaje cuando se solicita cargar un archivo"""
        pass
    
    BINDINGS = [("enter", "select", "Select")]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_files = []
    
    def update_files(self, files: list):
        """Actualiza la lista de archivos"""
        self.clear()
        self.log_files = files
        
        for file_info in files:
            size = log_utils.format_file_size(file_info['size'])
            readable = "✓" if file_info['readable'] else "✗"
            
            # Formatear la fecha de modificación
            try:
                mod_time = datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M')
            except:
                mod_time = "Desconocido"
            
            label = f"{readable} {file_info['name']:<40} {size:>10}  {mod_time}"
            self.append(ListItem(Label(label)))


class LogContentViewer(VerticalScroll):
    """Visor de contenido del log con scroll"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_lines = []
        self.current_file = None
    
    def show_log(self, filepath: Path):
        """Muestra el contenido de un log"""
        self.current_file = filepath
        
        # Limpiar el contenido anterior primero
        self.remove_children()
        
        # Leer el archivo
        lines, truncated = log_utils.read_log_file(filepath, max_lines=2000, tail=True)
        self.current_lines = lines
        
        # Crear texto simple
        content = f"Archivo: {filepath.name}\nRuta: {filepath.parent}\nLíneas: {len(lines)}\n\n"
        for i, line in enumerate(lines, 1):
            content += f"{i:3d}: {line}\n"
        
        if truncated:
            content = f"... (Primeras líneas truncadas)\n{content}"
        
        # Montar
        self.mount(Static(content))


class LogViewerScreen(Screen):
    """Pantalla principal del visor de logs"""
    
    BINDINGS = [
        Binding("q", "quit", "Salir", priority=True),
        Binding("r", "refresh", "Actualizar"),
        Binding("c", "clear_search", "Limpiar búsqueda"),
        ("escape", "volver", "Volver"),
    ]
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #left-panel {
        width: 40%;
        border-right: solid $primary;
        padding: 1;
    }
    
    #right-panel {
        width: 60%;
        padding: 1;
    }
    
    #search-container {
        height: auto;
        padding: 1;
        background: $boost;
        margin-bottom: 1;
    }
    
    #directory-selector {
        height: auto;
        margin-bottom: 1;
    }
    
    LogFileList {
        height: 1fr;
        border: solid $primary;
    }
    
    LogContentViewer {
        height: 1fr;
        border: solid $primary;
        background: $surface;
        overflow-y: scroll;
    }

    LogContentViewer Static {
        width: 100%;
        color: $text;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    Button {
        margin-right: 1;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.current_directory = None
        self.log_files = []
        self.selected_file = None
        self.loading = False
    
    def compose(self) -> ComposeResult:
        """Componer la interfaz"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            # Panel izquierdo: selector de directorio y lista de logs
            with Vertical(id="left-panel"):
                yield Label("📂 Directorio de logs:", id="directory-label")
                
                with Horizontal(id="directory-selector"):
                    yield Button("Seleccionar directorio", id="btn-select-dir", variant="primary")
                    yield Button("Escanear rutas comunes", id="btn-scan-common", variant="success")
                
                yield Label("📋 Archivos de log encontrados:", id="files-label")
                yield LogFileList(id="file-list")
            
            # Panel derecho: búsqueda y contenido
            with Vertical(id="right-panel"):
                with Container(id="search-container"):
                    yield Label("🔍 Buscar en el log:")
                    yield Input(placeholder="Ingrese término de búsqueda...", id="search-input")
                    with Horizontal():
                        yield Button("Buscar", id="btn-search", variant="primary")
                        yield Button("Limpiar", id="btn-clear", variant="warning")
                
                yield Label("📄 Contenido del log:", id="content-label")
                yield LogContentViewer(id="log-content")
        
        yield Static("Seleccione un directorio para comenzar", id="status-bar")
        yield Footer()
    
    def on_mount(self):
        """Al montar la pantalla"""
        self.update_status("💡 Presione 'Escanear rutas comunes' para comenzar | Use ↑↓ para navegar y ENTER para abrir")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clicks en botones"""
        if event.button.id == "btn-scan-common":
            self.scan_common_paths()
        elif event.button.id == "btn-select-dir":
            self.select_custom_directory()
        elif event.button.id == "btn-search":
            self.perform_search()
        elif event.button.id == "btn-clear":
            self.clear_search()
    
    def scan_common_paths(self):
        """Escanear rutas comunes del sistema"""
        self.update_status("Escaneando rutas de logs del sistema...")
        
        log_paths = log_utils.get_platform_log_paths()
        all_logs = []
        
        for path in log_paths:
            logs = log_utils.scan_log_files(path, max_depth=3)
            all_logs.extend(logs)
        
        # Ordenar por fecha de modificación (más recientes primero)
        all_logs.sort(key=lambda x: x['modified'], reverse=True)
        
        self.log_files = all_logs
        file_list = self.query_one("#file-list", LogFileList)
        file_list.update_files(all_logs)
        
        if all_logs:
            file_list.focus()
            self.set_focus(file_list)
        
        self.update_status(f"✅ {len(all_logs)} archivos encontrados | Use ↑↓ para navegar y ENTER para abrir")
    
    def select_custom_directory(self):
        """Permitir seleccionar un directorio personalizado"""
        # Por ahora, usar el directorio actual como demo
        # En una implementación completa, se podría usar un selector de directorios
        current_dir = Path.cwd()
        self.update_status(f"Escaneando {current_dir}...")
        
        logs = log_utils.scan_log_files(current_dir, max_depth=2)
        logs.sort(key=lambda x: x['modified'], reverse=True)
        
        self.log_files = logs
        file_list = self.query_one("#file-list", LogFileList)
        file_list.update_files(logs)
        
        if logs:
            file_list.focus()
            self.set_focus(file_list)
            self.update_status(f"✅ {len(logs)} archivos encontrados en {current_dir.name} | Use ↑↓ y ENTER para abrir")
        else:
            self.update_status(f"✅ {len(logs)} archivos encontrados en {current_dir.name} | Use ↑↓ y ENTER para abrir")
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Cuando se selecciona un archivo de la lista con click o Enter"""
        self._load_file_from_list()
    
    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Cuando se resalta un archivo al navegar con teclas - mostrar preview"""
        file_list = self.query_one("#file-list", LogFileList)
        if event.list_view == file_list and file_list.index is not None:
            index = file_list.index
            if 0 <= index < len(self.log_files):
                selected = self.log_files[index]
                self.update_status(f"📄 {selected['name']} ({log_utils.format_file_size(selected['size'])}) - Presione ENTER para abrir")
    
    def on_log_file_list_load_requested(self, message: LogFileList.LoadRequested) -> None:
        """Cuando se solicita cargar un archivo desde la lista"""
        self._load_file_from_list()
    

    
    def on_key(self, event) -> None:
        """Manejo global de teclas"""
        if event.key == "enter":
            try:
                file_list = self.query_one("#file-list", LogFileList)
                if file_list.has_focus and file_list.index is not None:
                    # Fallback por si la selección de lista no funciona
                    self._load_file_from_list()
            except:
                pass

    def perform_search(self):
        """Realizar búsqueda en el log actual"""
        search_input = self.query_one("#search-input", Input)
        query = search_input.value.strip()
        
        if not query:
            self.update_status("Ingrese un término de búsqueda")
            return
        
        if not self.selected_file:
            self.update_status("Seleccione primero un archivo de log")
            return
        
        # Por ahora, solo mostrar mensaje
        self.update_status(f"Búsqueda: '{query}' (funcionalidad pendiente)")
    
    def clear_search(self):
        """Limpiar la búsqueda y mostrar todo el log"""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        
        if self.selected_file:
            content_viewer = self.query_one("#log-content", LogContentViewer)
            content_viewer.show_log(self.selected_file)
            self.update_status("Búsqueda limpiada")
        else:
            self.update_status("No hay archivo seleccionado")
    
    def action_clear_search(self):
        """Acción de teclado para limpiar búsqueda"""
        self.clear_search()
    
    def action_refresh(self):
        """Refrescar la lista de archivos"""
        if self.log_files:
            self.scan_common_paths()
        else:
            self.update_status("Primero escanee un directorio")
    
    def action_volver(self):
        """Volver al menú principal"""
        self.app.exit()
    
    def action_quit(self):
        """Salir de la aplicación"""
        self.app.exit()
    
    def action_load_selected(self):
        """Cargar el archivo seleccionado"""
        self._load_file_from_list()
    
    def _load_file_from_list(self):
        """Método auxiliar para cargar archivo desde la lista"""
        if self.loading:
            return
            
        file_list = self.query_one("#file-list", LogFileList)
        if file_list.index is not None and 0 <= file_list.index < len(self.log_files):
            selected = self.log_files[file_list.index]
            self.selected_file = selected['path']
            
            # Verificar permisos
            if not selected['readable']:
                self.update_status(f"⚠️  Sin permisos para leer: {selected['name']}")
                return
            
            self.update_status(f"🚀 Abriendo {selected['name']} en terminal externa...")
            self.open_in_external_terminal(selected['path'])
        else:
            self.update_status(f"[DEBUG] Índice inválido: {file_list.index}, len: {len(self.log_files)}")

    def open_in_external_terminal(self, filepath: Path):
        """Abre el archivo usando el visor del sistema en la misma terminal"""
        try:
            with self.app.suspend():
                system = platform.system().lower()
                if system == "windows":
                    # En Windows usamos 'more'
                    os.system(f"more \"{filepath}\"")
                else:
                    # En Linux/Mac usamos 'less' si está disponible
                    viewer = "less" if shutil.which("less") else "more"
                    subprocess.run([viewer, str(filepath)])
            
            self.update_status(f"✅ Visualización finalizada")
            
        except Exception as e:
            self.update_status(f"❌ Error al abrir visor: {str(e)}")
    
    def update_status(self, message: str):
        """Actualizar la barra de estado"""
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(message)


if __name__ == "__main__":
    print("Iniciando aplicación del visor de logs...")
    from textual.app import App
    
    class LogViewerApp(App):
        """Aplicación del visor de logs"""
        
        TITLE = "Visor de Logs del Sistema"
        
        def on_mount(self):
            print("Aplicación montada, mostrando pantalla...")
            self.push_screen(LogViewerScreen())
    
    print("Creando instancia de la aplicación...")
    app = LogViewerApp()
    print("Ejecutando aplicación...")
    app.run()
