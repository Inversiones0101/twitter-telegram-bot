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
        browser = p.chromium.launch(headless=True) # Navegador invisible
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # 1. Ir a la cuenta
        print(f"Visitando {url_cuenta}...")
        page.goto(url_cuenta, wait_until="networkidle")
        time.sleep(5) # Esperar a que carguen los graficos
        
        # 2. Sacar la foto del primer tweet
        # Usamos un selector basico para capturar el primer articulo/tweet
        path_foto = "tweet.png"
        page.locator('article').first.screenshot(path=path_foto)
        
        browser.close()
        return path_foto

if __name__ == "__main__":
    # Prueba inicial con una cuenta de tu lista
    cuenta_prueba = "https://x.com/DolarBlueDiario"
    try:
        foto = capturar_tweet(cuenta_prueba)
        enviar_telegram(foto, f"📸 Captura fresca de {cuenta_prueba}")
        print("¡Exito! Foto enviada a Telegram.")
    except Exception as e:
        print(f"Error: {e}")
