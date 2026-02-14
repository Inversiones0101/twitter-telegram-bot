import os
import feedparser
import requests
import time

# --- FUENTES 100% VISUALES Y TÉCNICAS ---
FEEDS = {
    "TrendSpider_USA": "https://rss.blue/user/trendspider.com",
    "BOA_Arg_Bonos": "https://rss.blue/user/boa.com.ar",
    "Merval_Tecnico": "https://rss.blue/user/alfredovictor.bsky.social",
    "Investing_Tecnico": "https://es.investing.com/rss/market_overview_technical.rss"
}

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Diseño limpio para que el gráfico destaque
    caption = f"📈 *{fuente.upper()}*\n\n{titulo}\n\n🔗 [Ver análisis]({link})"
    
    if image_url:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
    else:
        # Si no hay imagen, mandamos mensaje con vista previa de link
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
    
    requests.post(url, json=payload)

def extraer_imagen(entrada):
    # Lógica específica para capturar fotos de BlueSky y Investing
    if 'media_content' in entrada:
        return entrada.media_content[0]['url']
    if 'enclosures' in entrada and entrada.enclosures:
        return entrada.enclosures[0]['url']
    return None

def main():
    # Usamos un set para el historial en memoria durante la ejecución
    if not os.path.exists("last_id_inicio.txt"):
        open("last_id_inicio.txt", "w").close()

    with open("last_id_inicio.txt", "r") as f:
        historial = set(f.read().splitlines())

    nuevas_urls = []

    for nombre, url in FEEDS.items():
        feed = feedparser.parse(url)
        for entrada in feed.entries[:5]: # Miramos las últimas 5
            if entrada.link not in historial:
                print(f"Nueva entrada en {nombre}")
                imagen = extraer_imagen(entrada)
                enviar_telegram(entrada.title, entrada.link, imagen, nombre)
                nuevas_urls.append(entrada.link)
                time.sleep(2)

    # Guardar en el archivo para no repetir mañana
    with open("last_id_inicio.txt", "a") as f:
        for url in nuevas_urls:
            f.write(url + "\n")

if __name__ == "__main__":
    main()
