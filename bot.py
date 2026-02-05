import os
import time
import requests
from playwright.sync_api import sync_playwright

CUENTAS = ["Barchart", "TrendSpider", "AndresConstabel", "chtrader", "robertojirusta", "leofinanzas"]

def enviar_telegram_foto(foto_path, cuenta, link):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    caption = f"📸 *Nueva captura de {cuenta}*\n🔗 [Ver en X]({link})"
    with open(foto_path, 'rb') as photo:
        payload = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
        files = {'photo': photo}
        requests.post(url, data=payload, files=files)

def capturar_y_enviar():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Usamos una identidad de celular para que cargue más liviano
        context = browser.new_context(viewport={'width': 400, 'height': 800})
        page = context.new_page()

        for cuenta in CUENTAS:
            try:
                print(f"Fotografiando a {cuenta} via Nitter...")
                # Usamos una instancia confiable de Nitter
                page.goto(f"https://nitter.net/{cuenta}", wait_until="domcontentloaded", timeout=30000)
                time.sleep(3) # Espera corta, Nitter es veloz

                # Seleccionamos el primer tweet en Nitter
                tweet_selector = '.timeline-item'
                primer_tweet = page.locator(tweet_selector).first
                
                texto_tweet = primer_tweet.inner_text()
                id_foto = str(hash(texto_tweet))
                
                log_file = f"last_id_{cuenta}.txt"
                if os.path.exists(log_file):
                    with open(log_file, "r") as f:
                        if f.read().strip() == id_foto:
                            print(f"Sin cambios en {cuenta}")
                            continue

                foto_name = f"{cuenta}.png"
                primer_tweet.screenshot(path=foto_name)
                
                # Enviamos el link de X original para que tú lo veas bien
                enviar_telegram_foto(foto_name, cuenta, f"https://x.com/{cuenta}")
                
                with open(log_file, "w") as f:
                    f.write(id_foto)
                
            except Exception as e:
                print(f"Error con {cuenta}: {e}")
        
        browser.close()

if __name__ == "__main__":
    capturar_y_enviar()
