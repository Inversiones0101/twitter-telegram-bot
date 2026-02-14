import os
import feedparser
import requests
import time

# --- FUENTES 100% OPERATIVAS ---
FEEDS = {
    "StockConsultant_USA": "https://www.stockconsultant.com/consultant/rss.cgi",
    "TrendSpider_USA": "https://rss.blue/user/trendspider.com",
    "Merval_Investing": "https://es.investing.com/rss/market_overview_Argentina.rss",
    "BOA_Arg_Bonos": "https://rss.blue/user/boa.com.ar"
}

def extraer_imagen(entrada):
    # Buscamos en todas las etiquetas posibles para no perder el gráfico
    if 'media_content' in entrada: return entrada.media_content[0]['url']
    if 'enclosures' in entrada and entrada.enclosures: return entrada.enclosures[0]['url']
    if 'summary' in entrada and '<img' in entrada.summary:
        try: return entrada.summary.split('src="')[1].split('"')[0]
        except: pass
    return None

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    caption = f"📊 *{fuente.upper()}*\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 [Ver análisis]({link})"
    
    # Si hay imagen, intentamos mandar foto; si falla o no hay, mandamos texto
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200: return
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
        requests.post(url, json=payload, timeout=10)
    except:
        print(f"Error enviando a Telegram desde {fuente}")

def main():
    print("🚀 Iniciando radar de alta velocidad...")
    archivo_h = "last_id_inicio.txt"
    historial = open(archivo_h, "r").read().splitlines() if os.path.exists(archivo_h) else []

    for nombre, url in FEEDS.items():
        try:
            print(f"🔍 Revisando {nombre}...")
            # Usamos un User-Agent para que no nos bloqueen como bots
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=15)
            feed = feedparser.parse(resp.content)
            
            for entrada in feed.entries[:2]: # Solo los 2 últimos para probar
                if entrada.link not in historial:
                    print(f"✨ Nueva entrada en {nombre}")
                    img = extraer_imagen(entrada)
                    enviar_telegram(entrada.title, entrada.link, img, nombre)
                    with open(archivo_h, "a") as f: f.write(entrada.link + "\n")
                    time.sleep(2)
        except:
            print(f"⚠️ {nombre} no respondió rápido, saltando...")

    print("✅ Proceso terminado.")

if __name__ == "__main__":
    main()
