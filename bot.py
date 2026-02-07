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
    # Probamos con una instancia que suele ser más rápida para cargar contenido
    url = "https://nitter.privacydev.net/robertojirusta"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"Navegando a {url}...")
            # Subimos el tiempo de espera y usamos 'networkidle' para asegurar carga
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # CAMBIO CLAVE: Esperamos específicamente al selector del tweet
            # Si no aparece en 20 segundos, pasamos a otra instancia
            page.wait_for_selector('.timeline-item', timeout=20000)
            time.sleep(5) # Un respiro para que carguen los gráficos

            tweet = page.locator('.timeline-item').first
            
            if tweet.count() > 0:
                texto = tweet.inner_text()
                id_actual = str(hash(texto))
                
                log_file = "last_id_robertojirusta.txt"
                if os.path.exists(log_file) and open(log_file).read().strip() == id_actual:
                    print("Nada nuevo bajo el sol.")
                    return

                foto_path = "roberto.png"
                # Forzamos a que espere a que el elemento sea visible
                tweet.screenshot(path=foto_path)
                
                enviar_telegram_foto(foto_path, "https://x.com/robertojirusta")
                
                with open(log_file, "w") as f:
                    f.write(id_actual)
                print("¡BOOM! Foto enviada.")
            else:
                print("El servidor respondió pero el muro está vacío.")

        except Exception as e:
            print(f"Agotado el tiempo de espera: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    capturar()
