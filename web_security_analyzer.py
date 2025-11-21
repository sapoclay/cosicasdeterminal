from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding
import requests
from urllib.parse import urlparse

class WebSecurityAnalyzerApp(App):
    """Analizador de seguridad de cabeceras HTTP"""
    
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
    
    #input-container {
        height: auto;
        margin-bottom: 1;
    }
    
    #input-url {
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
    """
    
    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("escape", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Static("🌐 ANALIZADOR DE SEGURIDAD WEB", id="title")
            yield Static("Analiza cabeceras de seguridad HTTP y detecta vulnerabilidades", classes="description")
            
            with Horizontal(id="input-container"):
                yield Input(placeholder="https://ejemplo.com", id="input-url")
                yield Button("🔍 Analizar", variant="primary", id="btn-analyze")
            
            with VerticalScroll(id="results-container"):
                yield Static("Escribe una URL para analizar su seguridad...", id="analysis-results")
                
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-analyze":
            self.analyze_website()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-url":
            self.analyze_website()

    def analyze_website(self):
        url = self.query_one("#input-url", Input).value.strip()
        
        if not url:
            self.query_one("#analysis-results", Static).update(
                "[red]❌ Por favor escribe una URL válida[/]"
            )
            return
        
        if not url.startswith("http"):
            url = "https://" + url
            self.query_one("#input-url", Input).value = url
        
        results_widget = self.query_one("#analysis-results", Static)
        results_widget.update("⏳ Analizando seguridad del sitio web...")
        
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            headers = response.headers
            
            # Analizar cabeceras de seguridad
            security_score = 0
            total_checks = 10
            issues = []
            recommendations = []
            good_practices = []
            
            # 1. Strict-Transport-Security (HSTS)
            if 'strict-transport-security' in headers:
                hsts = headers['strict-transport-security']
                security_score += 1
                good_practices.append(f"✅ HSTS habilitado: {hsts}")
            else:
                issues.append("❌ HSTS no configurado - El sitio es vulnerable a ataques SSL Strip")
                recommendations.append("Añade: Strict-Transport-Security: max-age=31536000; includeSubDomains")
            
            # 2. Content-Security-Policy (CSP)
            if 'content-security-policy' in headers:
                security_score += 1
                good_practices.append("✅ Content Security Policy configurado")
            else:
                issues.append("❌ CSP no configurado - Vulnerable a XSS y inyección de código")
                recommendations.append("Configura CSP para controlar recursos permitidos")
            
            # 3. X-Frame-Options
            if 'x-frame-options' in headers:
                security_score += 1
                xfo = headers['x-frame-options']
                good_practices.append(f"✅ X-Frame-Options: {xfo}")
            else:
                issues.append("❌ X-Frame-Options ausente - Vulnerable a Clickjacking")
                recommendations.append("Añade: X-Frame-Options: DENY o SAMEORIGIN")
            
            # 4. X-Content-Type-Options
            if 'x-content-type-options' in headers:
                security_score += 1
                good_practices.append("✅ X-Content-Type-Options: nosniff")
            else:
                issues.append("❌ X-Content-Type-Options ausente - Riesgo de MIME sniffing")
                recommendations.append("Añade: X-Content-Type-Options: nosniff")
            
            # 5. X-XSS-Protection
            if 'x-xss-protection' in headers:
                xss = headers['x-xss-protection']
                if '1' in xss:
                    security_score += 1
                    good_practices.append(f"✅ X-XSS-Protection: {xss}")
                else:
                    issues.append("⚠️ X-XSS-Protection deshabilitado")
            else:
                issues.append("❌ X-XSS-Protection ausente")
                recommendations.append("Añade: X-XSS-Protection: 1; mode=block")
            
            # 6. Referrer-Policy
            if 'referrer-policy' in headers:
                security_score += 1
                good_practices.append(f"✅ Referrer-Policy: {headers['referrer-policy']}")
            else:
                issues.append("⚠️ Referrer-Policy no configurado - Posible fuga de información")
                recommendations.append("Añade: Referrer-Policy: no-referrer o strict-origin-when-cross-origin")
            
            # 7. Permissions-Policy
            if 'permissions-policy' in headers or 'feature-policy' in headers:
                security_score += 1
                good_practices.append("✅ Permissions-Policy configurado")
            else:
                issues.append("⚠️ Permissions-Policy ausente - Control limitado de APIs del navegador")
            
            # 8. Verificar HTTPS
            if url.startswith('https://'):
                security_score += 1
                good_practices.append("✅ Conexión HTTPS establecida")
            else:
                issues.append("❌ Conexión HTTP insegura - Los datos se transmiten en texto plano")
                recommendations.append("Migra a HTTPS con un certificado SSL/TLS válido")
            
            # 9. Server header
            if 'server' in headers:
                server = headers['server']
                issues.append(f"⚠️ Server header expuesto: {server} - Información sensible revelada")
                recommendations.append("Oculta o modifica el header 'Server' para no revelar tecnología")
            else:
                security_score += 1
                good_practices.append("✅ Server header oculto")
            
            # 10. X-Powered-By
            if 'x-powered-by' in headers:
                powered = headers['x-powered-by']
                issues.append(f"⚠️ X-Powered-By expuesto: {powered} - Revela tecnología backend")
                recommendations.append("Elimina el header 'X-Powered-By'")
            else:
                security_score += 1
                good_practices.append("✅ X-Powered-By no presente")
            
            # Verificar cookies
            cookies_secure = True
            cookies_httponly = True
            cookies_samesite = True
            
            if 'set-cookie' in headers:
                cookie_header = headers['set-cookie']
                if 'Secure' not in cookie_header:
                    cookies_secure = False
                    issues.append("⚠️ Cookies sin flag 'Secure' - Vulnerable a interceptación")
                if 'HttpOnly' not in cookie_header:
                    cookies_httponly = False
                    issues.append("⚠️ Cookies sin flag 'HttpOnly' - Vulnerable a robo via XSS")
                if 'SameSite' not in cookie_header:
                    cookies_samesite = False
                    issues.append("⚠️ Cookies sin flag 'SameSite' - Vulnerable a CSRF")
            
            # Calcular puntuación
            percentage = (security_score / total_checks) * 100
            
            if percentage >= 80:
                grade = "A"
                color = "green"
                icon = "🟢"
                verdict = "EXCELENTE"
            elif percentage >= 60:
                grade = "B"
                color = "green"
                icon = "🟢"
                verdict = "BUENO"
            elif percentage >= 40:
                grade = "C"
                color = "yellow"
                icon = "🟡"
                verdict = "REGULAR"
            elif percentage >= 20:
                grade = "D"
                color = "red"
                icon = "🟠"
                verdict = "MALO"
            else:
                grade = "F"
                color = "red"
                icon = "🔴"
                verdict = "MUY MALO"
            
            # Generar reporte
            parsed_url = urlparse(url)
            output = f"""
