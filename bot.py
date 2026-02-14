import os
import feedparser
import requests
import time

# --- FUENTES SELECCIONADAS ARG & USA ---
FEEDS = {
    "TrendSpider_USA": "https://rss.blue/user/trendspider.com",
    "BOA_Arg_Bonos": "https://rss.blue/user/boa.com.ar",
    "Merval_Tecnico": "https://rss.blue/user/alfredovictor.bsky.social",
    "Investing_Tecnico": "https://es.investing.com/rss/market_overview_technical.rss"
}

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Formato elegante
    caption = f"📊 *{fuente.upper()}*\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 [Abrir Gráfico]({link})"
    
    if image_url:
        url_api = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
    else:
        url_api = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
    
    try:
        r = requests.post(url_api, json=payload, timeout=10)
        return r.status_code == 200
    except:
        return False

def extraer_imagen(entrada):
    # Lógica múltiple para no perder ningún gráfico
    if 'media_content' in entrada: return entrada.media_content[0]['url']
    if 'enclosures' in entrada and entrada.enclosures: return entrada.enclosures[0]['url']
    if 'summary' in entrada and '<img' in entrada.summary:
        try: return entrada.summary.split('src="')[1].split('"')[0]
        except: pass
    return None

def main():
    print("🚀 Iniciando radar de gráficos...")
    archivo_h = "last_id_inicio.txt"
    
    # Leer historial si existe
    historial = []
    if os.path.exists(archivo_h):
        with open(archivo_h, "r") as f:
            historial = f.read().splitlines()

    nuevas_urls = []
    
    for nombre, url in FEEDS.items():
        print(f"🔍 Revisando {nombre}...")
        feed = feedparser.parse(url)
        
        # Tomamos solo los 2 últimos para no saturar en el primer arranque
        for entrada in feed.entries[:2]:
            if entrada.link not in historial:
                print(f"✨ ¡Nueva oportunidad encontrada en {nombre}!")
                img = extraer_imagen(entrada)
                if enviar_telegram(entrada.title, entrada.link, img, nombre):
                    nuevas_urls.append(entrada.link)
                    time.sleep(3) # Pausa de seguridad

    # Guardar progreso
    with open(archivo_h, "a") as f:
        for u in nuevas_urls:
            f.write(u + "\n")
    
    print("✅ Radar completado.")

if __name__ == "__main__":
    main()
