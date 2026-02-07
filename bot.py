import os
import time
import requests
import random
from playwright.sync_api import sync_playwright

# Reducimos el grupo para ser más discretos y efectivos
CUENTAS = ["robertojirusta", "Barchart", "TrendSpider"]

def enviar_telegram_foto(foto_path, cuenta, link):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    caption = f"📸 *Nueva captura de {cuenta}*\n🔗 [Ver en X]({link})"
    try:
        with open(foto_path, 'rb') as photo:
            payload = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
            files = {'photo': photo}
            requests.post(url, data=payload, files=files)
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")

def capturar_y_enviar():
    # Usamos las instancias más estables
    instancias = ["https://nitter.net", "https://nitter.cz"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Disfrazamos al bot como un navegador de escritorio moderno
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()

        for cuenta in CUENTAS:
            # Descanso aleatorio entre 10 y 20 segundos para simular lectura humana
            espera = random.randint(10, 20)
            print(f"Esperando {espera} segundos antes de buscar a {cuenta}...")
            time.sleep(espera)
            
            exito_cuenta = False
            for base_url in instancias:
                if exito_cuenta: break
                try:
                    print(f"--- Buscando a {cuenta} en {base_url} ---")
                    # Vamos a la página de inicio (Home) como un humano
                    page.goto(base_url, wait_until="networkidle", timeout=30000)
                    
                    # Escribimos en el cuadro de búsqueda (input name="q")
                    page.fill('input[name="q"]', cuenta)
                    
                    # Presionamos Enter (la lupita)
                    page.keyboard.press("Enter")
                    
                    # Esperamos a que aparezcan los resultados
                    page.wait_for_selector('.timeline-item', timeout=25000)
                    time.sleep(5) # Tiempo para que carguen los gráficos y fotos

                    tweet = page.locator('.timeline-item').first
                    if tweet.count() > 0:
                        texto = tweet.inner_text()
                        id_actual = str(hash(texto))
                        
                        # Verificamos si es un tweet nuevo consultando la memoria
                        log_file = f"last_id_{cuenta}.txt"
                        if os.path.exists(log_file):
                            with open(log_file, "r") as f:
                                if f.read().strip() == id_actual:
                                    print(f"Sin novedades para {cuenta}")
                                    exito_cuenta = True
                                    continue

                        # Tomamos la captura del recuadro del tweet
                        foto_name = f"{cuenta}.png"
                        tweet.screenshot(path=foto_name)
                        
                        # Enviamos a Telegram y guardamos ID
                        enviar_telegram_foto(foto_name, cuenta, f"https://x.com/{cuenta}")
                        with open(log_file, "w") as f:
                            f.write(id_actual)
                        
                        print(f"¡LOGRADO! Captura de {cuenta} enviada correctamente.")
                        exito_cuenta = True
                    else:
                        print(f"No se encontraron resultados para {cuenta} en {base_url}.")
                
                except Exception as e:
                    print(f"Fallo el intento en {base_url} para {cuenta}. Probando siguiente...")
        
        browser.close()

if __name__ == "__main__":
    capturar_y_enviar()
