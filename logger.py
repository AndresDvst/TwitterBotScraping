"""
Sistema de logging profesional para el Twitter Bot
Proporciona logging a archivo y consola con rotación automática
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import Config

class ColoredFormatter(logging.Formatter):
    """Formatter con colores para consola"""
    
    # Códigos ANSI de colores
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Agregar color al nivel de log
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logger(name: str = 'TwitterBot') -> logging.Logger:
    """
    Configura y retorna un logger con handlers para archivo y consola
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers si ya está configurado
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # ==================== HANDLER DE ARCHIVO ====================
    # Crear directorio de logs si no existe
    log_path = Path(Config.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # ==================== HANDLER DE CONSOLA ====================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    console_formatter = ColoredFormatter(
        '%(levelname)-8s | %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Logger global para el bot
bot_logger = setup_logger('TwitterBot')


def log_exception(logger: logging.Logger, exc: Exception, context: str = ""):
    """
    Registra una excepción con contexto completo
    
    Args:
        logger: Logger a usar
        exc: Excepción capturada
        context: Contexto adicional
    """
    import traceback
    
    error_msg = f"{context}\n" if context else ""
    error_msg += f"Tipo: {type(exc).__name__}\n"
    error_msg += f"Mensaje: {str(exc)}\n"
    error_msg += f"Traceback:\n{''.join(traceback.format_tb(exc.__traceback__))}"
    
    logger.error(error_msg)


# Ejemplo de uso
if __name__ == "__main__":
    logger = setup_logger()
    
    logger.debug("Mensaje de debug")
    logger.info("Mensaje informativo")
    logger.warning("Advertencia")
    logger.error("Error")
    logger.critical("Crítico")
    
    try:
        1 / 0
    except Exception as e:
        log_exception(logger, e, "Error de prueba")
