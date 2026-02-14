import os
import feedparser
import requests
import time
import re

# --- CONFIGURACIÓN ---
FEEDS = {
    "TRENDSPIDER_BSKY": "https://rss.blue/user/trendspider.com",
    "STOCK_CONSULTANT": "https://www.stockconsultant.com/consultant/rss.cgi"
}

def extraer_imagen_premium(entrada):
    # 1. Prioridad absoluta a imágenes de BlueSky/TrendSpider
    if 'media_content' in entrada:
        return entrada.media_content[0]['url']
    
    # 2. Búsqueda en el cuerpo del mensaje (StockConsultant)
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
            payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code == 200: return

        # Si no hay foto o falla, enviamos texto
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
        requests.post(url, json=payload, timeout=20)
    except: pass

def obtener_feed_con_reintentos(url, max_intentos=3):
    """Intenta conectar varias veces si el servidor está saturado"""
    for i in range(max_intentos):
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=35)
            if resp.status_code == 200:
                return feedparser.parse(resp.content)
        except:
            print(f"⏳ Intento {i+1} fallido, esperando...")
            time.sleep(10)
    return None

def main():
    print("🚀 Iniciando Radar con Reintentos...")
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h):
        with open(archivo_h, "w") as f: f.write("")

    with open(archivo_h, "r") as f:
        historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        print(f"🔍 Escaneando {nombre}...")
        feed = obtener_feed_con_reintentos(url)
        
        if feed and feed.entries:
            for entrada in feed.entries[:2]:
                if entrada.link not in historial:
                    print(f"✨ ¡Capturando novedad en {nombre}!")
                    img = extraer_imagen_premium(entrada)
                    enviar_telegram(entrada.title, entrada.link, img, nombre)
                    
                    with open(archivo_h, "a") as f:
                        f.write(entrada.link + "\n")
                    historial.add(entrada.link)
                    time.sleep(5)
                else:
                    print(f"⏩ {nombre}: Ya procesado.")
        else:
            print(f"⚠️ No se pudo conectar con {nombre} tras varios intentos.")

if __name__ == "__main__":
    main()
