import os
import time
import requests
from playwright.sync_api import sync_playwright

def enviar_telegram_foto(foto_path, link):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    caption = f"📊 *Actualización de Roberto Jirusta*\n🔗 [Ver en X]({link})"
    try:
        with open(foto_path, 'rb') as photo:
            payload = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
            files = {'photo': photo}
            requests.post(url, data=payload, files=files)
    except Exception as e:
        print(f"Error Telegram: {e}")

def capturar():
    # LISTA DE INSTANCIAS: Si una falla, prueba la otra automáticamente
    instancias = [
        "https://nitter.net",
        "https://nitter.cz",
        "https://nitter.no-logs.com",
        "https://nitter.privacydev.net"
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        exito = False
        for base_url in instancias:
            if exito: break
            url = f"{base_url}/robertojirusta"
            try:
                print(f"Intentando en {base_url}...")
                # Reducimos el tiempo de espera por intento para avanzar rápido
                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                
                # Esperamos a que el tweet sea visible
                page.wait_for_selector('.timeline-item', timeout=15000)
                time.sleep(5) 

                tweet = page.locator('.timeline-item').first
                if tweet.count() > 0:
                    texto = tweet.inner_text()
                    id_actual = str(hash(texto))
                    
                    log_file = "last_id_robertojirusta.txt"
                    if os.path.exists(log_file) and open(log_file).read().strip() == id_actual:
                        print(f"Sin cambios en {base_url}.")
                        exito = True
                        continue

                    foto_path = "roberto.png"
                    tweet.screenshot(path=foto_path)
                    enviar_telegram_foto(foto_path, "https://x.com/robertojirusta")
                    
                    with open(log_file, "w") as f:
                        f.write(id_actual)
                    print(f"¡CONSEGUIDO en {base_url}!")
                    exito = True
            except Exception as e:
                print(f"Fallo {base_url}: {e}")
                continue # Si falla, el bucle prueba la siguiente instancia de la lista

        browser.close()

if __name__ == "__main__":
    capturar()
