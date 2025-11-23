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
    
    print(f"{Colors.CYAN}═══ Herramientas básicas ═══{Colors.NC}")
    print("  1) 🔍 Escáner de RED LOCAL")
    print("  2) 📊 Monitor de RED en tiempo real")
    print("  3) 🛠️  Herramientas de diagnóstico")
    print("  4) 🌐 Verificador de conectividad")
    print("  5) 📡 Monitor de interfaces")
    print("  6) 🔌 Escáner de puertos locales")
    print("  7) 📶 Analizador de WiFI")
    print("  8) 💾 Monitor de uso de RED")
    print("  9) 🖥️  Info del sistema de RED")
    print()
    
    print(f"{Colors.CYAN}═══ Herramientas avanzadas ═══{Colors.NC}")
    print(" 10) 🔢 Calculadora de subredes")
    print(" 11) 🔍 DNS avanzado")
    print(" 12) 🔒 Verificador de SSL/TLS")
    print(" 13) 🚀 Test de velocidad (speedtest)")
    print(" 14) 🔍 Detector de cambios en RED")
    print(" 15) 🌍 Localizador GEOIP")
    print(" 16) 🕵️  Inspector HTTP/API")
    print()
    
    print(f"{Colors.CYAN}═══ Herramientas de seguridad ═══{Colors.NC}")
    print(" 17) 🛡️  Analizador de vulnerabilidades")
    print(" 18) 🔑 Generador de contraseñas")
    print(" 19) 🌐 Analizador de seguridad Web")
    print(" 20) 🔍 Enumerador de subdominios")
    print()
    
    print(f"{Colors.CYAN}═══ Diagnóstico y Privacidad ═══{Colors.NC}")
    print(" 21) 🔒 Verificador de fugas (DNS/IPv6/WebRTC)")
    print(" 22) 🔧 Troubleshooter (diagnóstico automático)")
    print(" 23) 🌍 Monitor de latencia geográfica")
    print(" 24) 📋 Visor de logs del sistema")
    print(" 25) ⏰ Wake on LAN (WoL)")
    print(" 26) 🔑 Gestor de Conexiones (SSH/FTP/SFTP)")
    print()
    
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
        "17": ("vuln_port_scanner.py", "ANALIZADOR DE VULNERABILIDADES"),
        "18": ("password_generator.py", "GENERADOR DE CONTRASEÑAS"),
        "19": ("web_security_analyzer.py", "ANALIZADOR DE SEGURIDAD WEB"),
        "20": ("subdomain_enumerator.py", "ENUMERADOR DE SUBDOMINIOS"),
        "21": ("leak_tester.py", "VERIFICADOR DE FUGAS"),
        "22": ("network_troubleshooter.py", "TROUBLESHOOTER"),
        "23": ("geo_latency_monitor.py", "MONITOR DE LATENCIA GEOGRÁFICA"),
        "24": ("log_viewer.py", "VISOR DE LOGS"),
        "25": ("wake_on_lan.py", "WAKE ON LAN"),
        "26": ("connection_manager.py", "GESTOR DE CONEXIONES"),
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
