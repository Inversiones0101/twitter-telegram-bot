import os
import time
import requests
from playwright.sync_api import sync_playwright

def enviar_telegram(imagen_path, texto):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(imagen_path, 'rb') as photo:
        requests.post(url, data={'chat_id': chat_id, 'caption': texto}, files={'photo': photo})

def capturar_tweet(url_cuenta):
    with sync_playwright() as p:
        # Usamos un "User Agent" para parecer una persona real y no un bot
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Visitando {url_cuenta}...")
        # Le damos más tiempo (60 segundos) y esperamos a que cargue lo básico
        try:
            page.goto(url_cuenta, wait_until="domcontentloaded", timeout=60000)
            time.sleep(10) # Pausa generosa para que aparezcan los tweets
            
            path_foto = "tweet.png"
            # Intentamos capturar el primer artículo que aparezca
            page.locator('article').first.screenshot(path=path_foto)
            browser.close()
            return path_foto
        except Exception as e:
            print(f"Error detallado: {e}")
            browser.close()
            return None

if __name__ == "__main__":
    # Probemos con Barchart que suele cargar más rápido
    cuenta_prueba = "https://x.com/Barchart"
    foto = capturar_tweet(cuenta_prueba)
    if foto:
        enviar_telegram(foto, f"📸 ¡Prueba superada! Captura de {cuenta_prueba}")
        print("¡Éxito total!")
    else:
        print("No se pudo sacar la foto, reintentando...")
