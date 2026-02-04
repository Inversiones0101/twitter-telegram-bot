import os
import time
import requests
from playwright.sync_api import sync_playwright

# Tu lista de objetivos actualizada
CUENTAS = [
    "https://x.com/Barchart",
    "https://x.com/TrendSpider",
    "https://x.com/AndresConstabel",
    "https://x.com/chtrader",
    "https://x.com/BancoCentral_AR",
    "https://x.com/robertojirusta",
    "https://x.com/leofinanzas"
]

def enviar_telegram_texto(texto):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': texto, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

def vigilar_y_fixup(url_cuenta):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Forzamos idioma y un navegador moderno para evitar bloqueos
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="es-AR"
        )
        page = context.new_page()
        
        try:
            print(f"Buscando link en {url_cuenta}...")
            # Tiempo de espera generoso para cargar el contenido pesado de X
            page.goto(url_cuenta, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector('article', timeout=20000) 
            time.sleep(5) 
            
            tweet_element = page.locator('article').first
            
            # Buscador de links mejorado: rastrea todos los enlaces del tweet
            links = tweet_element.locator('a').all()
            path_tweet = None
            for link in links:
                href = link.get_attribute('href')
                # Buscamos el patrón único de un tweet: /status/número
                if href and '/status/' in href and not 'photo' in href:
                    path_tweet = href
                    break
            
            if not path_tweet:
                print(f"No se encontró link válido en {url_cuenta}")
                return None

            # Aplicamos tu toque maestro: FixupX
            link_fixup = f"https://fixupx.com{path_tweet}"
            
            # SISTEMA DE MEMORIA PERSISTENTE
            log_file = f"last_id_{url_cuenta.split('/')[-1]}.txt"
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    if f.read().strip() == link_fixup:
                        print(f"Sin novedades en {url_cuenta}")
                        browser.close()
                        return None

            # Guardamos el ID localmente (luego el .yml lo subirá a GitHub)
            with open(log_file, "w") as f:
                f.write(link_fixup)
            
            browser.close()
            return link_fixup
        except Exception as e:
            print(f"Error en {url_cuenta}: {e}")
            browser.close()
            return None

if __name__ == "__main__":
    for cuenta in CUENTAS:
        enlace = vigilar_y_fixup(cuenta)
        if enlace:
            # Enviamos el link con estética limpia a Telegram
            nombre = cuenta.split('/')[-1]
            enviar_telegram_texto(f"🚀 *Nueva publicación de {nombre}*\n\n{enlace}")
            print(f"¡Enviado con éxito: {nombre}!")
