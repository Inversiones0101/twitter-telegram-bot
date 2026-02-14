import os
import feedparser
import requests
import time

# --- FUENTES 100% GRÁFICAS (Sacamos Ámbito por ahora porque solo manda billetes) ---
FEEDS = {
    "STOCK_CONSULTANT": "https://www.stockconsultant.com/consultant/rss.cgi", # Gráficos USA
    "RAVA_MERVAL": "https://www.rava.com/rss.php", # El panel de Argentina
    "INVESTING_TECNICO": "https://es.investing.com/rss/market_overview_technical.rss" # Velas Japonesas
}

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Si la imagen es del billete de 100 de Ámbito, la ignoramos para buscar una mejor
    if image_url and "ambito.com" in image_url and "dolar" in image_url:
        image_url = None

    caption = f"📊 *{fuente}*\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 [Ver Gráfico Completo]({link})"
    
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
        
        requests.post(url, json=payload, timeout=10)
    except: pass

def main():
    print("🚀 Iniciando radar sin repeticiones...")
    # El truco para no repetir: GitHub Actions necesita que el historial sea persistente
    archivo_h = "last_id_inicio.txt"
    
    if os.path.exists(archivo_h):
        with open(archivo_h, "r") as f:
            historial = set(f.read().splitlines())
    else:
        historial = set()

    nuevas_noticias = []

    for nombre, url in FEEDS.items():
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            feed = feedparser.parse(resp.content)
            
            for entrada in feed.entries[:3]:
                if entrada.link not in historial:
                    print(f"✨ Nueva noticia técnica en {nombre}")
                    
                    # Buscamos la imagen en la etiqueta correcta (enclosure)
                    img = None
                    if 'enclosures' in entrada and entrada.enclosures:
                        img = entrada.enclosures[0]['url']
                    
                    enviar_telegram(entrada.title, entrada.link, img, nombre)
                    historial.add(entrada.link)
                    nuevas_noticias.append(entrada.link)
                    time.sleep(2)
        except:
            print(f"⚠️ Error en {nombre}")

    # Guardamos el historial actualizado
    with open(archivo_h, "w") as f:
        for link in historial:
            f.write(link + "\n")

if __name__ == "__main__":
    main()
