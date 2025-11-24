from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Input, Label, Static, TabbedContent, TabPane, DirectoryTree, TextArea
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from PIL import Image
import os

class StegoToolApp(App):
    """Herramienta de Esteganografía (LSB)"""
    
    TITLE = "🖼️ Esteganografía (Stego Tool)"
    CSS = """
    Screen {
        background: $surface;
    }
    
    .box {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    #tree-view {
        height: 20;
        border: solid $secondary;
        margin-bottom: 1;
    }
    
    .path-display {
        background: $surface-lighten-1;
        padding: 1;
        margin-bottom: 1;
    }
    
    Button {
        margin: 1;
    }
    
    TextArea {
        height: 10;
        border: solid $secondary;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
    ]
    
    selected_image = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with TabbedContent():
            with TabPane("🔒 Ocultar (Encode)", id="tab-encode"):
                yield Label("1. Selecciona una imagen (PNG recomendado):")
                yield DirectoryTree("/", id="tree-encode")
                yield Static("Ninguna imagen seleccionada", id="path-encode", classes="path-display")
                
                yield Label("2. Escribe el mensaje secreto:")
                yield TextArea(id="secret-msg")
                
                yield Label("3. Nombre del archivo de salida (ej: secreto.png):")
                yield Input(placeholder="output.png", id="output-name")
                
                yield Button("🔒 Ocultar Mensaje", id="btn-encode", variant="primary")
                yield Static("", id="status-encode")
                
            with TabPane("🔓 Revelar (Decode)", id="tab-decode"):
                yield Label("1. Selecciona la imagen con mensaje oculto:")
                yield DirectoryTree("/", id="tree-decode")
                yield Static("Ninguna imagen seleccionada", id="path-decode", classes="path-display")
                
                yield Button("🔓 Revelar Mensaje", id="btn-decode", variant="warning")
                
                yield Label("Mensaje revelado:")
                yield TextArea(id="revealed-msg", read_only=True)
                yield Static("", id="status-decode")
        
        yield Footer()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        path = event.path
        if not path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            self.notify("Por favor selecciona una imagen (PNG/JPG/BMP)", severity="warning")
            return
            
        if event.control.id == "tree-encode":
            self.query_one("#path-encode", Static).update(f"Seleccionado: {path}")
            self.selected_encode = path
        elif event.control.id == "tree-decode":
            self.query_one("#path-decode", Static).update(f"Seleccionado: {path}")
            self.selected_decode = path

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-encode":
            self.encode_message()
        elif event.button.id == "btn-decode":
            self.decode_message()

    def encode_message(self):
        try:
            if not hasattr(self, 'selected_encode') or not self.selected_encode:
                self.notify("Selecciona una imagen primero", severity="error")
                return
                
            msg = self.query_one("#secret-msg", TextArea).text
            if not msg:
                self.notify("Escribe un mensaje", severity="error")
                return
                
            output_name = self.query_one("#output-name", Input).value
            if not output_name: output_name = "output.png"
            
            # Logic
            img = Image.open(self.selected_encode)
            encoded = self.hide_text(img, msg)
            encoded.save(output_name)
            
            self.query_one("#status-encode", Static).update(f"[green]¡Mensaje oculto guardado en {output_name}![/]")
            self.notify("Mensaje ocultado con éxito")
            
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            self.query_one("#status-encode", Static).update(f"[red]Error: {e}[/]")

    def decode_message(self):
        try:
            if not hasattr(self, 'selected_decode') or not self.selected_decode:
                self.notify("Selecciona una imagen primero", severity="error")
                return
                
            img = Image.open(self.selected_decode)
            msg = self.reveal_text(img)
            
            self.query_one("#revealed-msg", TextArea).text = msg
            self.query_one("#status-decode", Static).update("[green]¡Decodificación completada![/]")
            
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            self.query_one("#status-decode", Static).update(f"[red]Error: {e}[/]")

    # --- LSB Logic ---
    def to_bin(self, data):
        if isinstance(data, str):
            return ''.join([format(ord(i), "08b") for i in data])
        elif isinstance(data, bytes) or isinstance(data, int): # Pixel values
            return [format(i, "08b") for i in data]
        return data

    def hide_text(self, image, secret_message):
        # Append delimiter to know when to stop
        secret_message += "#####" 
        
        image = image.convert('RGB')
        data = image.getdata()
        
        binary_secret_message = self.to_bin(secret_message)
        data_len = len(binary_secret_message)
        
        new_data = []
        digit = 0
        
        for pixel in data:
            if digit < data_len:
                new_pixel = list(pixel)
                for i in range(3): # R, G, B
                    if digit < data_len:
                        # Modify LSB
                        new_pixel[i] = int(self.to_bin(new_pixel[i])[:-1] + binary_secret_message[digit], 2)
                        digit += 1
                new_data.append(tuple(new_pixel))
            else:
                new_data.append(pixel)
                
        new_img = Image.new(image.mode, image.size)
        new_img.putdata(new_data)
        return new_img

    def reveal_text(self, image):
        image = image.convert('RGB')
        data = image.getdata()
        
        binary_data = ""
        for pixel in data:
            for value in pixel:
                binary_data += self.to_bin(value)[-1] # Get LSB
                
        # Split by 8 bits
        all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
        
        decoded_data = ""
        for byte in all_bytes:
            decoded_data += chr(int(byte, 2))
            if decoded_data[-5:] == "#####": # Check delimiter
                return decoded_data[:-5]
                
        return decoded_data # Should not happen if delimiter exists

if __name__ == "__main__":
    StegoToolApp().run()