[bold {color}]{icon} CALIFICACIÓN DE SEGURIDAD: {grade} ({percentage:.0f}%) - {verdict}[/]

[bold cyan]Sitio analizado:[/] {parsed_url.netloc}
[bold cyan]URL:[/] {url}
[bold cyan]Código HTTP:[/] {response.status_code}

[bold underline]Resumen:[/]
Controles de seguridad aprobados: {security_score}/{total_checks}

"""
            
            if good_practices:
                output += "\n[bold green]✅ BUENAS PRÁCTICAS IMPLEMENTADAS:[/]\n"
                for practice in good_practices:
                    output += f"{practice}\n"
            
            if issues:
                output += "\n[bold red]❌ PROBLEMAS DE SEGURIDAD DETECTADOS:[/]\n"
                for issue in issues:
                    output += f"{issue}\n"
            
            if recommendations:
                output += "\n[bold yellow]💡 RECOMENDACIONES:[/]\n"
                for rec in recommendations:
                    output += f"• {rec}\n"
            
            # Información adicional
            output += """
[bold cyan]📚 INFORMACIÓN ADICIONAL:[/]

[bold]HSTS (HTTP Strict Transport Security):[/]
Fuerza conexiones HTTPS y previene ataques SSL Strip.

[bold]CSP (Content Security Policy):[/]
Controla qué recursos puede cargar la página, previniendo XSS.

[bold]X-Frame-Options:[/]
Previene que la página sea cargada en un iframe (anti-Clickjacking).

[bold]X-Content-Type-Options:[/]
Evita que el navegador "adivine" el tipo MIME (anti-MIME sniffing).

[bold]Cookies Secure:[/]
Las cookies solo se envían por HTTPS, no por HTTP.

[bold]Cookies HttpOnly:[/]
Las cookies no son accesibles desde JavaScript (anti-XSS).

[bold]Cookies SameSite:[/]
Previene ataques CSRF limitando el envío cross-site.

[dim]Análisis básico completado. Para auditorías completas considera herramientas como
Mozilla Observatory, Security Headers o Qualys SSL Labs.[/]
            """
            
            results_widget.update(output)
            
        except requests.exceptions.SSLError:
            results_widget.update(
                f"[red]❌ Error SSL/TLS:[/] No se pudo verificar el certificado de {url}\n\n"
                "Posibles causas:\n"
                "• Certificado autofirmado\n"
                "• Certificado expirado\n"
                "• Certificado inválido\n\n"
                "[yellow]Este es un problema de seguridad crítico.[/]"
            )
        except requests.exceptions.ConnectionError:
            results_widget.update(
                f"[red]❌ Error de conexión:[/] No se pudo conectar con {url}\n\n"
                "Verifica que la URL sea correcta y el sitio esté accesible."
            )
        except Exception as e:
            results_widget.update(
                f"[red]❌ Error:[/] {str(e)}"
            )

if __name__ == "__main__":
    WebSecurityAnalyzerApp().run()
