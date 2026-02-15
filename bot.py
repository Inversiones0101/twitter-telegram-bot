import os
import feedparser
import requests
import time
import re

# --- EL NUEVO DÚO DINÁMICO ---
FEEDS = {
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss",
    "BARCHART_BSKY": "https://bsky.app/profile/barchart.com/rss"
}

def extraer_imagen_premium(entrada):
    # Prioridad 1: Media content (imágenes nativas de BlueSky)
    if 'media_content' in entrada: return entrada.media_content[0]['url']
    # Prioridad 2: Enclosures (adjuntos de feed)
    if 'enclosures' in entrada and entrada.enclosures: return entrada.enclosures[0]['url']
    return None

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    txt_titulo = (titulo or "Actualización de Mercado").strip()
    caption = f"🎯 *{fuente}*\n━━━━━━━━━━━━━━\n📝 {txt_titulo}\n\n🔗 [Ver análisis completo]({link})"
    
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            requests.post(url, json={'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}, timeout=30)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}, timeout=20)
    except: pass

def main():
    print("🚀 Radar Dúo Dinámico: TrendSpider + Barchart...")
    archivo_h = "last_id_inicio.txt"
    
    if not os.path.exists(archivo_h):
        with open(archivo_h, "w") as f: f.write("")

    with open(archivo_h, "r") as f:
        historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            print(f"🔍 Escaneando {nombre}...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
            resp = requests.get(url, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                # Invertimos para que el orden en Telegram sea cronológico
                for entrada in reversed(feed.entries[:3]):
                    link = entrada.get('link')
                    if link and link not in historial:
                        print(f"✨ ¡Nuevo posteo en {nombre}!")
                        titulo = entrada.get('title') or (entrada.get('description', '')[:70] + "...")
                        img = extraer_imagen_premium(entrada)
                        enviar_telegram(titulo, link, img, nombre)
                        
                        with open(archivo_h, "a") as f: f.write(link + "\n")
                        historial.add(link)
                        time.sleep(3)
            else:
                print(f"❌ {nombre} falló (Código {resp.status_code})")
        except Exception as e:
            print(f"⚠️ Error en {nombre}: {e}")

if __name__ == "__main__":
    main()
