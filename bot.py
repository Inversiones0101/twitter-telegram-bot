import os
import time
import requests
from playwright.sync_api import sync_playwright
import random
import re 

CUENTAS = ["Barchart", "TrendSpider", "AndresConstabel", "chtrader", "robertojirusta", "leofinanzas"]

def enviar_telegram(texto):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': texto, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

def obtener_tweet(cuenta):
    with sync_playwright() as p:
        # Usamos un navegador que parece un usuario real
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 667} # Simula un celular
        )
        page = context.new_page()
        
        try:
            # Vamos directo a los tweets, esto suele saltar el bloqueo de perfil
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{cuenta}"
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Buscamos el ID del tweet en el código de la página
            content = page.content()
            # Buscamos el patrón de un ID de tweet (números largos)
            import re
            ids = re.findall(r'status/(\d+)', content)
            
            if not ids:
                print(f"No se detectaron tweets para {cuenta}")
                return None
            
            id_reciente = ids[0]
            link_fixup = f"https://fixupx.com/{cuenta}/status/{id_reciente}"
            
            # MEMORIA
            log_file = f"last_id_{cuenta}.txt"
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    if f.read().strip() == id_reciente:
                        return None

            with open(log_file, "w") as f:
                f.write(id_reciente)
            
            return link_fixup
        except Exception as e:
            print(f"Error en {cuenta}: {e}")
            return None
        finally:
            browser.close()

if __name__ == "__main__":
    for c in CUENTAS:
        resultado = obtener_tweet(c)
        if resultado:
            enviar_telegram(f"🚀 *Nuevo de {c}*\n\n{resultado}")
            time.sleep(random.randint(5, 10)) # Espera aleatoria para no ser detectado
