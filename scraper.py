from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # Importar Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException
import time
import random
from typing import List, Set

class TwitterScraper:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        
    def iniciar_navegador(self):
        """Inicia el navegador Chrome/Chromium con perfil persistente"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Directorio de perfil de usuario para mantener la sesión
        import os
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Configurar perfil persistente
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        chrome_options.add_argument('--profile-directory=Default')
        
        # Opciones adicionales
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-session-crashed-bubble') # Evitar "Restaurar sesión"
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--new-window')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--remote-allow-origins=*')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--v=0')
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # Iniciar maximizado para asegurar viewport consistente
        chrome_options.add_argument("--start-maximized")
        
        # Usar Chrome portable si existe
        chrome_binary = os.path.join(os.getcwd(), "chrome-win", "chrome.exe")
        if os.path.exists(chrome_binary):
            chrome_options.binary_location = chrome_binary
        
        # Ruta al chromedriver personalizado
        from selenium.webdriver.chrome.service import Service
        import subprocess
        
        chromedriver_path = r"I:\Proyectos\Twitter Bot Scraping\chrome-win\chromedriver.exe"
        
        # Verificar que existe
        if not os.path.exists(chromedriver_path):
            print(f"⚠ Error: No se encontró chromedriver en {chromedriver_path}")
            raise FileNotFoundError(f"ChromeDriver no encontrado en {chromedriver_path}")
        
        service = Service(executable_path=chromedriver_path, log_output=subprocess.DEVNULL)
        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except SessionNotCreatedException as e:
            try:
                print("⚠ Falló el ChromeDriver local. Probando con webdriver-manager...")
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e2:
                raise e2
        
        # Maximizar ventana
        self.driver.maximize_window()
        
        print(f"✓ Usando chromedriver de: {chromedriver_path}")
        print(f"✓ Perfil de usuario guardado en: {user_data_dir}")
        print("✓ Navegador iniciado")
        
    def ir_a_twitter(self, url="https://x.com/home"):
        """Navega a Twitter/X - requiere sesión activa"""
        if not self.driver:
            self.iniciar_navegador()
        
        # Asegurar que sólo haya una ventana/tabs abierta limpia
        self.asegurar_ventana_unica()
        
        print(f"🌐 Navegando a {url}...")
        self.driver.get(url)
        print(f"✓ Página cargada")
        time.sleep(7)  # Esperar carga inicial más tiempo
    
    def asegurar_ventana_unica(self):
        """Cierra pestañas/ventanas restauradas y abre una nueva ventana limpia"""
        try:
            if not self.driver:
                return
            handles = self.driver.window_handles
            if len(handles) > 1:
                # Abrir una ventana NUEVA y luego cerrar todas las anteriores
                self.driver.switch_to.new_window('window')
                nueva = self.driver.current_window_handle
                for h in handles:
                    try:
                        self.driver.switch_to.window(h)
                        self.driver.close()
                    except:
                        pass
                # Volver a la nueva ventana limpia
                self.driver.switch_to.window(nueva)
                try:
                    self.driver.maximize_window()
                except:
                    pass
        except:
            pass
        
    def hacer_scroll(self, scrolls=3, pausa_entre_scrolls=2):
        """Realiza scroll en el feed con comportamiento más humano"""
        print(f"Iniciando {scrolls} scrolls...")
        
        for i in range(scrolls):
            # Scroll con distancia variable (más humano)
            distancia = random.randint(600, 1000)
            self.driver.execute_script(f"window.scrollBy(0, {distancia});")
            
            # Pausa variable entre scrolls
            pausa = random.uniform(pausa_entre_scrolls * 0.8, pausa_entre_scrolls * 1.2)
            time.sleep(pausa)
            print(f"  Scroll {i+1}/{scrolls} ({distancia}px)")
    
    def extraer_y_dar_likes_inteligente(self, cantidad=10) -> tuple:
        """
        Extrae usuarios y da likes de forma más humana:
        1. Encuentra un tweet
        2. Extrae el usuario
        3. Da like al tweet de ese usuario
        4. Espera 5 seg
        5. Salta 2-6 publicaciones usando LÓGICA DE ELEMENTOS (más precisa)
        6. Repite
        """
        usuarios_extraidos = []
        likes_dados = 0
        
        print(f"\n🤖 Iniciando extracción inteligente (objetivo: {cantidad} usuarios con likes)...")
        
        try:
            # Hacer scroll inicial para cargar tweets
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
            
            # Selectores para tweets completos
            selectores_tweets = [
                "//article[@data-testid='tweet']",
                "//div[@data-testid='cellInnerDiv']//article"
            ]
            
            # Conjunto de IDs de tweets ya procesados o saltados
            # Usaremos el link permanente del tweet como ID único si es posible, o una firma del contenido
            tweets_procesados = set()
            
            intentos = 0
            max_intentos = cantidad * 4
            
            while likes_dados < cantidad and intentos < max_intentos:
                intentos += 1
                like_dado_en_este_ciclo = False
                
                # 1. Obtener TODOS los tweets visibles en el DOM actual
                tweets_visibles = []
                for selector in selectores_tweets:
                    try:
                        elementos = self.driver.find_elements(By.XPATH, selector)
                        if elementos:
                            tweets_visibles = elementos
                            break
                    except:
                        continue
                
                if not tweets_visibles:
                    print("  ⚠ No se encontraron tweets, haciendo scroll...")
                    self.driver.execute_script("window.scrollBy(0, 800);")
                    time.sleep(2)
                    continue
                
                # 2. Filtrar tweets que ya hemos procesado
                tweets_candidatos = []
                for tweet in tweets_visibles:
                    try:
                        # Intentar obtener ID único (URL del status)
                        links_status = tweet.find_elements(By.XPATH, ".//a[contains(@href, '/status/')]")
                        tweet_id = None
                        for link in links_status:
                            href = link.get_attribute('href')
                            if href and '/status/' in href and '/photo/' not in href:
                                tweet_id = href
                                break
                        
                        # Fallback: usar parte del HTML si no hay link status claro
                        if not tweet_id:
                            tweet_id = tweet.get_attribute('outerHTML')[:200]
                            
                        if tweet_id not in tweets_procesados:
                            # Guardamos la tupla (elemento, id)
                            tweets_candidatos.append((tweet, tweet_id))
                    except:
                        continue
                
                if not tweets_candidatos:
                    # Todos los visibles ya fueron procesados -> Scroll al final
                    print("  Todos los tweets visibles ya fueron procesados. Scrolleando...")
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweets_visibles[-1])
                        time.sleep(1)
                        self.driver.execute_script("window.scrollBy(0, 800);")
                    except:
                        self.driver.execute_script("window.scrollBy(0, 800);")
                    
                    time.sleep(random.uniform(2, 3))
                    continue
                
                # 3. Tomar el PRIMER candidato disponible (es el siguiente en la lista visual)
                tweet_actual, tweet_id_actual = tweets_candidatos[0]
                
                try:
                    # Scroll suave hacia el tweet
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", tweet_actual)
                    time.sleep(random.uniform(1.0, 2.0))
                    
                    # --- PROCESAR TWEET (Extraer y Like) ---
                    usuario = None
                    try:
                        links_usuario = tweet_actual.find_elements(By.XPATH, ".//a[contains(@href, '/') and not(contains(@href, '/status/'))]")
                        for link in links_usuario:
                            href = link.get_attribute('href')
                            if href and ('x.com/' in href or 'twitter.com/' in href):
                                usuario = href.split('/')[-1] if href.split('/')[-1] != '' else href.split('/')[-2]
                                if usuario not in ['home', 'explore', 'notifications', 'messages', 'i', 'compose']:
                                    break
                    except:
                        pass
                    
                    # Marcar como procesado (éxito o no, para no repetirlo)
                    tweets_procesados.add(tweet_id_actual)
                    
                    if usuario and usuario not in usuarios_extraidos:
                        # Intentar dar LIKE
                        try:
                            boton_like = tweet_actual.find_element(By.XPATH, ".//button[@data-testid='like']")
                            boton_like.click()
                            likes_dados += 1
                            usuarios_extraidos.append(usuario)
                            print(f"  ✓ [{likes_dados}/{cantidad}] Like dado a @{usuario}")
                            like_dado_en_este_ciclo = True
                            
                            # Espera post-like
                            espera = random.uniform(5.0, 8.0)
                            print(f"    ⏳ Esperando {espera:.1f}s...")
                            time.sleep(espera)
                            
                        except Exception as e:
                            # Si falla el like, tal vez ya lo tenía o no es botón
                            pass
                    
                    # --- LÓGICA DE SALTO ---
                    if like_dado_en_este_ciclo:
                        saltos = random.randint(2, 6)
                        print(f"    ↓ Saltando {saltos} publicaciones (por elementos)...")
                        
                        # Buscar el índice del tweet actual en la lista VISIBLE original
                        indice_actual = -1
                        for i, t in enumerate(tweets_visibles):
                            if t == tweet_actual:
                                indice_actual = i
                                break
                        
                        if indice_actual != -1:
                            indice_objetivo = indice_actual + saltos
                            
                            # Marcar los intermedios como procesados para no volver a ellos
                            for k in range(indice_actual + 1, min(indice_objetivo, len(tweets_visibles))):
                                try:
                                    inter_tweet = tweets_visibles[k]
                                    # Intentar sacar ID por enlace de status
                                    links_status_inter = inter_tweet.find_elements(By.XPATH, ".//a[contains(@href, '/status/')]")
                                    inter_id = None
                                    for link in links_status_inter:
                                        href = link.get_attribute('href')
                                        if href and '/status/' in href and '/photo/' not in href:
                                            inter_id = href
                                            break
                                    if not inter_id:
                                        inter_id = inter_tweet.get_attribute('outerHTML')[:200]
                                    tweets_procesados.add(inter_id)
                                except:
                                    pass
                            
                            if indice_objetivo < len(tweets_visibles):
                                # El objetivo está en pantalla
                                tweet_objetivo = tweets_visibles[indice_objetivo]
                                print(f"      Saltando al elemento visible #{indice_objetivo}...")
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", tweet_objetivo)
                                time.sleep(random.uniform(1.5, 2.5))
                            else:
                                # El objetivo está más allá de lo cargado
                                print(f"      El objetivo está fuera de pantalla. Scrolleando al final...")
                                try:
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweets_visibles[-1])
                                    time.sleep(1)
                                    # Scroll adicional para cargar nuevos
                                    self.driver.execute_script(f"window.scrollBy(0, {random.randint(600, 1000)});")
                                except:
                                    pass
                                time.sleep(random.uniform(2, 3))
                        else:
                            # Fallback si no encontramos índice
                            self.driver.execute_script("window.scrollBy(0, 800);")
                            
                except Exception as e:
                    print(f"Error procesando tweet: {e}")
                    continue

            print(f"\n✅ Proceso completado:")
            print(f"  - Usuarios extraídos: {len(usuarios_extraidos)}")
            print(f"  - Likes dados: {likes_dados}")
            
        except Exception as e:
            print(f"✗ Error en extracción inteligente: {e}")
        
        return usuarios_extraidos, likes_dados
            
    def extraer_usuarios(self, objetivo=10) -> List[str]:
        """Extrae nombres de usuario del feed"""
        usuarios_encontrados = set()
        
        try:
            # Selectores comunes para nombres de usuario en Twitter/X
            # Nota: estos selectores pueden cambiar, ajústalos según la estructura actual
            selectores = [
                "//a[contains(@href, '/') and not(contains(@href, '/status/')) and not(contains(@href, '/photo/'))]",
                "//div[@data-testid='User-Name']//a",
                "//span[contains(text(), '@')]"
            ]
            
            for selector in selectores:
                try:
                    elementos = self.driver.find_elements(By.XPATH, selector)
                    
                    for elemento in elementos:
                        try:
                            # Intentar obtener href
                            href = elemento.get_attribute('href')
                            if href and ('twitter.com/' in href or 'x.com/' in href):
                                # Extraer username de la URL
                                if 'twitter.com/' in href:
                                    username = href.split('twitter.com/')[-1].split('/')[0]
                                else:
                                    username = href.split('x.com/')[-1].split('/')[0]
                                    
                                if username and not username in ['home', 'explore', 'notifications', 'messages', 'i', 'compose']:
                                    usuarios_encontrados.add(username)
                            
                            # Intentar obtener texto
                            texto = elemento.text
                            if texto and '@' in texto:
                                username = texto.replace('@', '').strip()
                                if username:
                                    usuarios_encontrados.add(username)
                                    
                        except Exception as e:
                            continue
                            
                    if len(usuarios_encontrados) >= objetivo:
                        break
                        
                except Exception as e:
                    print(f"  Error con selector: {e}")
                    continue
            
            print(f"✓ Extraídos {len(usuarios_encontrados)} usuarios únicos")
            
        except Exception as e:
            print(f"✗ Error extrayendo usuarios: {e}")
        
        return list(usuarios_encontrados)[:objetivo]
    
    
    def scrapear_feed(self, scrolls=3, usuarios_objetivo=10, dar_likes_activo=True, likes_objetivo=10) -> tuple:
        """Proceso completo: scroll inicial + extracción inteligente con likes"""
        print("\n=== Iniciando scraping ===")
        
        # Hacer scroll inicial para cargar contenido
        self.hacer_scroll(scrolls=scrolls, pausa_entre_scrolls=2)
        
        # Usar la nueva función inteligente que extrae usuarios y da likes
        if dar_likes_activo:
            usuarios, likes_dados = self.extraer_y_dar_likes_inteligente(cantidad=usuarios_objetivo)
        else:
            # Si no se quieren likes, usar método antiguo (backup)
            usuarios = []
            likes_dados = 0
        
        print(f"=== Scraping completado: {len(usuarios)} usuarios | {likes_dados} likes ===\n")
        
        return usuarios, likes_dados
    
    def cerrar(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()
            print("✓ Navegador cerrado")
    
    def mantener_sesion_activa(self, minutos=60, intervalo_minutos=10, usuarios_por_pasada=10, likes_por_pasada=10):
        """
        Mantiene el scraping activo durante X minutos con intervalos
        
        Args:
            minutos: Duración total (default 60 minutos = 1 hora)
            intervalo_minutos: Cada cuánto hacer scraping (default 10 min)
            usuarios_por_pasada: Usuarios a extraer por pasada (default 10)
            likes_por_pasada: Likes a dar por pasada (default 10)
        """
        from manager import UsuariosManager
        manager = UsuariosManager()
        
        iteraciones = minutos // intervalo_minutos
        intervalo_segundos = intervalo_minutos * 60
        
        # Contadores totales
        total_usuarios_agregados = 0
        total_likes_dados = 0
        
        print(f"\n{'='*50}")
        print(f"Configuración:")
        print(f"  - Duración total: {minutos} minutos")
        print(f"  - Intervalo: cada {intervalo_minutos} minutos")
        print(f"  - Total de pasadas: {iteraciones}")
        print(f"  - Usuarios por pasada: {usuarios_por_pasada}")
        print(f"  - Likes por pasada: {likes_por_pasada} 💙")
        print(f"{'='*50}\n")
        
        for i in range(iteraciones):
            print(f"\n{'='*50}")
            print(f"PASADA {i+1}/{iteraciones}")
            print(f"{'='*50}")
            
            # Scrapear con el nuevo método inteligente
            nuevos_usuarios, likes_dados = self.scrapear_feed(
                scrolls=3,  # Menos scrolls iniciales
                usuarios_objetivo=usuarios_por_pasada,
                dar_likes_activo=True,
                likes_objetivo=likes_por_pasada
            )
            
            # Procesar con manager
            agregados = manager.agregar_nuevos_usuarios(nuevos_usuarios)
            
            # Actualizar contadores totales
            total_usuarios_agregados += len(agregados)
            total_likes_dados += likes_dados
            
            print(f"\n📊 Resultados de esta pasada:")
            print(f"  - Usuarios encontrados: {len(nuevos_usuarios)}")
            print(f"  - Usuarios nuevos agregados: {len(agregados)}")
            print(f"  - Usuarios repetidos: {len(nuevos_usuarios) - len(agregados)}")
            print(f"  - Likes dados: {likes_dados}/{likes_por_pasada} 💙")
            
            # Mostrar estadísticas totales
            stats = manager.obtener_estadisticas()
            print(f"\n📈 Estadísticas totales del sistema:")
            print(f"  - Total en base principal: {stats['total_principales']}")
            print(f"  - Total repetidos registrados: {stats['total_repetidos']}")
            
            print(f"\n🎯 Acumulado en esta sesión:")
            print(f"  - Total usuarios nuevos agregados: {total_usuarios_agregados}")
            print(f"  - Total likes dados: {total_likes_dados} 💙")
            
            # (Removido) extracción de trending topics
            
            # Esperar hasta la siguiente pasada (excepto en la última)
            if i < iteraciones - 1:
                print(f"\n⏳ Esperando {intervalo_minutos} minutos hasta la siguiente pasada...") 
                time.sleep(intervalo_segundos)
        
        print(f"\n{'='*50}")
        print("✅ PROCESO COMPLETADO")
        print(f"{'='*50}")
        print(f"\n📊 RESUMEN FINAL:")
        print(f"  - Pasadas completadas: {iteraciones}")
        print(f"  - Usuarios nuevos agregados: {total_usuarios_agregados}")
        print(f"  - Likes dados en total: {total_likes_dados} 💙")
        print(f"{'='*50}\n")
