import os
import feedparser
import requests
import time
import re

# --- FUENTES CORREGIDAS ---
FEEDS = {
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss",
    "STOCK_CONSULTANT": "https://www.stockconsultant.com/consultant/rss.cgi"
}

def extraer_imagen_premium(entrada):
    # 1. Buscar en media_content o enclosures
    if 'media_content' in entrada: return entrada.media_content[0]['url']
    if 'enclosures' in entrada and entrada.enclosures: return entrada.enclosures[0]['url']
    
    # 2. Buscar en el texto (StockConsultant)
    content = entrada.get('summary', '') + entrada.get('description', '')
    img_match = re.search(r'src="([^"]+)"', content)
    if img_match:
        url = img_match.group(1)
        return 'https:' + url if url.startswith('//') else url
    return None

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    # Manejo de error si el título no existe (el error que vimos en el log)
    txt_titulo = titulo if titulo else "Análisis Técnico Nuevo"
    caption = f"🎯 *{fuente}*\n━━━━━━━━━━━━━━\n📝 {txt_titulo}\n\n🔗 [Ver análisis]({link})"
    
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            requests.post(url, json={'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown'}, timeout=15)
    except: pass

def main():
    print("🚀 Iniciando Radar de Emergencia Final...")
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h):
        with open(archivo_h, "w") as f: f.write("")

    with open(archivo_h, "r") as f:
        historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            print(f"🔍 Conectando a {nombre}...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
            resp = requests.get(url, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                for entrada in feed.entries[:2]:
                    # Usamos .get() para evitar el error 'no attribute title'
                    link = entrada.get('link', '')
                    if link and link not in historial:
                        print(f"✨ Procesando novedad en {nombre}")
                        # Intentamos sacar el título de varias formas
                        titulo = entrada.get('title') or entrada.get('description', '')[:50]
                        img = extraer_imagen_premium(entrada)
                        enviar_telegram(titulo, link, img, nombre)
                        
                        with open(archivo_h, "a") as f: f.write(link + "\n")
                        historial.add(link)
                        time.sleep(2)
            else:
                print(f"❌ {nombre} devolvió error {resp.status_code}")
        except Exception as e:
            print(f"⚠️ Error en {nombre}: {e}")

if __name__ == "__main__":
    main()
