# Twitter Bot Scraping

<div align="center">
<a href="https://wa.me/+573001234567?text=Hola%20desde%20BotCryptoV2%20🚀" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white" /></a>
<a href="https://twitter.com/AndresDvst25" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/X/Twitter-000000?style=for-the-badge&logo=x&logoColor=white" /></a>
<a href="https://www.facebook.com/andres.campos.732122" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white" /></a>
<a href="https://www.instagram.com/andres.devback/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" /></a>
<a href="https://www.linkedin.com/in/andresdevback22/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" /></a>
<a href="https://github.com/AndresDvst" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" /></a>
<a href="https://discord.com/users/1133809866130067476" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" /></a>
</div>

Bot en Python para interactuar con el feed de X/Twitter, extraer usuarios y dar likes de forma segura y más humana mediante Selenium. Incluye:
- Menú CLI para operaciones comunes
- Sesión persistente con perfil de Chrome propio
- Extracción inteligente de usuarios y likes con saltos por elementos
- Gestión de usuarios: base principal, historial, repetidos
- Generación de login.json con estructura lateral

## Características
- Scraping manual o automático por intervalos con métricas agregadas
- Like inteligente: identifica tweet actual, da like y salta 2–6 publicaciones
- Evita repetición inmediata de likes con un conjunto de tweets procesados
- Persistencia de sesión con un perfil local dedicado y apertura en ventana nueva
- Utilidades para:
  - Obtener 10 usuarios únicos en los últimos 3 días
  - Agregar usuarios nuevos evitando duplicados
  - Limpiar historial anterior a X días
  - Construir login.json con 40 usuarios aleatorios distribuidos en 4 grupos

## Arquitectura y Flujo
- Entrada principal: [bot.py](file:///Twitter%20Bot%20Scraping/bot.py)
- Lógica de scraping: [scraper.py](file:///Twitter%20Bot%20Scraping/scraper.py)
- Gestión y persistencia: [manager.py](file:///Twitter%20Bot%20Scraping/manager.py)

Flujo típico:
- Ejecutar menú
- Abrir navegador con perfil persistente en ventana nueva
- Navegar a https://x.com/home, iniciar sesión si es necesario
- Ejecutar pasada de scraping (scroll inicial + extracción/likes)
- Registrar nuevos usuarios y estadísticas

## Requisitos
- Python 3.10+ recomendado
- Google Chrome/Chromium instalado
- ChromeDriver local disponible en: \Twitter Bot Scraping\chrome-win\chromedriver.exe`
- Dependencias Python:
  - selenium==4.16.0
  - webdriver-manager==4.0.1

## Instalación
1. Crear entorno virtual:
   
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Instalar dependencias:
   
   ```bash
   pip install -r requirements.txt
   ```

3. Verificar ChromeDriver:
   - Asegura que exista `chrome-win/chromedriver.exe` en el proyecto, o ajusta la ruta en [scraper.py:L53-L61](file:///Twitter%20Bot%20Scraping/scraper.py#L53-L61).
   - Alternativa: migrar a webdriver-manager para descarga automática (ya incluido en requirements).

## Uso
1. Ejecutar el menú:
   
   ```bash
   python Twitter Bot Scraping\bot.py
   ```

2. Opciones:
   - 1: Modificar login.json con 40 usuarios aleatorios distribuidos en aurora/emily/eva/gaby
   - 2: Scraping automático por 1 hora (cada 10 minutos)
   - 3: Scraping manual (una pasada)
   - 4: Ver estadísticas
   - 5: Limpiar historial (>30 días)

3. Primer uso:
   - El bot abre Chrome; inicia sesión manualmente en X si no lo estás.
   - Confirma en la terminal para continuar con el scraping.

## Puntos Clave Técnicos
- Apertura en ventana limpia con perfil persistente: [iniciar_navegador](file:///Twitter%20Bot%20Scraping/scraper.py#L16-L68), [asegurar_ventana_unica](file:///Twitter%20Bot%20Scraping/scraper.py#L83-L105)
- Scroll humano y extracción/likes con saltos por elementos: [scrapear_feed](file:///Twitter%20Bot%20Scraping/scraper.py#L378-L395), [extraer_y_dar_likes_inteligente](file:///Twitter%20Bot%20Scraping/scraper.py#L122-L320)
- Persistencia y utilidades de usuarios: [UsuariosManager](file:///Twitter%20Bot%20Scraping/manager.py#L6-L177)
- Generación de login.json lateral (40 usuarios): [modificar_json_login](file:///Twitter%20Bot%20Scraping/manager.py#L140-L177) y llamada desde [bot.py](file:///Twitter%20Bot%20Scraping/bot.py#L45-L55)

## Estructura de Datos
- data/usuarios_principales.json: lista base de usuarios
- data/historial_entregados.json: registros de entregas con fecha
- data/usuarios_repetidos.json: duplicados detectados con timestamp
- Twitter Bot Scraping\login.json: estructura lateral con 4 grupos y 40 usuarios

## Limpieza de Archivos Obsoletos
Para un repositorio más limpio y portable, se recomienda excluir/eliminar archivos generados por Chrome y datos de perfil. Mantén únicamente lo imprescindible:
- Mantener:
  - `chrome-win/chromedriver.exe` (driver necesario si no usas webdriver-manager)
  - Archivos `.py` del proyecto y `requirements.txt`
  - `data/*.json` propios del bot
- Eliminar o ignorar (caché/perfil/bundles de Chrome):
  - `chrome-win/locales/*` y recursos como `MEIPreload`, `PrivacySandboxAttestationsPreloaded`, `IwaKeyDistribution`, `vk_swiftshader_icd.json`
  - `chrome_profile/**` contenido (LevelDB, LOG, manifests, CaptchaProviders, Crowd Deny, etc.). Mantén la carpeta vacía si quieres conservar la ruta del perfil.
  - Cualquier archivo `LOG`, `LOG.old`, `.pb` dentro de `chrome_profile/Default/**`

Sugerencia: añade estas rutas a `.gitignore` si versionas el proyecto.

## Buenas Prácticas
- Evitar likes consecutivos: el bot salta entre 2–6 publicaciones tras cada like
- Mantener pausas aleatorias y scroll humano para reducir detección
- Mantener el perfil dedicado en `chrome_profile/` para persistencia, pero no versionar su contenido
- Considerar migrar a `webdriver-manager` para descarga/gestión automática del driver

## Créditos
- Selenium WebDriver
- Estructura inspirada en guías profesionales de automatización y bots CLI

<div align="center">
<a href="https://wa.me/+573001234567?text=Hola%20desde%20BotCryptoV2%20🚀" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white" /></a>
<a href="https://twitter.com/AndresDvst25" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/X/Twitter-000000?style=for-the-badge&logo=x&logoColor=white" /></a>
<a href="https://www.facebook.com/andres.campos.732122" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white" /></a>
<a href="https://www.instagram.com/andres.devback/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" /></a>
<a href="https://www.linkedin.com/in/andresdevback22/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" /></a>
<a href="https://github.com/AndresDvst" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" /></a>
<a href="https://discord.com/users/1133809866130067476" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" /></a>
</div>

