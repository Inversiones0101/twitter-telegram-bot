import os
import time
import requests
from playwright.sync_api import sync_playwright

# Configuración de cuentas
CUENTAS = [
    "https://x.com/Barchart",
    "https://x.com/TrendSpider",
    "https://x.com/AndresConstabel",
    "https://x.com/chtrader",
    "https://x.com/DolarBlueDiario"
]

def enviar_telegram(imagen_path, texto):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(imagen_path, 'rb') as photo:
        requests.post(url, data={'chat_id': chat_id, 'caption': texto}, files={'photo': photo})

def capturar_tweet(url_cuenta):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"Buscando novedades en {url_cuenta}...")
            page.goto(url_cuenta, wait_until="domcontentloaded", timeout=60000)
            time.sleep(10) 
            
            # Buscamos el primer tweet disponible
            tweet_element = page.locator('article').first
            
            # Buscamos el link del tweet de forma más segura
            # Buscamos el elemento 'a' que contiene el tiempo (time)
            nuevo_id = tweet_element.locator('time').locator('xpath=..').get_attribute('href')
            
            log_file = f"last_id_{url_cuenta.split('/')[-1]}.txt"
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    if f.read() == nuevo_id:
                        print(f"No hay nada nuevo en {url_cuenta}")
                        browser.close()
                        return None, None

            path_foto = f"foto_{url_cuenta.split('/')[-1]}.png"
            tweet_element.screenshot(path=path_foto)
            
            with open(log_file, "w") as f:
                f.write(nuevo_id)
            
            browser.close()
            return path_foto, nuevo_id
        except Exception as e:
            print(f"Error en {url_cuenta}: {e}")
            browser.close()
            return None, None

if __name__ == "__main__":
    for cuenta in CUENTAS:
        foto, id_tweet = capturar_tweet(cuenta)
        if foto:
            enviar_telegram(foto, f"📈 Novedad de {cuenta}\n🔗 Link: https://x.com{id_tweet}")
            print(f"¡Foto enviada de {cuenta}!")
