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
    # Lista de espejos de Twitter que no bloquean
    instancias = [
        "https://nitter.cz",
        "https://nitter.privacydev.net",
        "https://nitter.no-logs.com",
        "https://nitter.poast.org", # <-- Agregamos esta
        "https://nitter.net"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 400, 'height': 800})
        page = context.new_page()

        for cuenta in CUENTAS:
            exito = False
            for base_url in instancias:
                if exito: break
                try:
                    print(f"Probando {cuenta} en {base_url}...")
                    page.goto(f"{base_url}/{cuenta}", wait_until="domcontentloaded", timeout=25000)
                    time.sleep(5)

                    tweet_selector = '.timeline-item'
                    primer_tweet = page.locator(tweet_selector).first
                    
                    if primer_tweet.count() > 0:
                        texto_tweet = primer_tweet.inner_text()
                        id_foto = str(hash(texto_tweet))
                        
                        log_file = f"last_id_{cuenta}.txt"
                        if os.path.exists(log_file):
                            with open(log_file, "r") as f:
                                if f.read().strip() == id_foto:
                                    print(f"Sin cambios en {cuenta}")
                                    exito = True
                                    continue

                        foto_name = f"{cuenta}.png"
                        primer_tweet.screenshot(path=foto_name)
                        enviar_telegram_foto(foto_name, cuenta, f"https://x.com/{cuenta}")
                        
                        with open(log_file, "w") as f:
                            f.write(id_foto)
                        exito = True
                        print(f"¡Captura lograda para {cuenta}!")
                except Exception as e:
                    print(f"Fallo en {base_url} para {cuenta}: saltando...")
        
        browser.close()

if __name__ == "__main__":
    capturar_y_enviar()
