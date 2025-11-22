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

# Ejecutar
chmod +x start.sh
./start.sh
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
10. **Calculadora de subredes** - CIDR, máscaras, división de redes
11. **DNS avanzado** - Consulta registros A, AAAA, MX, TXT, NS, SOA, PTR
12. **Verificador SSL/TLS** - Valida certificados y cadenas de confianza
13. **Test de velocidad** - Speedtest con historial
14. **Detector de cambios** - Alertas cuando dispositivos se conectan/desconectan
15. **Localizador GEOIP** - Geolocalización de IPs y dominios
16. **Inspector HTTP** - Prueba APIs y analiza headers HTTP/HTTPS

### Seguridad
17. **Escáner de vulnerabilidades** - Detecta puertos y configuraciones inseguras
18. **Generador de contraseñas** - Genera y analiza contraseñas seguras
19. **Analizador de seguridad web** - Evalúa headers de seguridad (HSTS, CSP, etc.)
20. **Ancho de banda** - Monitorea qué procesos usan la red
21. **Enumerador de subdominios** - Descubre subdominios vía certificados y DNS

### Diagnóstico y Privacidad
22. **Verificador de fugas** - Detecta fugas DNS, IPv6, WebRTC y verifica VPN
23. **Troubleshooter** - Diagnóstico automático de problemas con soluciones
24. **Monitor de latencia geográfica** - Prueba latencia a regiones del mundo
25. **Visor de logs** - Visualiza logs en terminal (compatible con SSH/Windows/Linux)

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
./start.sh              # Menú CLI
python launcher.py      # Menú gráfico (recomendado)
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
