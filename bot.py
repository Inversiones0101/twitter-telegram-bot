import os
import feedparser
import requests
import time

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
    
    txt_titulo = (titulo or "Análisis").strip()
    
    # La magia del HTML: El link queda oculto en el nombre de la fuente
    # Ej: BARCHART_BSKY aparecerá en azul y te llevará a BlueSky
    caption_html = f"🎯 <b><a href='{link}'>{fuente}</a></b>\n━━━━━━━━━━━━━━\n📝 {txt_titulo}"
    
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {
                'chat_id': chat_id,
                'photo': image_url,
                'caption': caption_html,
                'parse_mode': 'HTML' # <--- CAMBIO CLAVE
            }
            requests.post(url, json=payload, timeout=30)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': caption_html,
                'parse_mode': 'HTML', # <--- CAMBIO CLAVE
                'disable_web_page_preview': True
            }
            requests.post(url, json=payload, timeout=20)
    except Exception as e:
        print(f"Error en Telegram: {e}")
        
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
                # Invertimos para orden cronológico en Telegram
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
