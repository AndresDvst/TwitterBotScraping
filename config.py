"""
Módulo de configuración centralizada para el Twitter Bot
Carga variables de entorno desde .env y proporciona valores por defecto
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()

class Config:
    """Configuración centralizada del bot"""
    
    # ==================== RUTAS ====================
    CHROMEDRIVER_PATH: str = os.getenv(
        'CHROMEDRIVER_PATH',
        str(PROJECT_ROOT / 'chrome-win' / 'chromedriver.exe')
    )
    
    CHROME_BINARY_PATH: str = os.getenv(
        'CHROME_BINARY_PATH',
        str(PROJECT_ROOT / 'chrome-win' / 'chrome.exe')
    )
    
    CHROME_PROFILE_DIR: str = os.getenv(
        'CHROME_PROFILE_DIR',
        str(PROJECT_ROOT / 'chrome_profile')
    )
    
    DATA_DIR: str = os.getenv(
        'DATA_DIR',
        str(PROJECT_ROOT / 'data')
    )
    
    LOGIN_JSON_PATH: str = os.getenv(
        'LOGIN_JSON_PATH',
        r'I:\Archivos\login.json'
    )
    
    # ==================== SCRAPING ====================
    HEADLESS_MODE: bool = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    SCROLL_COUNT: int = int(os.getenv('SCROLL_COUNT', '10'))
    USUARIOS_POR_PASADA: int = int(os.getenv('USUARIOS_POR_PASADA', '10'))
    LIKES_POR_PASADA: int = int(os.getenv('LIKES_POR_PASADA', '10'))
    INTERVALO_MINUTOS: int = int(os.getenv('INTERVALO_MINUTOS', '10'))
    DURACION_TOTAL_MINUTOS: int = int(os.getenv('DURACION_TOTAL_MINUTOS', '60'))
    
    # ==================== ANTI-DETECCIÓN ====================
    MIN_PAUSE_SECONDS: float = float(os.getenv('MIN_PAUSE_SECONDS', '2.0'))
    MAX_PAUSE_SECONDS: float = float(os.getenv('MAX_PAUSE_SECONDS', '5.0'))
    MIN_SCROLL_DISTANCE: int = int(os.getenv('MIN_SCROLL_DISTANCE', '600'))
    MAX_SCROLL_DISTANCE: int = int(os.getenv('MAX_SCROLL_DISTANCE', '1000'))
    MIN_POST_LIKE_WAIT: float = float(os.getenv('MIN_POST_LIKE_WAIT', '5.0'))
    MAX_POST_LIKE_WAIT: float = float(os.getenv('MAX_POST_LIKE_WAIT', '8.0'))
    MIN_SALTOS: int = int(os.getenv('MIN_SALTOS', '2'))
    MAX_SALTOS: int = int(os.getenv('MAX_SALTOS', '6'))
    
    # ==================== LÍMITES DE SEGURIDAD ====================
    MAX_LIKES_PER_HOUR: int = int(os.getenv('MAX_LIKES_PER_HOUR', '50'))
    MAX_LIKES_PER_DAY: int = int(os.getenv('MAX_LIKES_PER_DAY', '200'))
    DIAS_HISTORIAL_LIMPIEZA: int = int(os.getenv('DIAS_HISTORIAL_LIMPIEZA', '30'))
    
    # ==================== LOGGING ====================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', str(PROJECT_ROOT / 'logs' / 'bot.log'))
    LOG_MAX_BYTES: int = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # ==================== BACKUPS ====================
    BACKUP_ENABLED: bool = os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_DIR: str = os.getenv('BACKUP_DIR', str(PROJECT_ROOT / 'backups'))
    MAX_BACKUPS: int = int(os.getenv('MAX_BACKUPS', '10'))
    
    # ==================== USER AGENTS ====================
    USER_AGENTS: List[str] = os.getenv(
        'USER_AGENTS',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36,'
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36,'
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ).split(',')
    
    @classmethod
    def validate(cls) -> bool:
        """Valida que las rutas críticas existan"""
        # Crear directorios si no existen
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
        
        if cls.BACKUP_ENABLED:
            os.makedirs(cls.BACKUP_DIR, exist_ok=True)
        
        return True
    
    @classmethod
    def get_random_user_agent(cls) -> str:
        """Retorna un User-Agent aleatorio"""
        import random
        return random.choice(cls.USER_AGENTS).strip()


# Validar configuración al importar
Config.validate()
