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
        # Simulamos un usuario real para evitar bloqueos
        context = browser.new_context(viewport={'width': 800, 'height': 1200})
        page = context.new_page()

        for cuenta in CUENTAS:
            try:
                print(f"Fotografiando a {cuenta}...")
                page.goto(f"https://x.com/{cuenta}", wait_until="networkidle", timeout=60000)
                time.sleep(5) # Esperamos que carguen las imágenes

                # Localizamos el primer tweet
                tweet_selector = 'article[data-testid="tweet"]'
                primer_tweet = page.locator(tweet_selector).first
                
                # Obtenemos un ID visual (el texto del tweet) para la memoria
                texto_tweet = primer_tweet.inner_text()
                id_foto = str(hash(texto_tweet))
                
                # REVISAR MEMORIA
                log_file = f"last_id_{cuenta}.txt"
                if os.path.exists(log_file):
                    with open(log_file, "r") as f:
                        if f.read().strip() == id_foto:
                            print(f"Sin cambios en {cuenta}")
                            continue

                # SACAR FOTO
                foto_name = f"{cuenta}.png"
                primer_tweet.screenshot(path=foto_name)
                
                # ENVIAR
                link_directo = f"https://x.com/{cuenta}"
                enviar_telegram_foto(foto_name, cuenta, link_directo)
                
                # GUARDAR MEMORIA
                with open(log_file, "w") as f:
                    f.write(id_foto)
                
            except Exception as e:
                print(f"Error con {cuenta}: {e}")
        
        browser.close()

if __name__ == "__main__":
    capturar_y_enviar()
