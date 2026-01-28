"""
Utilidades para manejo de errores y reintentos
"""

import time
import functools
from typing import Callable, Any, Type, Tuple
from logger import bot_logger, log_exception


class BotException(Exception):
    """Excepción base para el bot"""
    pass


class RateLimitException(BotException):
    """Excepción cuando se detecta rate limiting"""
    pass


class LoginRequiredException(BotException):
    """Excepción cuando se requiere login"""
    pass


class ElementNotFoundException(BotException):
    """Excepción cuando no se encuentra un elemento"""
    pass


class ScrapingException(BotException):
    """Excepción general de scraping"""
    pass


def retry_on_exception(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorador para reintentar una función en caso de excepción
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Delay inicial en segundos
        backoff: Factor de multiplicación del delay
        exceptions: Tupla de excepciones a capturar
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        bot_logger.error(
                            f"Función {func.__name__} falló después de {max_attempts} intentos"
                        )
                        raise
                    
                    bot_logger.warning(
                        f"Intento {attempt}/{max_attempts} falló para {func.__name__}: {str(e)}. "
                        f"Reintentando en {current_delay:.1f}s..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default=None, log_errors: bool = True, **kwargs) -> Any:
    """
    Ejecuta una función de forma segura, retornando un valor por defecto en caso de error
    
    Args:
        func: Función a ejecutar
        *args: Argumentos posicionales
        default: Valor por defecto a retornar en caso de error
        log_errors: Si se deben registrar los errores
        **kwargs: Argumentos con nombre
        
    Returns:
        Resultado de la función o valor por defecto
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            log_exception(bot_logger, e, f"Error ejecutando {func.__name__}")
        return default
