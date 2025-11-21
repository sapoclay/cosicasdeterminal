"""
Utilidades multiplataforma para CosicasDeTerminal
Maneja las diferencias entre Linux, Windows y macOS
"""

import platform
import subprocess
import re
from typing import Optional, List, Tuple

def get_platform() -> str:
    """Obtiene el sistema operativo actual"""
    return platform.system().lower()

def is_windows() -> bool:
    """Verifica si es Windows"""
    return get_platform() == "windows"

def is_linux() -> bool:
    """Verifica si es Linux"""
    return get_platform() == "linux"

def is_macos() -> bool:
    """Verifica si es macOS"""
    return get_platform() == "darwin"


# ========== COMANDOS DE RED ==========

def get_ping_command(host: str, count: int = 4) -> List[str]:
    """Obtiene el comando ping según la plataforma"""
    if is_windows():
        return ['ping', '-n', str(count), host]
    else:
        return ['ping', '-c', str(count), host]

def get_ping_fast_command(host: str) -> List[str]:
    """Obtiene comando ping rápido (1 paquete, timeout corto)"""
    if is_windows():
        return ['ping', '-n', '1', '-w', '1000', host]  # -w en milisegundos
    else:
        return ['ping', '-c', '1', '-W', '1', host]

def get_traceroute_command(host: str) -> List[str]:
    """Obtiene el comando traceroute según la plataforma"""
    if is_windows():
        return ['tracert', host]
    else:
        return ['traceroute', host]

def get_arp_command() -> List[str]:
    """Obtiene el comando para ver la tabla ARP"""
    if is_windows():
        return ['arp', '-a']
    else:
        return ['arp', '-n']

def get_arp_mac(ip: str) -> Optional[str]:
    """Obtiene la MAC de una IP desde la tabla ARP"""
    try:
        if is_windows():
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            # Buscar la IP y su MAC en formato Windows
            pattern = rf'{re.escape(ip)}\s+([0-9a-fA-F]{{2}}-[0-9a-fA-F]{{2}}-[0-9a-fA-F]{{2}}-[0-9a-fA-F]{{2}}-[0-9a-fA-F]{{2}}-[0-9a-fA-F]{{2}})'
            match = re.search(pattern, result.stdout)
            if match:
                # Convertir de formato Windows (AA-BB-CC) a formato estándar (AA:BB:CC)
                return match.group(1).replace('-', ':')
        else:
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True)
            match = re.search(r'(([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})', result.stdout)
            if match:
                return match.group(1)
    except:
        pass
    return None



def get_dns_lookup_command(domain: str, record_type: str = "A") -> List[str]:
    """Obtiene el comando para hacer DNS lookup"""
    if is_windows():
        # nslookup funciona en Windows
        if record_type == "PTR":
            return ['nslookup', '-type=PTR', domain]
        else:
            return ['nslookup', '-type=' + record_type, domain]
    else:
        # Preferir dig en Linux/macOS
        try:
            subprocess.run(['which', 'dig'], capture_output=True, check=True)
            return ['dig', '+short', record_type, domain]
        except:
            return ['nslookup', '-type=' + record_type, domain]

def get_netstat_command() -> List[str]:
    """Obtiene el comando netstat según la plataforma"""
    if is_windows():
        return ['netstat', '-ano']
    else:
        return ['netstat', '-tuln']

def get_whois_command(target: str) -> List[str]:
    """Obtiene el comando whois"""
    # whois funciona similar en ambas plataformas si está instalado
    return ['whois', target]

def check_whois_available() -> bool:
    """Verifica si whois está disponible"""
    try:
        if is_windows():
            # En Windows, whois generalmente no viene instalado
            result = subprocess.run(['where', 'whois'], capture_output=True)
            return result.returncode == 0
        else:
            result = subprocess.run(['which', 'whois'], capture_output=True)
            return result.returncode == 0
    except:
        return False


# ========== DETECCIÓN DE FIREWALL ==========

