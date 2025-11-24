#!/usr/bin/env python3
"""
Launcher Universal 
Compatible con Linux, Windows y macOS
"""

import os
import sys
import platform
import subprocess
import time

# Colores ANSI
class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    RED = '\033[0;31m'
    NC = '\033[0m' # No Color

    @staticmethod
    def enable_windows_ansi():
        """Habilita soporte ANSI en Windows 10/11"""
        if platform.system() == "Windows":
            try:
                from ctypes import windll
                kernel32 = windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass

def clear_screen():
    """Limpia la pantalla según el SO"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def get_python_path():
    """Obtiene la ruta del intérprete Python en el venv"""
    if platform.system() == "Windows":
        venv_python = os.path.join(".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(".venv", "bin", "python")
    
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable # Fallback al python del sistema si no hay venv

def check_venv():
    """Verifica y crea el entorno virtual si es necesario"""
    if not os.path.exists(".venv"):
        print(f"{Colors.YELLOW}⚠️  Entorno virtual no encontrado. Creando...{Colors.NC}")
        subprocess.run([sys.executable, "-m", "venv", ".venv"])
        
        # Instalar dependencias
        pip_path = os.path.join(".venv", "Scripts", "pip") if platform.system() == "Windows" else os.path.join(".venv", "bin", "pip")
        if os.path.exists("requirements.txt"):
            print(f"{Colors.YELLOW}📦 Instalando dependencias...{Colors.NC}")
            subprocess.run([pip_path, "install", "-r", "requirements.txt"])

def show_header():
    print(f"{Colors.CYAN}╔═══════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.CYAN}║     🌐 CosicasDeTerminal - Launcher 🌐        ║{Colors.NC}")
    print(f"{Colors.CYAN}╚═══════════════════════════════════════════════╝{Colors.NC}")
    print()

def show_menu():
    clear_screen()
    show_header()
    print(f"{Colors.GREEN}Selecciona una herramienta:{Colors.NC}")
    print()
    
    # Definir las listas de herramientas por categoría
    basic_tools = [
        "  1) 🔍 Escáner de RED LOCAL",
        "  2) 📊 Monitor de RED en tiempo real",
        "  3) 🛠️  Herramientas de diagnóstico",
        "  4) 🌐 Verificador de conectividad",
        "  5) 📡 Monitor de interfaces",
        "  6) 🔌 Escáner de puertos locales",
        "  7) 📶 Analizador de WiFI",
        "  8) 💾 Monitor de uso de RED",
        "  9) 🖥️  Info del sistema de RED"
    ]

    advanced_tools = [
        " 10) 🔢 Calculadora IP Universal (v4/v6)",
        " 11) 🔍 DNS avanzado",
        " 12) 🔒  Verificador de SSL/TLS",
        " 13) 🚀 Test de velocidad (speedtest)",
        " 14) 🔍 Detector de cambios en RED",
        " 15) 🌍 Localizador GEOIP",
        " 16) 🕵️  Inspector HTTP/API",
        " 17) 🦈 Analizador de Paquetes (Sniffer) [ROOT]",
        " 18) 👂  Escucha de Puertos (Mini-Netcat)"
    ]

    security_tools = [
        " 19) 🛡️  Analizador de vulnerabilidades",
        " 20) 🔑 Generador de contraseñas",
        " 21) 🌐 Analizador de seguridad Web",
        " 22) 🔍 Enumerador de subdominios",
        " 23) 🎭 Cambiador de MAC (Spoofer) [ROOT]",
        " 24) 🔐 Decodificador Universal (Crypto)",
        " 25) 📷 Extractor de Metadatos (Exif)",
        " 26) 🕵️‍♂️ NetStat Monitor (Conexiones)",
        " 27) 🛡️ Verificador de Integridad (FIM)",
        " 28) 📡 Escáner WiFi (Wireless)"
    ]

    diagnostic_tools = [
        " 29) 🔒  Verificador de fugas (DNS/IPv6/WebRTC)",
        " 30) 🔧 Troubleshooter (diagnóstico automático)",
        " 31) 🌍 Monitor de latencia geográfica",
        " 32) 📋 Visor de logs del sistema",
        " 33) ⏰ Wake on LAN (WoL)",
        " 34) 🔑 Gestor de Conexiones (SSH/FTP/SFTP)",
        " 35) 🛡️  Analizador de Logs (Mini-SIEM)",
        " 36) 🖼️  Esteganografía (Stego Tool)",
        " 37) 🌍  Whois & Reputación IP"
    ]

    # Función auxiliar para calcular el ancho visual aproximado
    def get_visual_width(s):
        width = 0
        # Caracteres acentuados y otros símbolos comunes de ancho 1
        single_width_chars = "áéíóúüñÁÉÍÓÚÑ¿¡"
        
        has_emoji = False
        for char in s:
            if ord(char) < 128:
                width += 1
            elif char in single_width_chars:
                width += 1
            else:
                # Asumimos que cualquier otro caracter es parte de un emoji
                has_emoji = True
            
        # Si detectamos caracteres de emoji, sumamos 2 al ancho total
        # (Asumiendo 1 emoji por línea como en nuestras listas)
        if has_emoji:
            width += 2
            
        return width

    # Función auxiliar para imprimir dos columnas
    def print_two_columns(title1, list1, title2, list2):
        # Imprimir títulos
        print(f"{Colors.CYAN}{title1:<50}{title2}{Colors.NC}")
        
        # Determinar el número máximo de filas
        max_rows = max(len(list1), len(list2))
        
        # Imprimir filas
        for i in range(max_rows):
            item1 = list1[i] if i < len(list1) else ""
            item2 = list2[i] if i < len(list2) else ""
            
            # Calcular padding basado en ancho visual
            vis_len = get_visual_width(item1)
            padding = 55 - vis_len
            if padding < 1: padding = 1
            
            print(f"{item1}{' ' * padding}{item2}")
        print()

    # Fila 1: Básicas y Avanzadas
    print_two_columns("═══ Herramientas básicas ═══", basic_tools, "═══ Herramientas avanzadas ═══", advanced_tools)
    
    # Fila 2: Seguridad y Diagnóstico
    print_two_columns("═══ Herramientas de seguridad ═══", security_tools, "═══ Diagnóstico y Privacidad ═══", diagnostic_tools)
    
    print(f"{Colors.CYAN}═══ Otros ═══{Colors.NC}")
    print("  0) 🚀 Launcher (Menú GRÁFICO)")
    print("  a) ℹ️  Acerca de ...")
    print("  q) Salir")
    print()
    print(f"{Colors.YELLOW}💡 Algunas funciones requieren permisos de administrador/root{Colors.NC}")
    print(f"{Colors.YELLOW}💡 Pulsa 'q' en cualquier aplicación para volver aquí{Colors.NC}")
    print()

def show_about():
    clear_screen()
    print(f"{Colors.CYAN}╔═══════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.CYAN}║        📋 ACERCA DE ESTE PROGRAMA 📋          ║{Colors.NC}")
    print(f"{Colors.CYAN}╚═══════════════════════════════════════════════╝{Colors.NC}")
    print()
    print(f"{Colors.GREEN}CosicasDeTerminal - Suite Completa{Colors.NC}")
    print()
    print(f"{Colors.BLUE}Descripción:{Colors.NC}")
    print("  Suite de utilidades para administración,")
    print("  diagnóstico y monitorización de redes.")
    print()
    print(f"{Colors.BLUE}Características:{Colors.NC}")
    print("  • Escáner de dispositivos en red local")
    print("  • Monitor de tráfico en tiempo real")
    print("  • Herramientas de diagnóstico (Ping, Traceroute, etc.)")
    print("  • Calculadora de subredes IPv4")
    print("  • Consultas DNS avanzadas")
    print("  • Análisis de ancho de banda por proceso")
    print("  • Verificador de certificados SSL/TLS")
    print("  • Test de velocidad de internet")
    print("  • Detector de cambios en la red")
    print("  • Localizador GeoIP para IPs y dominios")
    print("  • Inspector HTTP/API para pruebas de endpoints")
    print("  • Analizador de vulnerabilidades de puertos")
    print("  • Generador y analizador de contraseñas seguras")
    print("  • Analizador de seguridad web (cabeceras HTTP)")
    print("  • Enumerador de subdominios")
    print("  • Verificador de fugas (DNS/IPv6/WebRTC/VPN)")
    print("  • Troubleshooter con diagnóstico automático")
    print("  • Monitor de latencia geográfica global")
    print("  • Visor de logs (CLI/TUI cross-platform)")
    print("  • Wake on LAN y Gestor Conexiones (SSH/FTP)")
    print("  • Analizador de Logs (Mini-SIEM)")
    print("  • Esteganografía (Ocultar datos en imágenes)")
    print("  • Whois & Reputación IP")
    print()
    print(f"{Colors.BLUE}Tecnologías:{Colors.NC}")
    print("  • Python 3.12+")
    print("  • Textual TUI Framework")
    print("  • psutil, netifaces, requests")
    print()
    print(f"{Colors.BLUE}Repositorio:{Colors.NC}")
    print(f"  {Colors.YELLOW}https://github.com/sapoclay/cosicasdeterminal{Colors.NC}")
    print()
    print(f"{Colors.GREEN}Desarrollado con ☕ y 🚬  para quien lo necesite por entreunosyceros.net{Colors.NC}")
    print()
    input(f"{Colors.BLUE}Pulsa Intro para volver al menú...{Colors.NC}")

def run_tool(script_name, tool_name):
    print(f"{Colors.GREEN}Iniciando {tool_name}...{Colors.NC}")
    python_exe = get_python_path()
    try:
        subprocess.run([python_exe, script_name])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"{Colors.RED}Error al ejecutar {script_name}: {e}{Colors.NC}")
        time.sleep(2)

def main():
    Colors.enable_windows_ansi()
    check_venv()
    
    tools = {
        "1": ("network_scanner.py", "ESCÁNER DE RED"),
        "2": ("network_monitor.py", "MONITOR DE RED"),
        "3": ("network_tools.py", "HERRAMIENTAS DE DIAGNÓSTICO"),
        "4": ("connectivity_checker.py", "VERIFICADOR DE CONECTIVIDAD"),
        "5": ("interface_monitor.py", "MONITOR DE INTERFACES"),
        "6": ("local_port_scanner.py", "ESCÁNER DE PUERTOS LOCALES"),
        "7": ("wifi_analyzer.py", "ANALIZADOR DE WIFI"),
        "8": ("simple_network_monitor.py", "MONITOR DE USO DE RED"),
        "9": ("network_system_info.py", "INFO DEL SISTEMA DE RED"),
        "10": ("subnet_calculator.py", "CALCULADORA DE SUBREDES"),
        "11": ("dns_advanced.py", "DNS AVANZADO"),
        "12": ("ssl_checker.py", "VERIFICADOR SSL/TLS"),
        "13": ("speedtest_app.py", "TEST DE VELOCIDAD"),
        "14": ("network_change_detector.py", "DETECTOR DE CAMBIOS EN RED"),
        "15": ("geoip_locator.py", "LOCALIZADOR GEOIP"),
        "16": ("http_inspector.py", "INSPECTOR HTTP"),
        "17": ("packet_sniffer.py", "ANALIZADOR DE PAQUETES"),
        "18": ("port_listener.py", "ESCUCHA DE PUERTOS"),
        "19": ("vuln_port_scanner.py", "ANALIZADOR DE VULNERABILIDADES"),
        "20": ("password_generator.py", "GENERADOR DE CONTRASEÑAS"),
        "21": ("web_security_analyzer.py", "ANALIZADOR DE SEGURIDAD WEB"),
        "22": ("subdomain_enumerator.py", "ENUMERADOR DE SUBDOMINIOS"),
        "23": ("mac_changer.py", "CAMBIADOR DE MAC"),
        "24": ("crypto_tool.py", "CRYPTO TOOL"),
        "25": ("metadata_viewer.py", "VISOR DE METADATOS"),
        "26": ("netstat_monitor.py", "NETSTAT MONITOR"),
        "27": ("file_integrity.py", "VERIFICADOR INTEGRIDAD"),
        "28": ("wifi_scanner.py", "ESCÁNER WIFI"),
        "29": ("leak_tester.py", "VERIFICADOR DE FUGAS"),
        "30": ("network_troubleshooter.py", "TROUBLESHOOTER"),
        "31": ("geo_latency_monitor.py", "MONITOR DE LATENCIA GEOGRÁFICA"),
        "32": ("log_viewer.py", "VISOR DE LOGS"),
        "33": ("wake_on_lan.py", "WAKE ON LAN"),
        "34": ("connection_manager.py", "GESTOR DE CONEXIONES"),
        "35": ("log_analyzer.py", "ANALIZADOR DE LOGS"),
        "36": ("stego_tool.py", "ESTEGANOGRAFÍA"),
        "37": ("whois_checker.py", "WHOIS & REPUTACIÓN"),
        "0": ("launcher.py", "Launcher Gráfico")
    }

    while True:
        show_menu()
        option = input("Opción: ").strip().lower()
        
        if option in ['q', 'quit', 'exit']:
            clear_screen()
            print(f"{Colors.YELLOW}¡Hasta luego!{Colors.NC}")
            break
        elif option in ['a', 'about']:
            show_about()
        elif option in tools:
            script, name = tools[option]
            if option == "0":
                clear_screen()
                print(f"{Colors.GREEN}Iniciando Launcher Gráfico...{Colors.NC}")
                time.sleep(1)
                run_tool(script, name)
                clear_screen()
            else:
                run_tool(script, name)
        else:
            print(f"{Colors.YELLOW}Opción no válida{Colors.NC}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n{Colors.YELLOW}¡Hasta luego!{Colors.NC}")
