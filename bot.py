import os
import time
import requests
from playwright.sync_api import sync_playwright

# Tu lista de objetivos
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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"Buscando link en {url_cuenta}...")
            page.goto(url_cuenta, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5) # Menos tiempo porque no necesitamos que cargue la imagen
            
            # Obtenemos el link del primer tweet
            tweet_element = page.locator('article').first
            path_tweet = tweet_element.locator('time').locator('xpath=..').get_attribute('href')
            
            # Convertimos x.com en fixupx.com
            link_fixup = f"https://fixupx.com{path_tweet}"
            
            # Sistema de memoria (para no repetir)
            log_file = f"last_id_{url_cuenta.split('/')[-1]}.txt"
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    if f.read() == link_fixup:
                        print(f"Sin novedades en {url_cuenta}")
                        browser.close()
                        return None

            # Guardamos la memoria
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
        enlace_magico = vigilar_y_fixup(cuenta)
        if enlace_magico:
            enviar_telegram_texto(f"🚀 *Nueva publicación de {cuenta.split('/')[-1]}*\n\n{enlace_magico}")
            print(f"¡Enlace enviado: {enlace_magico}!")
