#!/usr/bin/env python3
"""
Connection Manager
Gestor de conexiones multiplataforma (SSH, FTP, SFTP)
"""

from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Input, Static, Label, DataTable, RadioSet, RadioButton
from textual.binding import Binding
import json
import os
import subprocess
import platform

# Archivo de persistencia
DATA_FILE = "saved_connections.json"

class ConnectionForm(ModalScreen):
    """Formulario para añadir/editar conexión"""
    
    CSS = """
    ConnectionForm {
        align: center middle;
        background: 0%;
    }
    
    #dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
    }
    
    .label {
        margin-top: 1;
        margin-bottom: 0;
        color: $text-muted;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    RadioSet {
        margin-bottom: 1;
        height: auto;
    }
    
    #buttons {
        margin-top: 1;
        align: center middle;
        height: auto;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, connection=None):
        super().__init__()
        self.connection = connection
        
    def compose(self) -> ComposeResult:
        title = "Editar Conexión" if self.connection else "Nueva Conexión"
        
        with Container(id="dialog"):
            yield Label(f"[bold]{title}[/]")
            
            yield Label("Nombre (Alias):", classes="label")
            yield Input(
                placeholder="Ej: Servidor Web (REQUERIDO)", 
                id="name",
                value=self.connection['name'] if self.connection else ""
            )
            
            yield Label("Protocolo:", classes="label")
            with RadioSet(id="protocol"):
                yield RadioButton("SSH (Secure Shell)", value=True)
                yield RadioButton("SFTP (SSH File Transfer)")
                yield RadioButton("FTP (File Transfer Protocol)")
            
            
            yield Label("Host (IP o Dominio):", classes="label")
            yield Input(
                placeholder="Ej: ftp.example.com (REQUERIDO)", 
                id="host",
                value=self.connection['host'] if self.connection else ""
            )
            
            yield Label("Usuario:", classes="label")
            yield Input(
                placeholder="Ej: usuario", 
                id="user",
                value=self.connection.get('user', '') if self.connection else ""
            )
            
            yield Label("Puerto:", classes="label")
            yield Input(
                placeholder="Default: SSH/SFTP=22, FTP=21", 
                id="port",
                value=str(self.connection.get('port', '')) if self.connection else ""
            )
            
            with Horizontal(id="buttons"):
                yield Button("Guardar", variant="primary", id="save")
                yield Button("Cancelar", variant="error", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.save_connection()
        elif event.button.id == "cancel":
            self.dismiss(None)
            
    def save_connection(self):
        name = self.query_one("#name", Input).value.strip()
        radio_set = self.query_one("#protocol", RadioSet)
        
        # Map button label to protocol
        protocol_map = {
            "SSH (Secure Shell)": "ssh",
            "SFTP (SSH File Transfer)": "sftp",
            "FTP (File Transfer Protocol)": "ftp"
        }
        button_label = radio_set.pressed_button.label.plain if radio_set.pressed_button else "SSH (Secure Shell)"
        protocol = protocol_map.get(button_label, "ssh")
        
        host = self.query_one("#host", Input).value.strip()
        user = self.query_one("#user", Input).value.strip()
        port_str = self.query_one("#port", Input).value.strip()
        
        # Validation
        if not name:
            self.app.bell()
            self.query_one("#name", Input).focus()
            return
        
        if not host:
            self.app.bell()
            self.query_one("#host", Input).focus()
            return
        
        # Determinar puerto por defecto
        default_port = 21 if protocol == "ftp" else 22
        port = int(port_str) if port_str.isdigit() else default_port
            
        connection = {
            "name": name,
            "protocol": protocol,
            "host": host,
            "user": user if user else "anonymous", # Default user logic
            "port": port
        }
        self.dismiss(connection)

class ConnectionManagerScreen(Screen):
    """Pantalla principal del Gestor de Conexiones"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        padding: 1;
    }
    
    #toolbar {
        height: auto;
        margin-bottom: 1;
        align: right middle;
    }
    
    Button {
        margin-left: 1;
    }
    
    DataTable {
        height: 1fr;
        border: solid $primary;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("n", "new_conn", "Nuevo"),
        Binding("e", "edit_conn", "Editar"),
        Binding("d", "delete_conn", "Borrar"),
        Binding("c", "connect", "Conectar"),
        Binding("enter", "connect", "Conectar"),
        Binding("escape", "quit", "Volver"),
    ]
    
    def __init__(self):
        super().__init__()
        self.connections = []
        self.load_connections()
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Horizontal(id="toolbar"):
                yield Button("Nuevo (n)", id="btn-new", variant="success")
                yield Button("Editar (e)", id="btn-edit", variant="primary")
                yield Button("Borrar (d)", id="btn-delete", variant="error")
                yield Button("🚀 CONECTAR (Enter)", id="btn-connect", variant="warning")
            
            yield DataTable(cursor_type="row")
            
        yield Static("Listo", id="status-bar")
        yield Footer()
        
    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Nombre", "Protocolo", "Usuario", "Host", "Puerto")
        self.refresh_table()
        
    def load_connections(self):
        # Intentar cargar del nuevo archivo, si no existe, migrar del antiguo
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.connections = json.load(f)
            except:
                self.connections = []
        elif os.path.exists("ssh_connections.json"):
            # Migración simple
            try:
                with open("ssh_connections.json", 'r') as f:
                    old_conns = json.load(f)
                    for c in old_conns:
                        c['protocol'] = 'ssh' # Asumir SSH para los antiguos
                    self.connections = old_conns
                    self.save_connections() # Guardar en nuevo formato
            except:
                self.connections = []
    
    def save_connections(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.connections, f, indent=4)
            
    def refresh_table(self):
        table = self.query_one(DataTable)
        table.clear()
        for idx, conn in enumerate(self.connections):
            table.add_row(
                conn['name'],
                conn.get('protocol', 'ssh').upper(),
                conn['user'], 
                conn['host'], 
                str(conn['port']),
                key=str(idx)
            )
            
    def update_status(self, msg):
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(msg)
        status_bar.refresh()
        
    def action_new_conn(self):
        def callback(conn):
            if conn:
                self.connections.append(conn)
                self.save_connections()
                self.refresh_table()
                self.update_status(f"✅ Conexión '{conn['name']}' añadida")
        
        self.app.push_screen(ConnectionForm(), callback)
        
    def action_edit_conn(self):
        table = self.query_one(DataTable)
        
        # Check if there are any connections
        if not self.connections:
            self.notify("⚠️ No hay conexiones guardadas para editar", severity="warning", timeout=3)
            return
            
        if table.cursor_row is not None:
            try:
                idx = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
                conn = self.connections[idx]
                
                def callback(updated_conn):
                    if updated_conn:
                        self.connections[idx] = updated_conn
                        self.save_connections()
                        self.refresh_table()
                        self.update_status(f"✅ Conexión '{updated_conn['name']}' actualizada")
                
                self.app.push_screen(ConnectionForm(conn), callback)
            except:
                self.update_status("⚠️ Error al seleccionar la conexión")
            
    def action_delete_conn(self):
        table = self.query_one(DataTable)
        
        # Check if there are any connections
        if not self.connections:
            self.notify("⚠️ No hay conexiones guardadas para eliminar", severity="warning", timeout=3)
            return
            
        if table.cursor_row is not None:
            try:
                idx = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
                name = self.connections[idx]['name']
                del self.connections[idx]
                self.save_connections()
                self.refresh_table()
                self.update_status(f"🗑️ Conexión '{name}' eliminada")
            except:
                self.update_status("⚠️ Error al eliminar la conexión")
            
    def action_connect(self):
        table = self.query_one(DataTable)
        
        # Check if there are any connections
        if not self.connections:
            self.notify("⚠️ No hay conexiones guardadas. Crea una nueva con 'n'", severity="warning", timeout=3)
            return
            
        if table.cursor_row is not None:
            try:
                idx = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
                self.connect_session(self.connections[idx])
            except:
                self.update_status("⚠️ Error al conectar")
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new":
            self.action_new_conn()
        elif event.button.id == "btn-edit":
            self.action_edit_conn()
        elif event.button.id == "btn-delete":
            self.action_delete_conn()
        elif event.button.id == "btn-connect":
            self.action_connect()
            
    def connect_session(self, conn):
        protocol = conn.get('protocol', 'ssh')
        user = conn['user']
        host = conn['host']
        port = str(conn['port'])
        
        cmd = []
        
        if protocol == 'ssh':
            cmd = ["ssh", "-p", port, f"{user}@{host}"]
        elif protocol == 'sftp':
            cmd = ["sftp", "-P", port, f"{user}@{host}"]
        elif protocol == 'ftp':
            # FTP standard usage: ftp host port
            cmd = ["ftp", host, port]
        
        try:
            with self.app.suspend():
                # Limpiar pantalla
                if platform.system().lower() == "windows":
                    os.system("cls")
                else:
                    os.system("clear")
                    
                print(f"🚀 Conectando a {conn['name']} ({protocol.upper()}://{user}@{host}:{port})...")
                print("-" * 50)
                
                subprocess.run(cmd)
                
                print("-" * 50)
                input("Presiona ENTER para volver al gestor...")
                
            self.update_status(f"✅ Sesión {protocol.upper()} finalizada")
            
        except Exception as e:
            self.update_status(f"❌ Error al conectar: {str(e)}")

    def action_quit(self):
        self.app.exit()

if __name__ == "__main__":
    import traceback
    try:
        class ConnectionApp(App):
            def on_mount(self):
                self.push_screen(ConnectionManagerScreen())
                
            def on_exception(self, exception: Exception) -> None:
                import traceback
                with open("connection_manager_internal_error.log", "w") as f:
                    f.write(traceback.format_exc())
                self.exit()
                
        ConnectionApp().run()
    except Exception as e:
        with open("connection_manager_error.log", "w") as f:
            f.write(traceback.format_exc())
        print(f"Error fatal: {e}")
