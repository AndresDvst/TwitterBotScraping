"""
Script de verificación de configuración del bot
Ejecuta este script para verificar que todo esté correctamente instalado
"""

import sys
import os

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    print("=" * 60)
    print("VERIFICACIÓN DE DEPENDENCIAS")
    print("=" * 60)
    
    dependencias = {
        'selenium': 'selenium',
        'webdriver_manager': 'webdriver-manager',
        'dotenv': 'python-dotenv',
        'rich': 'rich',
        'click': 'click',
        'pydantic': 'pydantic',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'numpy': 'numpy'
    }
    
    faltantes = []
    instaladas = []
    
    for modulo, paquete in dependencias.items():
        try:
            __import__(modulo)
            instaladas.append(f"✓ {paquete}")
        except ImportError:
            faltantes.append(f"✗ {paquete}")
    
    print("\n📦 Dependencias instaladas:")
    for dep in instaladas:
        print(f"  {dep}")
    
    if faltantes:
        print("\n⚠ Dependencias faltantes:")
        for dep in faltantes:
            print(f"  {dep}")
        print("\n💡 Para instalar las faltantes, ejecuta:")
        print("  pip install " + " ".join([d.split()[1] for d in faltantes]))
        return False
    else:
        print("\n✅ Todas las dependencias están instaladas!")
        return True


def verificar_archivos():
    """Verifica que los archivos necesarios existan"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE ARCHIVOS")
    print("=" * 60)
    
    archivos_requeridos = [
        'config.py',
        'logger.py',
        'utils.py',
        'backup.py',
        'checkpoint.py',
        'manager.py',
        'scraper.py',
        'bot.py',
        'requirements.txt',
        '.env.example'
    ]
    
    faltantes = []
    existentes = []
    
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            existentes.append(f"✓ {archivo}")
        else:
            faltantes.append(f"✗ {archivo}")
    
    print("\n📄 Archivos encontrados:")
    for arch in existentes:
        print(f"  {arch}")
    
    if faltantes:
        print("\n⚠ Archivos faltantes:")
        for arch in faltantes:
            print(f"  {arch}")
        return False
    else:
        print("\n✅ Todos los archivos necesarios existen!")
        return True


def verificar_configuracion():
    """Verifica la configuración"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN")
    print("=" * 60)
    
    try:
        from config import Config
        
        print("\n⚙️ Configuración cargada:")
        print(f"  - Data dir: {Config.DATA_DIR}")
        print(f"  - Log level: {Config.LOG_LEVEL}")
        print(f"  - Headless: {Config.HEADLESS_MODE}")
        print(f"  - Usuarios por pasada: {Config.USUARIOS_POR_PASADA}")
        print(f"  - Likes por pasada: {Config.LIKES_POR_PASADA}")
        print(f"  - Max likes/hora: {Config.MAX_LIKES_PER_HOUR}")
        
        # Verificar si existe .env
        if os.path.exists('.env'):
            print("\n✓ Archivo .env encontrado")
        else:
            print("\n⚠ Archivo .env NO encontrado (usando valores por defecto)")
            print("  💡 Copia .env.example a .env para personalizar la configuración")
        
        print("\n✅ Configuración válida!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error cargando configuración: {e}")
        return False


def verificar_logging():
    """Verifica el sistema de logging"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE LOGGING")
    print("=" * 60)
    
    try:
        from logger import bot_logger
        
        # Crear directorio de logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        # Probar logging
        bot_logger.info("✓ Sistema de logging funcionando correctamente")
        
        print("\n✅ Sistema de logging OK!")
        print(f"  - Logs se guardarán en: logs/bot.log")
        return True
        
    except Exception as e:
        print(f"\n✗ Error en sistema de logging: {e}")
        return False


def verificar_directorios():
    """Verifica y crea directorios necesarios"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE DIRECTORIOS")
    print("=" * 60)
    
    directorios = ['data', 'logs', 'backups']
    
    for directorio in directorios:
        if not os.path.exists(directorio):
            os.makedirs(directorio)
            print(f"  ✓ Creado: {directorio}/")
        else:
            print(f"  ✓ Existe: {directorio}/")
    
    print("\n✅ Directorios verificados!")
    return True


def main():
    """Función principal"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DEL SISTEMA - TWITTER BOT")
    print("=" * 60)
    
    resultados = []
    
    # Verificar dependencias
    resultados.append(("Dependencias", verificar_dependencias()))
    
    # Verificar archivos
    resultados.append(("Archivos", verificar_archivos()))
    
    # Verificar configuración
    resultados.append(("Configuración", verificar_configuracion()))
    
    # Verificar logging
    resultados.append(("Logging", verificar_logging()))
    
    # Verificar directorios
    resultados.append(("Directorios", verificar_directorios()))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    todo_ok = True
    for nombre, resultado in resultados:
        estado = "✅ OK" if resultado else "❌ FALLO"
        print(f"  {nombre}: {estado}")
        if not resultado:
            todo_ok = False
    
    print("\n" + "=" * 60)
    
    if todo_ok:
        print("🎉 ¡TODO ESTÁ LISTO!")
        print("\nPuedes ejecutar el bot con:")
        print("  python bot.py")
    else:
        print("⚠️ HAY PROBLEMAS QUE RESOLVER")
        print("\nRevisa los errores arriba y:")
        print("  1. Instala las dependencias faltantes")
        print("  2. Verifica que todos los archivos existan")
        print("  3. Configura el archivo .env")
    
    print("=" * 60 + "\n")
    
    return 0 if todo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
