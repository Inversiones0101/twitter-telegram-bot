import os
import feedparser
import requests
import time

# --- FUENTES TÉCNICAS USA & ARG ---
FEEDS = {
    "Ambito_Finanzas": "https://www.ambito.com/rss/pages/finanzas.xml",
    "StockConsultant_USA": "https://www.stockconsultant.com/consultant/rss.cgi",
    "Investing_Argentina": "https://es.investing.com/rss/market_overview_Argentina.rss",
    "Investing_Tecnico_USA": "https://es.investing.com/rss/market_overview_technical.rss"
}

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    caption = f"📊 *{fuente.upper()}*\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 [Ver análisis]({link})"
    
    try:
        if image_url:
            # Intentamos enviar con foto
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200: return
            
        # Si no hay imagen o falló, enviamos solo texto para no perder la noticia
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error en {fuente}: {e}")

def main():
    print("🚀 Iniciando radar financiero...")
    archivo_h = "last_id_inicio.txt"
    historial = open(archivo_h, "r").read().splitlines() if os.path.exists(archivo_h) else []

    for nombre, url in FEEDS.items():
        try:
            print(f"🔍 Revisando {nombre}...")
            # Usamos headers para que no nos bloqueen
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            feed = feedparser.parse(resp.content)
            
            for entrada in feed.entries[:3]: # Traemos los últimos 3 de cada uno
                if entrada.link not in historial:
                    # Extraer imagen (investing usa 'enclosures')
                    img = None
                    if 'enclosures' in entrada and entrada.enclosures:
                        img = entrada.enclosures[0]['url']
                    
                    enviar_telegram(entrada.title, entrada.link, img, nombre)
                    with open(archivo_h, "a") as f: f.write(entrada.link + "\n")
                    time.sleep(2)
        except:
            print(f"⚠️ {nombre} lento, saltando...")
    print("✅ Radar completado.")

if __name__ == "__main__":
    main()
