import os
import time
import requests
from playwright.sync_api import sync_playwright

def enviar_telegram_foto(foto_path, link):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    caption = f"📈 *Nuevo análisis de Roberto Jirusta*\n🔗 [Ver en X]({link})"
    try:
        with open(foto_path, 'rb') as photo:
            payload = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
            files = {'photo': photo}
            requests.post(url, data=payload, files=files)
    except Exception as e:
        print(f"Error Telegram: {e}")

def capturar():
    # Usamos nitter.net que es la que te abrió a ti
    url = "https://nitter.net/robertojirusta"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # DISFRAZ: Copiamos un navegador de PC real
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"Intentando entrar a {url}...")
            # Le damos 45 segundos de tiempo para que no de error de timeout
            page.goto(url, wait_until="networkidle", timeout=45000)
            time.sleep(10) # Esperamos que aparezcan los gráficos

            # Buscamos el primer tweet (clase .timeline-item)
            tweet = page.locator('.timeline-item').first
            
            if tweet.count() > 0:
                texto = tweet.inner_text()
                id_actual = str(hash(texto))
                
                # Memoria
                log_file = "last_id_robertojirusta.txt"
                if os.path.exists(log_file) and open(log_file).read().strip() == id_actual:
                    print("Sin cambios en Roberto.")
                    return

                # CAPTURA
                foto_path = "roberto.png"
                tweet.screenshot(path=foto_path)
                
                # ENVIAR
                enviar_telegram_foto(foto_path, "https://x.com/robertojirusta")
                
                with open(log_file, "w") as f:
                    f.write(id_actual)
                print("¡Éxito! Foto enviada.")
            else:
                print("No se encontró el tweet. Nitter podría estar saturado.")

        except Exception as e:
            print(f"Fallo la conexión: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    capturar()
