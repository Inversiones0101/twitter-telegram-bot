import os
import feedparser
import requests
import time
import re

# --- SOLO EL DÚO DINÁMICO ---
FEEDS = {
    "TRENDSPIDER_BSKY": "https://rss.blue/user/trendspider.com",
    "STOCK_CONSULTANT": "https://www.stockconsultant.com/consultant/rss.cgi"
}

def extraer_imagen_premium(entrada):
    # 1. Prioridad BlueSky (TrendSpider)
    if 'media_content' in entrada:
        return entrada.media_content[0]['url']
    
    # 2. Prioridad StockConsultant (Gráficos de Breakout)
    content = entrada.get('summary', '') + entrada.get('description', '')
    img_match = re.search(r'src="([^"]+)"', content)
    if img_match:
        img_url = img_match.group(1)
        return 'https:' + img_url if img_url.startswith('//') else img_url
        
    # 3. Enclosures genéricos
    if 'enclosures' in entrada and entrada.enclosures:
        return entrada.enclosures[0]['url']
    
    return None

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    caption = f"🎯 *{fuente}*\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 [Ver Gráfico]({link})"
    
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code == 200: return
            
        # Si falla la imagen, mandamos el link igual para no perder el trade
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
        requests.post(url, json=payload, timeout=20)
    except:
        pass

def main():
    print("🚀 Iniciando Radar Dúo Dinámico...")
    archivo_h = "last_id_inicio.txt"
    historial = set(open(archivo_h, "r").read().splitlines()) if os.path.exists(archivo_h) else set()

    for nombre, url in FEEDS.items():
        try:
            print(f"🔍 Buscando en {nombre}...")
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=25)
            feed = feedparser.parse(resp.content)
            
            # Solo procesamos el ÚLTIMO post de cada uno para máxima precisión
            if feed.entries:
                ultima_entrada = feed.entries[0]
                if ultima_entrada.link not in historial:
                    print(f"✨ ¡Nuevo posteo detectado en {nombre}!")
                    img = extraer_imagen_premium(ultima_entrada)
                    enviar_telegram(ultima_entrada.title, ultima_entrada.link, img, nombre)
                    
                    with open(archivo_h, "a") as f:
                        f.write(ultima_entrada.link + "\n")
                    historial.add(ultima_entrada.link)
                else:
                    print(f"⏩ Sin novedades en {nombre}")
        except Exception as e:
            print(f"⚠️ Error en {nombre}: {e}")

if __name__ == "__main__":
    main()
