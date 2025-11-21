from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, TabbedContent, TabPane, Checkbox
from textual.binding import Binding
import random
import string
import math
import secrets

class PasswordGeneratorApp(App):
    """Generador y analizador de contraseñas seguras"""
    
    TITLE = "🔐 Generador de Contraseñas"
    
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
    
    #options-container {
        height: auto;
        background: $panel;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .option-row {
        height: auto;
        margin-bottom: 1;
    }
    
    #length-input {
        width: 20;
        margin-left: 1;
    }
    
    #password-display {
        background: $panel;
        border: heavy $primary;
        padding: 2;
        margin: 1 0;
        text-align: center;
        min-height: 5;
    }
    
    #analyze-input {
        width: 1fr;
        margin-right: 1;
    }
    
    #results-container {
        height: 1fr;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
        margin-top: 1;
    }
    
    .button-row {
        height: auto;
        margin-top: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("escape", "quit", "Salir"),
    ]
    
    # Lista de palabras comunes para passphrases
    WORDS = [
        "caballo", "correcto", "bateria", "basico", "python", "seguro", "dragon", "nube", "café", "tabaco",
        "montana", "oceano", "bosque", "ciudad", "estrella", "cerveza","planeta", "galaxia", "cometa",
        "tigre", "leon", "aguila", "delfin", "ballena", "colibri", "pinguino", "mariposa",
        "rayo", "trueno", "viento", "murcielago", "fuego", "agua", "tierra", "hielo", "vapor", "entre", "unos", "ceros", "sapo", "clay"
        "libro", "musica", "pintura", "danza", "poeta", "marihuana", "cancion", "historia", "leyenda",
        "puente", "torre", "castillo", "palacio", "templo", "catedral", "monumento", "estatua",
        "robot", "laser", "cohete", "satelite", "orbital", "quantum", "neutron", "foton", "esternocleidomastoideo"
        
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Static("🔑 GENERADOR Y ANALIZADOR DE CONTRASEÑAS", id="title")
            yield Static("Crea contraseñas seguras y analiza su fortaleza", classes="description")
            
            with TabbedContent():
                with TabPane("Generar Contraseña", id="tab-generate"):
                    with Vertical():
                        with Container(id="options-container"):
                            yield Static("[bold cyan]Opciones de generación:[/]")
                            
                            with Horizontal(classes="option-row"):
                                yield Static("Longitud:")
                                yield Input(value="16", id="length-input")
                                yield Static("(mínimo 8, recomendado 16+)")
                            
                            with Horizontal(classes="option-row"):
                                yield Checkbox("Mayúsculas (A-Z)", value=True, id="check-upper")
                            
                            with Horizontal(classes="option-row"):
                                yield Checkbox("Minúsculas (a-z)", value=True, id="check-lower")
                            
                            with Horizontal(classes="option-row"):
                                yield Checkbox("Números (0-9)", value=True, id="check-numbers")
                            
                            with Horizontal(classes="option-row"):
                                yield Checkbox("Símbolos (!@#$%^&*)", value=True, id="check-symbols")
                        
                        with Horizontal(classes="button-row"):
                            yield Button("🎲 Generar Contraseña", variant="primary", id="btn-generate")
                            yield Button("📝 Generar Passphrase", variant="success", id="btn-passphrase")
                        
                        yield Static("", id="password-display")
                
                with TabPane("Analizar Contraseña", id="tab-analyze"):
                    with Vertical():
                        yield Static(
                            "[cyan]Introduce una contraseña para analizar su fortaleza:[/]"
                        )
                        
                        with Horizontal():
                            yield Input(placeholder="Escribe una contraseña para analizar", password=True, id="analyze-input")
                            yield Button("🔍 Analizar", variant="warning", id="btn-analyze")
                        
                        with VerticalScroll(id="results-container"):
                            yield Static("Escribe una contraseña para comenzar el análisis...", id="analysis-results")
                    
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate":
            self.generate_password()
        elif event.button.id == "btn-passphrase":
            self.generate_passphrase()
        elif event.button.id == "btn-analyze":
            self.analyze_password()

    def generate_password(self):
        try:
            length = int(self.query_one("#length-input", Input).value)
            if length < 8:
                length = 8
        except:
            length = 16
        
        use_upper = self.query_one("#check-upper", Checkbox).value
        use_lower = self.query_one("#check-lower", Checkbox).value
        use_numbers = self.query_one("#check-numbers", Checkbox).value
        use_symbols = self.query_one("#check-symbols", Checkbox).value
        
        # Construir conjunto de caracteres
        chars = ""
        if use_upper:
            chars += string.ascii_uppercase
        if use_lower:
            chars += string.ascii_lowercase
        if use_numbers:
            chars += string.digits
        if use_symbols:
            chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        
        if not chars:
            self.query_one("#password-display", Static).update(
                "[red]❌ Debes seleccionar al menos un tipo de carácter[/]"
            )
            return
        
        # Generar contraseña usando secrets (criptográficamente seguro)
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        # Calcular entropía
        entropy = length * math.log2(len(chars))
        
        # Estimar tiempo de crackeo (asumiendo 10 mil millones intentos/seg)
        combinations = len(chars) ** length
        seconds = combinations / 10_000_000_000
        time_str = self.format_time(seconds)
        
        display = f"""
[bold green]✅ Contraseña generada:[/]

[bold cyan on black] {password} [/]

[bold yellow]Características:[/]
• Longitud: {length} caracteres
• Conjunto: {len(chars)} caracteres posibles
• Entropía: {entropy:.1f} bits
• Tiempo estimado de crackeo: [bold]{time_str}[/]

[dim]Haz clic para copiar (Ctrl+C) y guárdala en un gestor de contraseñas[/]
        """
        
        self.query_one("#password-display", Static).update(display)

    def generate_passphrase(self):
        # Generar 5 palabras aleatorias
        words = [secrets.choice(self.WORDS) for _ in range(5)]
        passphrase = "-".join(words)
        
        # Calcular entropía
        entropy = 5 * math.log2(len(self.WORDS))
        
        # Estimar tiempo de crackeo
        combinations = len(self.WORDS) ** 5
        seconds = combinations / 10_000_000_000
        time_str = self.format_time(seconds)
        
        display = f"""
[bold green]✅ Passphrase generada:[/]

[bold cyan on black] {passphrase} [/]

[bold yellow]Ventajas de las passphrases:[/]
• Más fácil de recordar
• Más difícil de adivinar que contraseñas cortas
• Longitud: {len(passphrase)} caracteres
• Entropía: {entropy:.1f} bits
• Tiempo estimado de crackeo: [bold]{time_str}[/]

[bold green]Ejemplo memorable:[/]
"{words[0].title()} {words[1]} en {words[2]} con {words[3]} y {words[4]}"

[dim]Tip: Puedes modificarla añadiendo números o símbolos para más seguridad[/]
        """
        
        self.query_one("#password-display", Static).update(display)

    def analyze_password(self):
        password = self.query_one("#analyze-input", Input).value
        
        if not password:
            self.query_one("#analysis-results", Static).update(
                "[red]❌ Por favor escribe una contraseña para analizar[/]"
            )
            return
        
        length = len(password)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)
        
        # Calcular tamaño del conjunto
        charset_size = 0
        if has_lower:
            charset_size += 26
        if has_upper:
            charset_size += 26
        if has_digit:
            charset_size += 10
        if has_symbol:
            charset_size += 32
        
        # Calcular entrópia
        entropy = length * math.log2(charset_size) if charset_size > 0 else 0
        
        # Tiempo de crackeo
        combinations = 0
        if charset_size > 0:
            combinations = charset_size ** length
            seconds = combinations / 10_000_000_000
            time_str = self.format_time(seconds)
        else:
            time_str = "Instantáneo"
        
        # Determinar nivel de fortaleza
        score = 0
        if length >= 12:
            score += 2
        elif length >= 8:
            score += 1
        
        if has_upper:
            score += 1
        if has_lower:
            score += 1
        if has_digit:
            score += 1
        if has_symbol:
            score += 2
        
        if entropy >= 80:
            strength = "MUY FUERTE"
            color = "green"
            icon = "🟢"
        elif entropy >= 60:
            strength = "FUERTE"
            color = "green"
            icon = "🟢"
        elif entropy >= 40:
            strength = "MEDIA"
            color = "yellow"
            icon = "🟡"
        elif entropy >= 25:
            strength = "DÉBIL"
            color = "red"
            icon = "🟠"
        else:
            strength = "MUY DÉBIL"
            color = "red"
            icon = "🔴"
        
        # Detectar patrones comunes
        warnings = []
        common_passwords = ["password", "123456", "qwerty", "admin", "letmein", "welcome"]
        if password.lower() in common_passwords:
            warnings.append("⚠️ Esta es una contraseña muy común ... échale más imaginación")
        
        if password.lower() == password or password.upper() == password:
            warnings.append("⚠️ Solo usa un tipo de letra (mayúsculas o minúsculas)")
        
        if password.isdigit():
            warnings.append("⚠️ Solo contiene números")
        
        if len(set(password)) < length / 2:
            warnings.append("⚠️ Esto tiene muchos caracteres repetidos")
        
        # Generar reporte
        output = f"""
[bold {color}]{icon} FORTALEZA: {strength}[/]

[bold underline]Análisis de la contraseña:[/]

[bold]Características:[/]
• Longitud: {length} caracteres {'✓' if length >= 12 else '✗ (mínimo recomendado: 12)'}
• Mayúsculas: {'✓' if has_upper else '✗'}
• Minúsculas: {'✓' if has_lower else '✗'}
• Números: {'✓' if has_digit else '✗'}
• Símbolos: {'✓' if has_symbol else '✗'}

[bold]Métricas de seguridad:[/]
• Entropía: {entropy:.1f} bits
• Conjunto de caracteres: {charset_size} posibles
• Combinaciones posibles: {combinations if charset_size > 0 else 0:,.0f}
• Tiempo estimado de crackeo: [bold]{time_str}[/]

"""
        
        if warnings:
            output += "[bold red]⚠️ ADVERTENCIAS:[/]\n"
            for warning in warnings:
                output += f"{warning}\n"
            output += "\n"
        
        # Recomendaciones
        output += "[bold cyan]💡 RECOMENDACIONES:[/]\n"
        
        if length < 12:
            output += "🔹 Aumenta la longitud a mínimo 12 caracteres\n"
        if not has_upper:
            output += "🔹 Añade letras mayúsculas\n"
        if not has_lower:
            output += "🔹 Añade letras minúsculas\n"
        if not has_digit:
            output += "🔹 Incluye números\n"
        if not has_symbol:
            output += "🔹 Usa símbolos especiales (!@#$%^&*)\n"
        
        output += "\n[bold green]Mejores prácticas:[/]\n"
        output += "• Usa contraseñas únicas para cada servicio\n"
        output += "• Usa un gestor de contraseñas\n"
        output += "• Habilita autenticación de dos factores (2FA)\n"
        output += "• Cambia contraseñas críticas regularmente\n"
        
        self.query_one("#analysis-results", Static).update(output)

    def format_time(self, seconds):
        """Formatea el tiempo de forma legible"""
        if seconds < 1:
            return "Menos de 1 segundo"
        elif seconds < 60:
            return f"{seconds:.0f} segundos"
        elif seconds < 3600:
            return f"{seconds/60:.0f} minutos"
        elif seconds < 86400:
            return f"{seconds/3600:.0f} horas"
        elif seconds < 31536000:
            return f"{seconds/86400:.0f} días"
        elif seconds < 31536000 * 1000:
            return f"{seconds/31536000:.0f} años"
        elif seconds < 31536000 * 1000000:
            return f"{seconds/(31536000*1000):.0f} mil años"
        elif seconds < 31536000 * 1000000000:
            return f"{seconds/(31536000*1000000):.0f} millones de años"
        else:
            return f"{seconds/(31536000*1000000000):.0f} mil millones de años"

if __name__ == "__main__":
    PasswordGeneratorApp().run()
