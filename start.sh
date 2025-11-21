#!/bin/bash
# Script de inicio para CosicasDeTerminal

# Colores para el output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Verificar que existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Entorno virtual no encontrado. Creando...${NC}"
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

# Función para mostrar el menú
show_menu() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     🌐 CosicasDeTerminal - Launcher 🌐        ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Selecciona una herramienta:${NC}"
    echo ""
    echo -e "${CYAN}═══ Herramientas básicas ═══${NC}"
    echo "  1) 🔍 Escáner de RED LOCAL"
    echo "  2) 📊 Monitor de RED en tiempo real"
    echo "  3) 🛠️  Herramientas de diagnóstico"
    echo "  4) 🌐 Verificador de conectividad"
    echo "  5) 📡 Monitor de interfaces"
    echo "  6) 🔌 Escáner de puertos locales"
    echo "  7) 📶 Analizador de WiFI"
    echo "  8) 💾 Monitor de uso de RED"
    echo "  9) 🖥️  Info del sistema de RED"
    echo ""
    echo -e "${CYAN}═══ Herramientas avanzadas ═══${NC}"
    echo " 10) 🔢 Calculadora de subredes"
    echo " 11) 🔍 DNS avanzado"
    echo " 12) 🔒 Verificador de SSL/TLS"
    echo " 13) 🚀 Test de velocidad (speedtest)"
    echo " 14) 🔍 Detector de cambios en RED"
    echo " 15) 🌍 Localizador GEOIP"
    echo " 16) 🕵️  Inspector HTTP/API"
    echo ""
    echo -e "${CYAN}═══ Herramientas de seguridad ═══${NC}"
    echo " 17) 🛡️  Analizador de vulnerabilidades"
    echo " 18) 🔑 Generador de contraseñas"
    echo " 19) 🌐 Analizador de seguridad Web"
    echo " 20) 🔍 Enumerador de subdominios"
    echo ""
    echo -e "${CYAN}═══ Otros ═══${NC}"
    echo "  0) 🚀 Launcher (Menú GRÁFICO)"
    echo "  a) ℹ️  Acerca de ..."
    echo "  q) Salir"
    echo ""
    echo -e "${YELLOW}💡 Algunas funciones requieren permisos SUDO${NC}"
    echo -e "${YELLOW}💡 Pulsa 'q' en cualquier aplicación para volver aquí${NC}"
    echo ""
}

# Función para mostrar información del programa
show_about() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        📋 ACERCA DE ESTE PROGRAMA 📋          ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}CosicasDeTerminal - Suite Completa${NC}"
    echo ""
    echo -e "${BLUE}Descripción:${NC}"
    echo "  Suite de utilidades para administración,"
    echo "  diagnóstico y monitorización de redes."
    echo ""
    echo -e "${BLUE}Características:${NC}"
    echo "  • Escáner de dispositivos en red local"
    echo "  • Monitor de tráfico en tiempo real"
    echo "  • Herramientas de diagnóstico (Ping, Traceroute, etc.)"
    echo "  • Calculadora de subredes IPv4"
    echo "  • Consultas DNS avanzadas"
    echo "  • Análisis de ancho de banda por proceso"
    echo "  • Verificador de certificados SSL/TLS"
    echo "  • Test de velocidad de internet"
    echo "  • Detector de cambios en la red"
    echo "  • Localizador GeoIP para IPs y dominios"
    echo "  • Inspector HTTP/API para pruebas de endpoints"
    echo "  • Analizador de vulnerabilidades de puertos"
    echo "  • Generador y analizador de contraseñas seguras"
    echo "  • Analizador de seguridad web (cabeceras HTTP)"
    echo "  • Enumerador de subdominios"
    echo ""
    echo -e "${BLUE}Tecnologías:${NC}"
    echo "  • Python 3.12+"
    echo "  • Textual TUI Framework"
    echo "  • psutil, netifaces, requests"
    echo ""
    echo -e "${BLUE}Repositorio:${NC}"
    echo -e "  ${YELLOW}https://github.com/sapoclay/cosicasdeterminal${NC}"
    echo ""
    echo -e "${GREEN}Desarrollado con ☕ y 🚬  para quien lo necesite por entreunosyceros.net{NC}"
    echo ""
    echo -e "${BLUE}Pulsa Intro para volver al menú...${NC}"
    read
}

