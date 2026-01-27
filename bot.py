#!/usr/bin/env python3
"""
Bot de gestión de usuarios de Twitter
Funcionalidades:
1. Entregar 10 usuarios aleatorios sin repetir en 3 días
2. Scrapear feed de Twitter cada 10 min por 1 hora
3. Agregar usuarios al JSON principal
4. Detectar y registrar repetidos
"""

from manager import UsuariosManager
from scraper import TwitterScraper
import sys

def mostrar_menu():
    """Muestra el menú principal"""
    print("\n" + "="*50)
    print("BOT DE GESTIÓN DE USUARIOS DE TWITTER")
    print("="*50)
    print("\n1. Modificar JSON de login (usuarios aleatorios)")
    print("2. Iniciar scraping automático (1 hora, cada 10 min)")
    print("3. Scraping manual (una sola pasada)")
    print("4. Ver estadísticas")
    print("5. Limpiar historial antiguo (>30 días)")
    print("6. Salir")
    print("\n" + "="*50)

def obtener_usuarios_aleatorios():
    """Opción 1: Obtener 10 usuarios"""
    manager = UsuariosManager()
    usuarios = manager.obtener_10_usuarios()
    
    print("\n" + "="*50)
    print("USUARIOS SELECCIONADOS:")
    print("="*50)
    
    if usuarios:
        for i, usuario in enumerate(usuarios, 1):
            print(f"{i}. @{usuario}")
    else:
        print("⚠ No hay usuarios disponibles que no se hayan usado en los últimos 3 días")
    
    print("="*50 + "\n")

def modificar_json_login():
    """Opción 1: Modificar Twitter Bot Scraping\\login.json con 40 usuarios aleatorios"""
    import os
    manager = UsuariosManager()
    try:
        usuarios_fuente = manager.cargar_usuarios_base()
        destino_login = r"Twitter Bot Scraping\login.json"
        manager.modificar_login_json(usuarios_fuente=usuarios_fuente, destino=destino_login, total_usuarios=40)
        print("\n✓ login.json actualizado con 40 usuarios aleatorios distribuidos en aurora/emily/eva/gaby")
    except Exception as e:
        print(f"\n✗ Error modificando login.json: {e}")

def iniciar_scraping_automatico():
    """Opción 2: Scraping automático durante 1 hora"""
    print("\n⚠ IMPORTANTE:")
    print("  - Debes estar LOGUEADO en Twitter en tu navegador")
    print("  - El bot abrirá Chrome y navegará a tu feed")
    print("  - Durará 1 hora con pasadas cada 10 minutos")
    print("  - Dará 10 likes por pasada para evitar detección 💙")
    
    confirmacion = input("\n¿Continuar? (s/n): ").lower()
    
    if confirmacion != 's':
        print("Operación cancelada")
        return
    
    import time
    scraper = TwitterScraper(headless=False)
    
    try:
        scraper.iniciar_navegador()
        
        print("\n⏸ PAUSA: El navegador está abierto.")
        print("Esperando 3 segundos antes de navegar a X...")
        time.sleep(3)
        
        # Navegar a X
        scraper.ir_a_twitter("https://x.com/home")
        
        print("\n⏸ PAUSA: Por favor, LOGUEATE en Twitter/X manualmente si es necesario")
        print("Presiona ENTER cuando estés logueado y en tu feed...")
        input()
        
        # Iniciar scraping automático con likes
        scraper.mantener_sesion_activa(
            minutos=60,
            intervalo_minutos=10,
            usuarios_por_pasada=10,
            likes_por_pasada=10
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        scraper.cerrar()

def scraping_manual():
    """Opción 3: Una sola pasada de scraping"""
    import time
    scraper = TwitterScraper(headless=False)
    manager = UsuariosManager()
    
    try:
        scraper.iniciar_navegador()
        
        print("\n⏸ PAUSA: El navegador está abierto.")
        print("Esperando 3 segundos antes de navegar a X...")
        time.sleep(3)
        
        # Navegar a X
        scraper.ir_a_twitter("https://x.com/home")
        
        print("\n⏸ PAUSA: Por favor, LOGUEATE en Twitter/X manualmente si es necesario")
        print("Presiona ENTER cuando estés listo...")
        input()
        
        # Hacer una pasada (ahora retorna tupla)
        usuarios, likes_dados = scraper.scrapear_feed(
            scrolls=10,  # 10 scrolls para cargar más contenido
            usuarios_objetivo=10,
            dar_likes_activo=True,
            likes_objetivo=10
        )
        
        # Agregar al manager
        agregados = manager.agregar_nuevos_usuarios(usuarios)
        
        print(f"\n📊 Resultados:")
        print(f"  - Usuarios encontrados: {len(usuarios)}")
        print(f"  - Usuarios nuevos: {len(agregados)}")
        print(f"  - Repetidos: {len(usuarios) - len(agregados)}")
        print(f"  - Likes dados: {likes_dados} 💙")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        scraper.cerrar()

def ver_estadisticas():
    """Opción 4: Mostrar estadísticas"""
    manager = UsuariosManager()
    stats = manager.obtener_estadisticas()
    
    print("\n" + "="*50)
    print("ESTADÍSTICAS DEL SISTEMA")
    print("="*50)
    print(f"Total usuarios en base principal: {stats['total_principales']}")
    print(f"Total en historial (últimos 30 días): {stats['total_historial']}")
    print(f"Total usuarios repetidos detectados: {stats['total_repetidos']}")
    print(f"Total en base inicial: {stats['total_base']}")
    print("="*50 + "\n")

def limpiar_historial():
    """Opción 5: Limpiar historial antiguo"""
    manager = UsuariosManager()
    eliminados = manager.limpiar_historial_antiguo(dias=30)
    
    print(f"\n✓ Se eliminaron {eliminados} entradas del historial (>30 días)")

def main():
    """Función principal"""
    while True:
        mostrar_menu()
        
        try:
            opcion = input("Selecciona una opción: ").strip()
            
            if opcion == '1':
                modificar_json_login()
            elif opcion == '2':
                iniciar_scraping_automatico()
            elif opcion == '3':
                scraping_manual()
            elif opcion == '4':
                ver_estadisticas()
            elif opcion == '5':
                limpiar_historial()
            elif opcion == '6':
                print("\n¡Hasta luego! 👋\n")
                sys.exit(0)
            else:
                print("\n⚠ Opción inválida. Intenta de nuevo.")
                
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego! 👋\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ Error inesperado: {e}\n")

if __name__ == "__main__":
    main()
