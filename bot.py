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
    # Usamos nitter.net como principal ya que viste que funciona bien manual
    instancias = ["https://nitter.net", "https://nitter.cz", "https://nitter.no-logs.com"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # DISFRAZ: Navegador de iPhone para saltar bloqueos 403
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
            viewport={'width': 400, 'height': 800}
        )
        page = context.new_page()

        for cuenta in CUENTAS:
            exito_cuenta = False
            for base_url in instancias:
                if exito_cuenta: break
                try:
                    url_directa = f"{base_url}/{cuenta}"
                    print(f"Navegando a {url_directa}...")
                    
                    # Cargamos la página igual que tú en tu navegador
                    page.goto(url_directa, wait_until="domcontentloaded", timeout=40000)
                    time.sleep(6) # Tiempo para que cargue el gráfico

                    # Localizamos el primer tweet por su clase en Nitter
                    tweet = page.locator('.timeline-item').first
                    
                    if tweet.count() > 0:
                        # Creamos un ID basado en el texto para no repetir
                        texto = tweet.inner_text()
                        id_actual = str(hash(texto))
                        
                        log_file = f"last_id_{cuenta}.txt"
                        if os.path.exists(log_file):
                            with open(log_file, "r") as f:
                                if f.read().strip() == id_actual:
                                    print(f"Sin cambios para {cuenta}")
                                    exito_cuenta = True
                                    continue

                        # SACAR CAPTURA
                        foto_name = f"{cuenta}.png"
                        tweet.screenshot(path=foto_name)
                        
                        # ENVIAR
                        enviar_telegram_foto(foto_name, cuenta, f"https://x.com/{cuenta}")
                        
                        with open(log_file, "w") as f:
                            f.write(id_actual)
                        
                        print(f"¡Captura enviada de {cuenta}!")
                        exito_cuenta = True
                except Exception as e:
                    print(f"Fallo en {base_url} para {cuenta}, probando siguiente espejo...")
        
        browser.close()

if __name__ == "__main__":
    capturar_y_enviar()
