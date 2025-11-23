#!/usr/bin/env python3
"""
Wake on LAN (WoL) Sender
Permite gestionar dispositivos y enviar paquetes mágicos para encenderlos remotamente.
"""

from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Button, Input, Static, Label, DataTable
from textual.binding import Binding
from textual.message import Message
import socket
import struct
import json
import os
from pathlib import Path

# Archivo de persistencia
DATA_FILE = "wol_devices.json"

class DeviceForm(ModalScreen):
    """Formulario para añadir/editar dispositivo"""
    
    CSS = """
    DeviceForm {
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
    
    #buttons {
        margin-top: 1;
        align: center middle;
        height: auto;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, device=None):
        super().__init__()
        self.device = device
        
    def compose(self) -> ComposeResult:
        title = "Editar Dispositivo" if self.device else "Nuevo Dispositivo"
        
        with Container(id="dialog"):
            yield Label(f"[bold]{title}[/]")
            
            yield Label("Nombre:", classes="label")
            yield Input(
                placeholder="Ej: Servidor Casa", 
                id="name",
                value=self.device['name'] if self.device else ""
            )
            
            yield Label("Dirección MAC:", classes="label")
            yield Input(
                placeholder="Ej: AA:BB:CC:DD:EE:FF", 
                id="mac",
                value=self.device['mac'] if self.device else ""
            )
            
            yield Label("IP Broadcast (Opcional):", classes="label")
            yield Input(
                placeholder="Ej: 192.168.1.255 (Default: 255.255.255.255)", 
                id="ip",
                value=self.device.get('ip', '') if self.device else ""
            )
            
            yield Label("Puerto (Opcional):", classes="label")
            yield Input(
                placeholder="Default: 9", 
                id="port",
                value=str(self.device.get('port', '')) if self.device else ""
            )
            
            with Horizontal(id="buttons"):
                yield Button("Guardar", variant="primary", id="save")
                yield Button("Cancelar", variant="error", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.save_device()
        elif event.button.id == "cancel":
            self.dismiss(None)
            
    def save_device(self):
        name = self.query_one("#name", Input).value.strip()
        mac = self.query_one("#mac", Input).value.strip()
        ip = self.query_one("#ip", Input).value.strip()
        port = self.query_one("#port", Input).value.strip()
        
        if not name or not mac:
            # En una app real mostraríamos un error
            return
            
        device = {
            "name": name,
            "mac": mac,
            "ip": ip if ip else "255.255.255.255",
            "port": int(port) if port.isdigit() else 9
        }
        self.dismiss(device)

class WakeOnLanScreen(Screen):
    """Pantalla principal de Wake on LAN"""
    
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
        Binding("n", "new_device", "Nuevo"),
        Binding("e", "edit_device", "Editar"),
        Binding("d", "delete_device", "Borrar"),
        Binding("w", "wake_device", "Wake (Encender)"),
        Binding("escape", "quit", "Volver"),
    ]
    
    def __init__(self):
        super().__init__()
        self.devices = []
        self.load_devices()
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Horizontal(id="toolbar"):
                yield Button("Nuevo (n)", id="btn-new", variant="success")
                yield Button("Editar (e)", id="btn-edit", variant="primary")
                yield Button("Borrar (d)", id="btn-delete", variant="error")
                yield Button("⚡ WAKE (w)", id="btn-wake", variant="warning")
            
            yield DataTable(cursor_type="row")
            
        yield Static("Listo", id="status-bar")
        yield Footer()
        
    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Nombre", "MAC", "Broadcast IP", "Puerto")
        self.refresh_table()
        
    def load_devices(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.devices = json.load(f)
            except:
                self.devices = []
    
    def save_devices(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.devices, f, indent=4)
            
    def refresh_table(self):
        table = self.query_one(DataTable)
        table.clear()
        for idx, dev in enumerate(self.devices):
            table.add_row(
                dev['name'], 
                dev['mac'], 
                dev.get('ip', '255.255.255.255'), 
                str(dev.get('port', 9)),
                key=str(idx)
            )
            
    def update_status(self, msg):
        self.query_one("#status-bar", Static).update(msg)
        
    def action_new_device(self):
        def callback(device):
            if device:
                self.devices.append(device)
                self.save_devices()
                self.refresh_table()
                self.update_status(f"✅ Dispositivo '{device['name']}' añadido")
        
        self.app.push_screen(DeviceForm(), callback)
        
    def action_edit_device(self):
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            idx = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            device = self.devices[idx]
            
            def callback(updated_device):
                if updated_device:
                    self.devices[idx] = updated_device
                    self.save_devices()
                    self.refresh_table()
                    self.update_status(f"✅ Dispositivo '{updated_device['name']}' actualizado")
            
            self.app.push_screen(DeviceForm(device), callback)
            
    def action_delete_device(self):
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            idx = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            name = self.devices[idx]['name']
            del self.devices[idx]
            self.save_devices()
            self.refresh_table()
            self.update_status(f"🗑️ Dispositivo '{name}' eliminado")
            
    def action_wake_device(self):
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            idx = int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            self.send_magic_packet(self.devices[idx])
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new":
            self.action_new_device()
        elif event.button.id == "btn-edit":
            self.action_edit_device()
        elif event.button.id == "btn-delete":
            self.action_delete_device()
        elif event.button.id == "btn-wake":
            self.action_wake_device()
            
    def send_magic_packet(self, device):
        mac = device['mac']
        ip = device.get('ip', '255.255.255.255')
        port = device.get('port', 9)
        
        try:
            # Limpiar MAC
            mac_clean = mac.replace(":", "").replace("-", "")
            if len(mac_clean) != 12:
                self.update_status("❌ Formato de MAC inválido")
                return
                
            # Crear paquete mágico: 6 bytes 0xFF + 16 veces la MAC
            data = b'\xFF' * 6 + (bytes.fromhex(mac_clean) * 16)
            
            # Enviar
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(data, (ip, port))
                
            self.update_status(f"⚡ Paquete mágico enviado a {device['name']} ({ip})")
            
        except Exception as e:
            self.update_status(f"❌ Error al enviar: {str(e)}")

    def action_quit(self):
        self.app.exit()

if __name__ == "__main__":
    class WoLApp(App):
        def on_mount(self):
            self.push_screen(WakeOnLanScreen())
            
    WoLApp().run()