# Bucle principal del menú
while true; do
    show_menu
    read -p "Opción: " option
    
    case $option in
        1)
            echo -e "${GREEN}Iniciando ESCÁNER DE RED...${NC}"
            .venv/bin/python network_scanner.py
            ;;
        2)
            echo -e "${GREEN}Iniciando MONITOR DE RED...${NC}"
            .venv/bin/python network_monitor.py
            ;;
        3)
            echo -e "${GREEN}Iniciando HERRAMIENTAS DE DIAGNÓSTICO...${NC}"
            .venv/bin/python network_tools.py
            ;;
        4)
            echo -e "${GREEN}Iniciando VERIFICADOR DE CONECTIVIDAD...${NC}"
            .venv/bin/python connectivity_checker.py
            ;;
        5)
            echo -e "${GREEN}Iniciando MONITOR DE INTERFACES...${NC}"
            .venv/bin/python interface_monitor.py
            ;;
        6)
            echo -e "${GREEN}Iniciando ESCÁNER DE PUERTOS LOCALES...${NC}"
            .venv/bin/python local_port_scanner.py
            ;;
        7)
            echo -e "${GREEN}Iniciando ANALIZADOR DE WIFI...${NC}"
            .venv/bin/python wifi_analyzer.py
            ;;
        8)
            echo -e "${GREEN}Iniciando MONITOR DE USO DE RED...${NC}"
            .venv/bin/python simple_network_monitor.py
            ;;
        9)
            echo -e "${GREEN}Iniciando INFO DEL SISTEMA DE RED...${NC}"
            .venv/bin/python network_system_info.py
            ;;
        10)
            echo -e "${GREEN}Iniciando CALCULADORA DE SUBREDES...${NC}"
            .venv/bin/python subnet_calculator.py
            ;;
        11)
            echo -e "${GREEN}Iniciando DNS AVANZADO...${NC}"
            .venv/bin/python dns_advanced.py
            ;;
        12)
            echo -e "${GREEN}Iniciando VERIFICADOR SSL/TLS...${NC}"
            .venv/bin/python ssl_checker.py
            ;;
        13)
            echo -e "${GREEN}Iniciando TEST DE VELOCIDAD...${NC}"
            .venv/bin/python speedtest_app.py
            ;;
        14)
            echo -e "${GREEN}Iniciando DETECTOR DE CAMBIOS EN RED...${NC}"
            .venv/bin/python network_change_detector.py
            ;;
        15)
            echo -e "${GREEN}Iniciando LOCALIZADOR GEOIP...${NC}"
            .venv/bin/python geoip_locator.py
            ;;
        16)
            echo -e "${GREEN}Iniciando INSPECTOR HTTP...${NC}"
            .venv/bin/python http_inspector.py
            ;;
        17)
            echo -e "${GREEN}Iniciando ANALIZADOR DE VULNERABILIDADES...${NC}"
            .venv/bin/python vuln_port_scanner.py
            ;;
        18)
            echo -e "${GREEN}Iniciando GENERADOR DE CONTRASEÑAS...${NC}"
            .venv/bin/python password_generator.py
            ;;
        19)
            echo -e "${GREEN}Iniciando ANALIZADOR DE SEGURIDAD WEB...${NC}"
            .venv/bin/python web_security_analyzer.py
            ;;
        20)
            echo -e "${GREEN}Iniciando ENUMERADOR DE SUBDOMINIOS...${NC}"
            .venv/bin/python subdomain_enumerator.py
            ;;
        0)
            clear
            echo -e "${GREEN}Iniciando Launcher Gráfico...${NC}"
            sleep 1
            .venv/bin/python launcher.py
            clear
            ;;
        a|A)
            show_about
            ;;
        q|Q)
            clear
            echo -e "${YELLOW}¡Hasta luego!${NC}"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Opción no válida${NC}"
            sleep 2
            ;;
    esac

done
