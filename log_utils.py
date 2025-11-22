"""
Utilidades para búsqueda y lectura de archivos de logs
"""

import os
import platform
from pathlib import Path
from typing import List, Dict, Optional
import mimetypes


def get_platform_log_paths() -> List[Path]:
    """Obtiene las rutas de logs según el sistema operativo"""
    system = platform.system().lower()
    log_paths = []
    
    if system == "linux":
        # Rutas comunes en Linux
        common_paths = [
            "/var/log",
            "/var/log/syslog",
            "/var/log/auth.log",
            "/var/log/apache2",
            "/var/log/nginx",
            "/var/log/mysql",
            "/var/log/postgresql",
            "~/.local/share",
        ]
        
    elif system == "windows":
        # Rutas comunes en Windows
        common_paths = [
            "C:/Windows/Logs",
            "C:/ProgramData",
            "C:/Windows/System32/LogFiles",
            os.path.expandvars("%LOCALAPPDATA%"),
            os.path.expandvars("%APPDATA%"),
        ]
        
    elif system == "darwin":  # macOS
        # Rutas comunes en macOS
        common_paths = [
            "/var/log",
            "/Library/Logs",
            "~/Library/Logs",
            "/private/var/log",
        ]
    else:
        common_paths = []
    
    # Expandir rutas y verificar que existan
    for path_str in common_paths:
        try:
            path = Path(path_str).expanduser()
            if path.exists():
                log_paths.append(path)
        except:
            continue
    
    # Agregar directorio actual como opción adicional
    current_dir = Path.cwd()
    if current_dir not in log_paths:
        log_paths.append(current_dir)
    
    return log_paths


def is_log_file(filepath: Path) -> bool:
    """Determina si un archivo es un log basándose en la extensión y contenido"""
    # Extensiones comunes de logs (sin .txt para evitar archivos Python)
    log_extensions = {'.log', '.out', '.err', '.trace'}
    
    # Verificar extensión de log específica
    if filepath.suffix.lower() in log_extensions:
        return True
    
    # Verificar archivos sin extensión que parecen logs (solo nombres exactos)
    common_log_names = {'syslog', 'messages', 'auth', 'kern', 'dmesg', 'error', 'access', 'debug'}
    if filepath.name.lower() in common_log_names:
        return True
    
    # Archivos numerados de rotación (*.log.1, *.log.2, etc)
    if '.log.' in filepath.name.lower():
        return True
    
    return False


def scan_log_files(directory: Path, max_depth: int = 3, current_depth: int = 0) -> List[Dict]:
    """
    Escanea recursivamente un directorio en busca de archivos de logs
    
    Returns:
        Lista de diccionarios con información de cada log encontrado
    """
    log_files = []
    
    if not directory.exists() or not directory.is_dir():
        return log_files
    
    if current_depth >= max_depth:
        return log_files
    
    try:
        for item in directory.iterdir():
            try:
                # Omitir enlaces simbólicos para evitar loops
                if item.is_symlink():
                    continue
                
                if item.is_file() and is_log_file(item):
                    try:
                        stat = item.stat()
                        log_files.append({
                            'path': item,
                            'name': item.name,
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'readable': os.access(item, os.R_OK)
                        })
                    except (PermissionError, OSError):
                        # Agregar el archivo aunque no tengamos todos los detalles
                        log_files.append({
                            'path': item,
                            'name': item.name,
                            'size': 0,
                            'modified': 0,
                            'readable': False
                        })
                
                elif item.is_dir():
                    # Recursión en subdirectorios
                    log_files.extend(scan_log_files(item, max_depth, current_depth + 1))
                    
            except (PermissionError, OSError):
                # Ignorar directorios/archivos sin permisos
                continue
                
    except (PermissionError, OSError):
        pass
    
    return log_files


def read_log_file(filepath: Path, max_lines: int = 1000, tail: bool = True) -> tuple[List[str], bool]:
    """
    Lee un archivo de log de forma segura
    
    Args:
        filepath: Ruta al archivo
        max_lines: Máximo número de líneas a leer
        tail: Si True, lee las últimas líneas; si False, las primeras
    
    Returns:
        (líneas leídas, archivo_truncado)
    """
    if not filepath.exists() or not filepath.is_file():
        return (["Error: El archivo no existe"], True)
    
    try:
        # Intentar detectar la codificación
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        lines = []
        
        truncated = False
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                    if tail:
                        # Leer todas las líneas y tomar las últimas
                        all_lines = f.readlines()
                        if len(all_lines) > max_lines:
                            lines = all_lines[-max_lines:]
                            truncated = True
                        else:
                            lines = all_lines
                            truncated = False
                    else:
                        # Leer solo las primeras líneas
                        lines = []
                        for i, line in enumerate(f):
                            if i >= max_lines:
                                truncated = True
                                break
                            lines.append(line)
                        else:
                            truncated = False
                
                # Si llegamos aquí, la codificación funcionó
                break
                
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Limpiar las líneas (remover \n al final)
        lines = [line.rstrip('\n\r') for line in lines]
        
        return (lines, truncated)
        
    except PermissionError:
        return (["Error: Sin permisos para leer el archivo"], True)
    except Exception as e:
        return ([f"Error al leer el archivo: {str(e)}"], True)


def search_in_log(lines: List[str], query: str, case_sensitive: bool = False) -> List[tuple[int, str]]:
    """
    Busca un término en las líneas del log
    
    Returns:
        Lista de tuplas (número_línea, línea_completa)
    """
    if not query:
        return [(i, line) for i, line in enumerate(lines)]
    
    results = []
    search_query = query if case_sensitive else query.lower()
    
    for i, line in enumerate(lines):
        search_line = line if case_sensitive else line.lower()
        if search_query in search_line:
            results.append((i, line))
    
    return results


def format_file_size(size_bytes: int) -> str:
    """Formatea el tamaño de archivo en formato legible"""
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_log_summary(filepath: Path) -> Dict:
    """Obtiene un resumen rápido de un archivo de log"""
    try:
        stat = filepath.stat()
        
        # Contar líneas (de forma eficiente)
        line_count = 0
        try:
            with open(filepath, 'rb') as f:
                line_count = sum(1 for _ in f)
        except:
            line_count = -1
        
        return {
            'path': filepath,
            'name': filepath.name,
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'modified': stat.st_mtime,
            'lines': line_count,
            'readable': os.access(filepath, os.R_OK)
        }
    except Exception as e:
        return {
            'path': filepath,
            'name': filepath.name,
            'error': str(e)
        }
