# 🌐 CosicasDeTerminal

<img width="1024" height="1024" alt="CosicasDeTerminal" src="https://github.com/user-attachments/assets/6718286a-5ba7-4896-a430-6d4928eb89e9" />

Esta es una pequeña suite, que por el momento incluye 25 herramientas interactivas para diagnóstico de red y seguridad. Todo esto se ha desarrollado con [Textual](https://textual.textualize.io/) y Python.

**✨ Compatible con Windows, Linux y a lo mejor con macOS**

## Inicio rápido

```bash
# Instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 🚀 Inicio Rápido (Multiplataforma)

La forma recomendada de iniciar la aplicación en **Linux, Windows y macOS** es:

```bash
python3 start.py
```

## 📦 Herramientas incluidas 📦

### Análisis de red
1. **Escáner de red** - Descubre dispositivos en tu red local (IP, MAC, hostname)
2. **Monitor de red** - Tráfico en tiempo real y conexiones activas
3. **Diagnóstico** - Ping, Traceroute, DNS, Port Scanner, Whois, Mi IP
4. **Verificador de conectividad** - Comprueba conectividad, DNS, latencia y detecta proxy/VPN
5. **Monitor de interfaces** - Información detallada de todas las interfaces de red
6. **Escáner de puertos locales** - Detecta puertos en escucha e identifica procesos
7. **Analizador WIFI** - Escanea redes WiFi con señal, canal y seguridad
8. **Monitor de uso de red** - Monitoreo en tiempo real de uso de red por proceso
9. **Info del sistema de red** - Configuración completa del sistema de red

### Herramientas avanzadas
10. **Calculadora IP Universal** - IPv4/IPv6, CIDR, rangos, división y formatos
11. **DNS avanzado** - Consultas A, AAAA, MX, NS, SOA, TXT y Reverse DNS
12. **Verificador SSL/TLS** - Análisis de certificados, caducidad y seguridad
13. **Test de velocidad** - Mide velocidad de bajada, subida y ping
14. **Detector de cambios** - Monitoriza la red y avisa de nuevos dispositivos
15. **Localizador GeoIP** - Geolocalización de IPs y dominios en mapa
16. **Inspector HTTP** - Analiza cabeceras, métodos y respuestas de APIs
17. **Analizador de Paquetes** - Sniffer de tráfico en tiempo real (requiere root) HTTP/HTTPS

### Seguridad
21. **Enumerador de subdominios** - Descubre subdominios vía certificados y DNS

### Diagnóstico y Privacidad
22. **Verificador de fugas** - Detecta fugas DNS, IPv6, WebRTC y verifica VPN
23. **Troubleshooter** - Diagnóstico automático de problemas con soluciones
24. **Monitor de latencia geográfica** - Prueba latencia a regiones del mundo
25. **Visor de logs** - Visualiza logs en terminal (compatible con SSH/Windows/Linux)
26. **Wake on LAN** - Enciende equipos remotamente mediante paquetes mágicos
27. **Gestor de Conexiones** - Gestiona conexiones SSH, FTP y SFTP rápidamente

## 🔧 Requisitos

**Python:**
- Python 3.10+
- textual, psutil, netifaces, requests, speedtest-cli, Pillow

**Sistema:**

*Linux (Debian/Ubuntu):*
```bash
sudo apt-get install iputils-ping net-tools traceroute whois dnsutils
```

*Windows:*
```powershell
# La mayoría de herramientas vienen incluidas con Windows
# Whois opcional: Descargar Sysinternals Whois
```

*macOS:*
```bash
# La mayoría de herramientas vienen preinstaladas
brew install whois  # Si es necesario
```

## 💻 Uso

```bash
python3 start.py              # Menú CLI
python3 launcher.py      # Menú gráfico (recomendado)
```

## ⚡ Atajos

- `q` - Salir
- `Ctrl+C` - Salir inmediato
- Usa las teclas numéricas o clics en los botones

## ⚠️ Notas

- Algunas herramientas requieren `sudo` para funcionalidad completa
- Solo para uso legítimo en redes propias
- Los escaneos se limitan a redes /24 por defecto

---

**Creado por entreunosyceros usando Python, Textual y un poco de café**
