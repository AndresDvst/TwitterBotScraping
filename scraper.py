"""
Twitter Scraper mejorado con logging, anti-detección y configuración centralizada
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException, TimeoutException
import time
import random
from typing import List, Set, Tuple, Optional

from logger import bot_logger, log_exception
from config import Config
from utils import retry_on_exception, safe_execute, ScrapingException, RateLimitException
from checkpoint import CheckpointManager


class TwitterScraper:
    def __init__(self, headless: bool = None):
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless if headless is not None else Config.HEADLESS_MODE
        self.checkpoint_manager = CheckpointManager()
        self.tweets_procesados: Set[str] = set()
        self.likes_dados_sesion = 0
        self.inicio_sesion = time.time()
        
        bot_logger.info(f"TwitterScraper inicializado (headless={self.headless})")
        
    def _get_random_user_agent(self) -> str:
        """Retorna un User-Agent aleatorio"""
        return Config.get_random_user_agent()
    
    def _pausa_humana(self, min_sec: float = None, max_sec: float = None):
        """Pausa con distribución normal para simular comportamiento humano"""
        min_sec = min_sec or Config.MIN_PAUSE_SECONDS
        max_sec = max_sec or Config.MAX_PAUSE_SECONDS
        
        # Usar distribución normal centrada en el promedio
        media = (min_sec + max_sec) / 2
        std_dev = (max_sec - min_sec) / 4
        
        # Usar random.gauss en lugar de numpy
        pausa = random.gauss(media, std_dev)
        pausa = max(min_sec, min(max_sec, pausa))  # Clamp
        
        time.sleep(pausa)
        
    @retry_on_exception(max_attempts=2, delay=2.0)
    def iniciar_navegador(self):
        """Inicia el navegador Chrome/Chromium con perfil persistente y anti-detección"""
        bot_logger.info("Iniciando navegador...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
            bot_logger.info("Modo headless activado")
        
        # Directorio de perfil de usuario
        import os
        user_data_dir = Config.CHROME_PROFILE_DIR
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Configurar perfil persistente
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        chrome_options.add_argument('--profile-directory=Default')
        
        # Anti-detección mejorada
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent aleatorio
        user_agent = self._get_random_user_agent()
        chrome_options.add_argument(f'user-agent={user_agent}')
        bot_logger.debug(f"User-Agent: {user_agent[:50]}...")
        
        # Opciones adicionales
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-session-crashed-bubble')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--new-window')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--remote-allow-origins=*')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--v=0')
        chrome_options.add_argument("--start-maximized")
        
        # Chrome portable si existe
        import os
        chrome_binary = Config.CHROME_BINARY_PATH
        if os.path.exists(chrome_binary):
            chrome_options.binary_location = chrome_binary
            bot_logger.debug(f"Usando Chrome portable: {chrome_binary}")
        
        # Configurar chromedriver
        from selenium.webdriver.chrome.service import Service
        import subprocess
        
        chromedriver_path = Config.CHROMEDRIVER_PATH
        
        try:
            # Intentar con chromedriver local primero
            if os.path.exists(chromedriver_path):
                service = Service(executable_path=chromedriver_path, log_output=subprocess.DEVNULL)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                bot_logger.info(f"ChromeDriver local: {chromedriver_path}")
            else:
                raise FileNotFoundError("ChromeDriver local no encontrado")
                
        except (SessionNotCreatedException, FileNotFoundError) as e:
            # Fallback a webdriver-manager
            bot_logger.warning("ChromeDriver local falló, usando webdriver-manager...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                bot_logger.info("ChromeDriver descargado automáticamente")
            except Exception as e2:
                log_exception(bot_logger, e2, "Error iniciando navegador")
                raise
        
        # Maximizar ventana
        self.driver.maximize_window()
        
        # Modificar navigator.webdriver para evitar detección
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        bot_logger.info("✓ Navegador iniciado correctamente")
        
    def ir_a_twitter(self, url: str = "https://x.com/home"):
        """Navega a Twitter/X"""
        if not self.driver:
            self.iniciar_navegador()
        
        self.asegurar_ventana_unica()
        
        bot_logger.info(f"Navegando a {url}...")
        self.driver.get(url)
        
        # Espera más natural
        self._pausa_humana(5.0, 8.0)
        bot_logger.info("✓ Página cargada")
    
    def asegurar_ventana_unica(self):
        """Cierra pestañas/ventanas restauradas y abre una nueva ventana limpia"""
        try:
            if not self.driver:
                return
            
            handles = self.driver.window_handles
            if len(handles) > 1:
                bot_logger.debug(f"Cerrando {len(handles)-1} ventanas adicionales...")
                
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
                    
                bot_logger.debug("✓ Ventana única asegurada")
        except Exception as e:
            bot_logger.warning(f"Error asegurando ventana única: {e}")
        
    def hacer_scroll(self, scrolls: int = None, pausa_entre_scrolls: float = None):
        """Realiza scroll en el feed con comportamiento más humano"""
        scrolls = scrolls or Config.SCROLL_COUNT
        pausa_entre_scrolls = pausa_entre_scrolls or Config.MIN_PAUSE_SECONDS
        
        bot_logger.info(f"Iniciando {scrolls} scrolls...")
        
        for i in range(scrolls):
            # Scroll con distancia variable (más humano)
            distancia = random.randint(Config.MIN_SCROLL_DISTANCE, Config.MAX_SCROLL_DISTANCE)
            self.driver.execute_script(f"window.scrollBy(0, {distancia});")
            
            # Pausa variable entre scrolls
            self._pausa_humana(pausa_entre_scrolls * 0.8, pausa_entre_scrolls * 1.2)
            
            bot_logger.debug(f"Scroll {i+1}/{scrolls} ({distancia}px)")
    
    def _verificar_rate_limit(self) -> bool:
        """Verifica si se alcanzó el límite de likes por hora"""
        tiempo_transcurrido = time.time() - self.inicio_sesion
        horas_transcurridas = tiempo_transcurrido / 3600
        
        if horas_transcurridas > 0:
            likes_por_hora = self.likes_dados_sesion / horas_transcurridas
            
            if likes_por_hora > Config.MAX_LIKES_PER_HOUR:
                bot_logger.warning(
                    f"⚠ Rate limit alcanzado: {likes_por_hora:.1f} likes/hora "
                    f"(máximo: {Config.MAX_LIKES_PER_HOUR})"
                )
                return True
        
        return False
    
    def extraer_y_dar_likes_inteligente(self, cantidad: int = 10) -> Tuple[List[str], int]:
        """
        Extrae usuarios y da likes de forma más humana con anti-detección mejorada
        """
        usuarios_extraidos = []
        likes_dados = 0
        
        bot_logger.info(f"Iniciando extracción inteligente (objetivo: {cantidad} usuarios)")
        
        try:
            # Hacer scroll inicial para cargar tweets
            self.driver.execute_script("window.scrollBy(0, 500);")
            self._pausa_humana(2, 3)
            
            # Selectores para tweets completos
            selectores_tweets = [
                "//article[@data-testid='tweet']",
                "//div[@data-testid='cellInnerDiv']//article"
            ]
            
            intentos = 0
            max_intentos = cantidad * 4
            
            while likes_dados < cantidad and intentos < max_intentos:
                intentos += 1
                
                # Verificar rate limit
                if self._verificar_rate_limit():
                    bot_logger.warning("Pausando por rate limit...")
                    time.sleep(60)  # Pausa de 1 minuto
                
                like_dado_en_este_ciclo = False
                
                # 1. Obtener TODOS los tweets visibles
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
                    bot_logger.debug("No se encontraron tweets, haciendo scroll...")
                    self.driver.execute_script("window.scrollBy(0, 800);")
                    self._pausa_humana(2, 3)
                    continue
                
                # 2. Filtrar tweets ya procesados
                tweets_candidatos = []
                for tweet in tweets_visibles:
                    try:
                        # Intentar obtener ID único
                        links_status = tweet.find_elements(By.XPATH, ".//a[contains(@href, '/status/')]")
                        tweet_id = None
                        
                        for link in links_status:
                            href = link.get_attribute('href')
                            if href and '/status/' in href and '/photo/' not in href:
                                tweet_id = href
                                break
                        
                        if not tweet_id:
                            tweet_id = tweet.get_attribute('outerHTML')[:200]
                        
                        if tweet_id not in self.tweets_procesados:
                            tweets_candidatos.append((tweet, tweet_id))
                    except:
                        continue
                
                if not tweets_candidatos:
                    bot_logger.debug("Todos los tweets visibles ya fueron procesados. Scrolleando...")
                    try:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", 
                            tweets_visibles[-1]
                        )
                        self._pausa_humana(1, 2)
                        self.driver.execute_script("window.scrollBy(0, 800);")
                    except:
                        self.driver.execute_script("window.scrollBy(0, 800);")
                    
                    self._pausa_humana(2, 3)
                    continue
                
                # 3. Tomar el PRIMER candidato
                tweet_actual, tweet_id_actual = tweets_candidatos[0]
                
                try:
                    # Scroll suave hacia el tweet
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                        tweet_actual
                    )
                    self._pausa_humana(1.0, 2.0)
                    
                    # --- PROCESAR TWEET ---
                    usuario = None
                    try:
                        links_usuario = tweet_actual.find_elements(
                            By.XPATH, 
                            ".//a[contains(@href, '/') and not(contains(@href, '/status/'))]"
                        )
                        
                        for link in links_usuario:
                            href = link.get_attribute('href')
                            if href and ('x.com/' in href or 'twitter.com/' in href):
                                usuario = href.split('/')[-1] if href.split('/')[-1] != '' else href.split('/')[-2]
                                if usuario not in ['home', 'explore', 'notifications', 'messages', 'i', 'compose']:
                                    break
                    except:
                        pass
                    
                    # Marcar como procesado
                    self.tweets_procesados.add(tweet_id_actual)
                    
                    if usuario and usuario not in usuarios_extraidos:
                        # Intentar dar LIKE
                        try:
                            boton_like = tweet_actual.find_element(By.XPATH, ".//button[@data-testid='like']")
                            boton_like.click()
                            
                            likes_dados += 1
                            self.likes_dados_sesion += 1
                            usuarios_extraidos.append(usuario)
                            
                            bot_logger.info(f"✓ [{likes_dados}/{cantidad}] Like dado a @{usuario}")
                            like_dado_en_este_ciclo = True
                            
                            # Espera post-like más variable
                            espera = random.uniform(Config.MIN_POST_LIKE_WAIT, Config.MAX_POST_LIKE_WAIT)
                            bot_logger.debug(f"Esperando {espera:.1f}s...")
                            time.sleep(espera)
                            
                        except Exception as e:
                            bot_logger.debug(f"No se pudo dar like: {e}")
                    
                    # --- LÓGICA DE SALTO ---
                    if like_dado_en_este_ciclo:
                        saltos = random.randint(Config.MIN_SALTOS, Config.MAX_SALTOS)
                        bot_logger.debug(f"Saltando {saltos} publicaciones...")
                        
                        # Buscar índice del tweet actual
                        indice_actual = -1
                        for i, t in enumerate(tweets_visibles):
                            if t == tweet_actual:
                                indice_actual = i
                                break
                        
                        if indice_actual != -1:
                            indice_objetivo = indice_actual + saltos
                            
                            # Marcar intermedios como procesados
                            for k in range(indice_actual + 1, min(indice_objetivo, len(tweets_visibles))):
                                try:
                                    inter_tweet = tweets_visibles[k]
                                    links_status_inter = inter_tweet.find_elements(
                                        By.XPATH, 
                                        ".//a[contains(@href, '/status/')]"
                                    )
                                    inter_id = None
                                    
                                    for link in links_status_inter:
                                        href = link.get_attribute('href')
                                        if href and '/status/' in href and '/photo/' not in href:
                                            inter_id = href
                                            break
                                    
                                    if not inter_id:
                                        inter_id = inter_tweet.get_attribute('outerHTML')[:200]
                                    
                                    self.tweets_procesados.add(inter_id)
                                except:
                                    pass
                            
                            if indice_objetivo < len(tweets_visibles):
                                tweet_objetivo = tweets_visibles[indice_objetivo]
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                                    tweet_objetivo
                                )
                                self._pausa_humana(1.5, 2.5)
                            else:
                                # Scroll adicional
                                try:
                                    self.driver.execute_script(
                                        "arguments[0].scrollIntoView({block: 'center'});", 
                                        tweets_visibles[-1]
                                    )
                                    self._pausa_humana(1, 2)
                                    self.driver.execute_script(
                                        f"window.scrollBy(0, {random.randint(600, 1000)});"
                                    )
                                except:
                                    pass
                                
                                self._pausa_humana(2, 3)
                        else:
                            self.driver.execute_script("window.scrollBy(0, 800);")
                            
                except Exception as e:
                    bot_logger.warning(f"Error procesando tweet: {e}")
                    continue
            
            bot_logger.info(
                f"✅ Proceso completado: {len(usuarios_extraidos)} usuarios, {likes_dados} likes"
            )
            
        except Exception as e:
            log_exception(bot_logger, e, "Error en extracción inteligente")
        
        return usuarios_extraidos, likes_dados
    
    def scrapear_feed(
        self, 
        scrolls: int = 3, 
        usuarios_objetivo: int = 10, 
        dar_likes_activo: bool = True, 
        likes_objetivo: int = 10
    ) -> Tuple[List[str], int]:
        """Proceso completo: scroll inicial + extracción inteligente con likes"""
        bot_logger.info("=== Iniciando scraping ===")
        
        # Hacer scroll inicial para cargar contenido
        self.hacer_scroll(scrolls=scrolls, pausa_entre_scrolls=2)
        
        # Usar la función inteligente
        if dar_likes_activo:
            usuarios, likes_dados = self.extraer_y_dar_likes_inteligente(cantidad=usuarios_objetivo)
        else:
            usuarios = []
            likes_dados = 0
        
        bot_logger.info(f"=== Scraping completado: {len(usuarios)} usuarios | {likes_dados} likes ===")
        
        return usuarios, likes_dados
    
    def cerrar(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()
            bot_logger.info("✓ Navegador cerrado")
    
    def mantener_sesion_activa(
        self, 
        minutos: int = 60, 
        intervalo_minutos: int = 10, 
        usuarios_por_pasada: int = 10, 
        likes_por_pasada: int = 10
    ):
        """Mantiene el scraping activo durante X minutos con intervalos y checkpoints"""
        from manager import UsuariosManager
        manager = UsuariosManager()
        
        iteraciones = minutos // intervalo_minutos
        intervalo_segundos = intervalo_minutos * 60
        
        # Contadores totales
        total_usuarios_agregados = 0
        total_likes_dados = 0
        
        bot_logger.info("="*50)
        bot_logger.info(f"Configuración:")
        bot_logger.info(f"  - Duración total: {minutos} minutos")
        bot_logger.info(f"  - Intervalo: cada {intervalo_minutos} minutos")
        bot_logger.info(f"  - Total de pasadas: {iteraciones}")
        bot_logger.info(f"  - Usuarios por pasada: {usuarios_por_pasada}")
        bot_logger.info(f"  - Likes por pasada: {likes_por_pasada}")
        bot_logger.info("="*50)
        
        for i in range(iteraciones):
            bot_logger.info("="*50)
            bot_logger.info(f"PASADA {i+1}/{iteraciones}")
            bot_logger.info("="*50)
            
            # Guardar checkpoint
            checkpoint_state = {
                'iteracion': i,
                'total_usuarios': total_usuarios_agregados,
                'total_likes': total_likes_dados
            }
            self.checkpoint_manager.save_checkpoint(checkpoint_state)
            
            # Scrapear
            nuevos_usuarios, likes_dados = self.scrapear_feed(
                scrolls=3,
                usuarios_objetivo=usuarios_por_pasada,
                dar_likes_activo=True,
                likes_objetivo=likes_por_pasada
            )
            
            # Procesar con manager
            agregados = manager.agregar_nuevos_usuarios(nuevos_usuarios)
            
            # Actualizar contadores
            total_usuarios_agregados += len(agregados)
            total_likes_dados += likes_dados
            
            bot_logger.info(f"\n📊 Resultados de esta pasada:")
            bot_logger.info(f"  - Usuarios encontrados: {len(nuevos_usuarios)}")
            bot_logger.info(f"  - Usuarios nuevos agregados: {len(agregados)}")
            bot_logger.info(f"  - Usuarios repetidos: {len(nuevos_usuarios) - len(agregados)}")
            bot_logger.info(f"  - Likes dados: {likes_dados}/{likes_por_pasada}")
            
            # Estadísticas totales
            stats = manager.obtener_estadisticas()
            bot_logger.info(f"\n📈 Estadísticas totales del sistema:")
            bot_logger.info(f"  - Total en base principal: {stats['total_principales']}")
            bot_logger.info(f"  - Total repetidos registrados: {stats['total_repetidos']}")
            
            bot_logger.info(f"\n🎯 Acumulado en esta sesión:")
            bot_logger.info(f"  - Total usuarios nuevos agregados: {total_usuarios_agregados}")
            bot_logger.info(f"  - Total likes dados: {total_likes_dados}")
            
            # Esperar hasta la siguiente pasada
            if i < iteraciones - 1:
                bot_logger.info(f"\n⏳ Esperando {intervalo_minutos} minutos hasta la siguiente pasada...")
                time.sleep(intervalo_segundos)
                
                # Recargar página para contenido fresco y evitar likes repetidos
                bot_logger.info("🔄 Recargando página para cargar contenido fresco...")
                try:
                    self.driver.refresh()
                    self._pausa_humana(3, 5)
                    bot_logger.info("✓ Página recargada")
                    
                    # Limpiar tweets procesados para la nueva pasada
                    self.tweets_procesados.clear()
                    bot_logger.debug("✓ Cache de tweets limpiado")
                    
                except Exception as e:
                    bot_logger.warning(f"Error recargando página: {e}")
                    # Si falla la recarga, intentar navegar de nuevo
                    try:
                        self.ir_a_twitter("https://x.com/home")
                        self.tweets_procesados.clear()
                    except:
                        pass
        
        # Limpiar checkpoint al finalizar
        self.checkpoint_manager.clear_checkpoint()
        
        bot_logger.info("="*50)
        bot_logger.info("✅ PROCESO COMPLETADO")
        bot_logger.info("="*50)
        bot_logger.info(f"\n📊 RESUMEN FINAL:")
        bot_logger.info(f"  - Pasadas completadas: {iteraciones}")
        bot_logger.info(f"  - Usuarios nuevos agregados: {total_usuarios_agregados}")
        bot_logger.info(f"  - Likes dados en total: {total_likes_dados}")
        bot_logger.info("="*50)
