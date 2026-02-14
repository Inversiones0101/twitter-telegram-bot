import os
import feedparser
import requests
import time
import re

# --- FUENTES RE-DIRECCIONADAS ---
FEEDS = {
    # Usamos un puente alternativo para BlueSky (más estable)
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss", 
    "STOCK_CONSULTANT": "https://www.stockconsultant.com/consultant/rss.cgi"
}

def extraer_imagen_premium(entrada):
    # 1. Buscar imagen en los campos estándar de RSS
    if 'media_content' in entrada: return entrada.media_content[0]['url']
    if 'enclosures' in entrada and entrada.enclosures: return entrada.enclosures[0]['url']
    
    # 2. Búsqueda manual en el texto (StockConsultant)
    content = entrada.get('summary', '') + entrada.get('description', '')
    img_match = re.search(r'src="([^"]+)"', content)
    if img_match:
        url = img_match.group(1)
        return 'https:' + url if url.startswith('//') else url
    return None

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    caption = f"🎯 *{fuente}*\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 [Ver análisis]({link})"
    
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            # Si la imagen es muy grande, Telegram puede tardar, bajamos el timeout a 15s pero con retry
            requests.post(url, json={'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown'}, timeout=15)
    except:
        pass

def main():
    print("🚀 Iniciando Radar de Emergencia...")
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h):
        with open(archivo_h, "w") as f: f.write("")

    with open(archivo_h, "r") as f:
        historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            print(f"🔍 Conectando a {nombre}...")
            # Usamos un User-Agent de navegador real para que no nos bloqueen
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
            resp = requests.get(url, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                for entrada in feed.entries[:2]:
                    if entrada.link not in historial:
                        print(f"✨ ¡Bingo! Noticia encontrada en {nombre}")
                        img = extraer_imagen_premium(entrada)
                        enviar_telegram(entrada.title, entrada.link, img, nombre)
                        
                        with open(archivo_h, "a") as f: f.write(entrada.link + "\n")
                        historial.add(entrada.link)
                        time.sleep(2)
            else:
                print(f"❌ {nombre} devolvió error {resp.status_code}")
        except Exception as e:
            print(f"⚠️ Error de conexión en {nombre}: {e}")

if __name__ == "__main__":
    main()