def get_firewall_status() -> Tuple[bool, str]:
    """Obtiene el estado del firewall según la plataforma"""
    try:
        if is_windows():
            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                if 'ON' in result.stdout.upper():
                    return True, "Windows Firewall: Activo"
                else:
                    return True, "Windows Firewall: Inactivo"
            return False, "No se pudo determinar"
        else:
            # Intentar UFW primero
            try:
                result = subprocess.run(
                    ['ufw', 'status'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    if 'active' in result.stdout.lower():
                        return True, "UFW: Activo"
                    else:
                        return True, "UFW: Inactivo"
            except FileNotFoundError:
                pass
            
            # Intentar iptables
            try:
                result = subprocess.run(
                    ['iptables', '-L', '-n'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return True, "iptables: Configurado"
            except (FileNotFoundError, PermissionError):
                pass
            
            return False, "Firewall no detectado"
    except Exception as e:
        return False, f"Error: {str(e)}"


# ========== WIFI (solo funciona en Linux con herramientas específicas) ==========

def wifi_scan_available() -> bool:
    """Verifica si el escaneo WiFi está disponible"""
    if is_windows():
        # En Windows se puede usar netsh wlan
        try:
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                    capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False
    else:
        # En Linux verificar nmcli o iwlist
        try:
            result = subprocess.run(['which', 'nmcli'], capture_output=True)
            if result.returncode == 0:
                return True
            result = subprocess.run(['which', 'iwlist'], capture_output=True)
            return result.returncode == 0
        except:
            return False

def get_wifi_scan_command() -> Optional[List[str]]:
    """Obtiene el comando para escanear WiFi según la plataforma"""
    if is_windows():
        return ['netsh', 'wlan', 'show', 'networks', 'mode=bssid']
    elif is_linux():
        # Intentar nmcli primero
        try:
            result = subprocess.run(['which', 'nmcli'], capture_output=True)
            if result.returncode == 0:
                return ['nmcli', '-f', 'SSID,SIGNAL,CHAN,FREQ,SECURITY,BSSID', 'device', 'wifi', 'list']
        except:
            pass
        
        # Intentar iwlist
        try:
            result = subprocess.run(['which', 'iwlist'], capture_output=True)
            if result.returncode == 0:
                return ['sudo', 'iwlist', 'scan']
        except:
            pass
    
    return None


# ========== UTILIDADES DE FORMATO ==========

def normalize_mac_address(mac: str) -> str:
    """Normaliza dirección MAC al formato estándar AA:BB:CC:DD:EE:FF"""
    # Eliminar separadores y convertir a mayúsculas
    mac_clean = re.sub(r'[:-]', '', mac).upper()
    # Agregar dos puntos cada 2 caracteres
    if len(mac_clean) == 12:
        return ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])
    return mac


# ========== MENSAJES DE AYUDA ==========

def get_installation_help() -> str:
    """Obtiene instrucciones de instalación según la plataforma"""
    if is_windows():
        return """
[yellow]REQUISITOS WINDOWS:[/]

[bold]Python y Dependencias:[/]
  pip install textual psutil netifaces requests speedtest-cli Pillow

[bold]Herramientas Opcionales:[/]
  • Algunas funcionalidades están limitadas en Windows
  • El escaneo WiFi usa comandos nativos de Windows
  • whois no está disponible por defecto (instalar desde sysinternals)

[bold]Limitaciones:[/]
  • Algunas herramientas avanzadas funcionan mejor en Linux
  • El análisis de interfaces está limitado
  • Requiere ejecutar como Administrador para algunas funciones
"""
    elif is_macos():
        return """
[yellow]REQUISITOS macOS:[/]

[bold]Python y Dependencias:[/]
  pip install textual psutil netifaces requests speedtest-cli Pillow

[bold]Herramientas del Sistema:[/]
  brew install whois

[bold]Notas:[/]
  • La mayoría de herramientas de red vienen preinstaladas
  • Algunas funciones pueden requerir permisos de administrador
"""
    else:  # Linux
        return """
[yellow]REQUISITOS LINUX:[/]

[bold]Python y Dependencias:[/]
  pip install textual psutil netifaces requests speedtest-cli Pillow

[bold]Herramientas del Sistema (Debian/Ubuntu):[/]
  sudo apt-get install iputils-ping net-tools traceroute whois dnsutils

[bold]Fedora/RHEL:[/]
  sudo dnf install iputils traceroute whois bind-utils

[bold]Arch Linux:[/]
  sudo pacman -S iputils traceroute whois bind-tools
"""


def get_platform_name() -> str:
    """Obtiene el nombre descriptivo de la plataforma"""
    system = platform.system()
    release = platform.release()
    
    if is_windows():
        return f"Windows {release}"
    elif is_linux():
        try:
            import distro  # type: ignore
            return f"{distro.name()} {distro.version()}"
        except (ImportError, Exception):
            return f"Linux {release}"
    elif is_macos():
        return f"macOS {release}"
    else:
        return f"{system} {release}"


def get_route_command() -> list:
    """Obtiene el comando para mostrar la tabla de enrutamiento"""
    if is_windows():
        return ['route', 'print']
    elif is_macos():
        return ['netstat', '-nr']
    else:  # Linux
        return ['ip', 'route', 'show']


def get_dns_servers() -> list:
    """Obtiene los servidores DNS configurados de forma multiplataforma"""
    dns_servers = []
    
    if is_windows():
        try:
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'DNS' in line and ':' in line:
                    dns = line.split(':')[1].strip()
                    if dns and dns[0].isdigit():
                        dns_servers.append(dns)
        except:
            pass
    else:  # Linux/macOS
        try:
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('nameserver'):
                        dns = line.split()[1]
                        dns_servers.append(dns)
        except:
            pass
    
    return dns_servers if dns_servers else ['No configurados']


def get_network_interfaces_command() -> list:
    """Obtiene el comando para listar interfaces de red"""
    if is_windows():
        return ['ipconfig', '/all']
    elif is_macos():
        return ['ifconfig']
    else:  # Linux
        return ['ip', 'link', 'show']


def check_vpn_interface() -> tuple[bool, str]:
    """Detecta interfaces VPN de forma multiplataforma"""
    try:
        if is_windows():
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True,
                text=True,
                timeout=2
            )
            output = result.stdout.lower()
            if 'vpn' in output or 'tap-windows' in output:
                return True, "Posible interfaz VPN detectada"
        else:  # Linux/macOS
            result = subprocess.run(
                ['ip', 'link', 'show'] if is_linux() else ['ifconfig'],
                capture_output=True,
                text=True,
                timeout=2
            )
            output = result.stdout.lower()
            if 'tun' in output or 'tap' in output:
                return True, "Posible interfaz VPN detectada (tun/tap)"
        
        return False, "No se detectaron interfaces VPN"
    except:
        return False, "No se pudo verificar VPN"
