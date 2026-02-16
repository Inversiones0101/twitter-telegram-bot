import os
import feedparser
import requests
import time
import re

# --- CONFIGURACIÓN DE FEEDS (Tus nuevas cuentas elegidas) ---
FEEDS = {
    "ECONOMISTA_AR": "https://bsky.app/profile/eleconomista.com.ar.web.brid.gy/rss",
    "FINCOINS_GLOBAL": "https://bsky.app/profile/fincoins.bsky.social/rss",
    "AMBITO_DOLAR": "https://bsky.app/profile/ambitodolar.bsky.social/rss",
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss",
    "BARCHART_BSKY": "https://bsky.app/profile/barchart.com/rss"
}

def enviar_telegram(titulo, link, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Formato con link para que Telegram genere la card automáticamente
    mensaje = f"🎯 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 {link}"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False # Activado para ver las imágenes de Ámbito
    }
    
    try:
        requests.post(url, json=payload, timeout=20)
    except Exception as e:
        print(f"Error en Telegram: {e}")

def main():
    print("🚀 Iniciando Bot Informador...")
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h):
        with open(archivo_h, "w") as f: f.write("")

    with open(archivo_h, "r") as f:
        historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                # Revisamos los últimos 5 para no perder la Apertura/Cierre si hay mucho spam de texto
                for entrada in reversed(feed.entries[:5]):
                    link = entrada.get('link')
                    if link and link not in historial:
                        titulo_original = entrada.get('title', '')
                        titulo_up = titulo_original.upper()
                        
                        # --- FILTRO EXCLUSIVO PARA ÁMBITO DÓLAR ---
                        if nombre == "AMBITO_DOLAR":
                            # Solo pasa si es Apertura o Cierre
                            if "APERTURA DE JORNADA" not in titulo_up and "CIERRE DE JORNADA" not in titulo_up:
                                continue 
                        
                        enviar_telegram(titulo_original, link, nombre)
                        
                        with open(archivo_h, "a") as f:
                            f.write(link + "\n")
                        historial.add(link)
                        time.sleep(2)
        except Exception as e:
            print(f"Error en {nombre}: {e}")

if __name__ == "__main__":
    main()
