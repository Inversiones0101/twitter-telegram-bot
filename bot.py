import os
import feedparser
import requests
import time
import re

FEEDS = {
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss",
    "STOCK_CONSULTANT": "https://www.stockconsultant.com/consultant/rss.cgi"
}

def extraer_imagen_premium(entrada):
    if 'media_content' in entrada: return entrada.media_content[0]['url']
    if 'enclosures' in entrada and entrada.enclosures: return entrada.enclosures[0]['url']
    content = entrada.get('summary', '') + entrada.get('description', '')
    img_match = re.search(r'src="([^"]+)"', content)
    if img_match:
        url = img_match.group(1)
        return 'https:' + url if url.startswith('//') else url
    return None

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    txt_titulo = (titulo or "Nuevo Gráfico Técnico").strip()
    caption = f"🎯 *{fuente}*\n━━━━━━━━━━━━━━\n📝 {txt_titulo}\n\n🔗 [Ver análisis]({link})"
    
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            requests.post(url, json={'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}, timeout=30)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}, timeout=20)
    except: pass

def main():
    print("🚀 Radar Tanque: Barrido en orden cronológico...")
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
                # TRUCO: .reversed() para que mande la más vieja primero y la nueva quede abajo
                for entrada in reversed(feed.entries[:3]):
                    link = entrada.get('link')
                    if link and link not in historial:
                        print(f"✨ ¡Capturado! {nombre}")
                        titulo = entrada.get('title') or (entrada.get('description', '')[:70] + "...")
                        img = extraer_imagen_premium(entrada)
                        enviar_telegram(titulo, link, img, nombre)
                        
                        with open(archivo_h, "a") as f: f.write(link + "\n")
                        historial.add(link)
                        time.sleep(3)
            else:
                print(f"❌ {nombre} bloqueó la conexión (Código {resp.status_code})")
        except Exception as e:
            print(f"⚠️ Error en {nombre}: {e}")

if __name__ == "__main__":
    main()
