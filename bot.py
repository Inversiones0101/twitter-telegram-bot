import os
import feedparser
import requests
import time
import re

# --- FUENTES TÉCNICAS SELECCIONADAS ---
FEEDS = {
    "STOCK_CONSULTANT": "https://www.stockconsultant.com/consultant/rss.cgi",
    "RAVA_MERVAL": "https://www.rava.com/rss.php",
    "INVESTING_TECNICO": "https://es.investing.com/rss/market_overview_technical.rss"
}

def extraer_imagen_tecnica(entrada):
    # Prioridad 1: Enclosures (Gráficos directos de Investing/StockConsultant)
    if 'enclosures' in entrada and entrada.enclosures:
        return entrada.enclosures[0]['url']
    
    # Prioridad 2: Media Content (Formato de Rava/BlueSky)
    if 'media_content' in entrada:
        return entrada.media_content[0]['url']
    
    # Prioridad 3: Buscar en el resumen HTML (Último recurso para Rava)
    if 'summary' in entrada:
        img_match = re.search(r'<img [^>]*src="([^"]+)"', entrada.summary)
        if img_match: 
            return img_match.group(1)
            
    return None

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Formato limpio para que destaque el gráfico
    caption = f"📊 *{fuente}*\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 [Ver análisis completo]({link})"
    
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
        
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def main():
    print("🚀 Iniciando radar de gráficos técnicos...")
    archivo_h = "last_id_inicio.txt"
    
    # Cargar historial persistente
    if os.path.exists(archivo_h):
        with open(archivo_h, "r") as f:
            historial = set(f.read().splitlines())
    else:
        historial = set()

    for nombre, url in FEEDS.items():
        try:
            print(f"🔍 Revisando {nombre}...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=15)
            feed = feedparser.parse(resp.content)
            
            # Procesamos las 3 más recientes de cada fuente
            for entrada in feed.entries[:3]:
                if entrada.link not in historial:
                    print(f"✨ ¡Nueva oportunidad detectada en {nombre}!")
                    img = extraer_imagen_tecnica(entrada)
                    enviar_telegram(entrada.title, entrada.link, img, nombre)
                    
                    # Actualizar historial en memoria
                    historial.add(entrada.link)
                    
                    # Guardar inmediatamente en el archivo
                    with open(archivo_h, "a") as f:
                        f.write(entrada.link + "\n")
                    
                    time.sleep(2) # Evitar saturar la API de Telegram
        except Exception as e:
            print(f"⚠️ Fallo en {nombre}: {e}")

    print("✅ Radar completado y memoria actualizada.")

if __name__ == "__main__":
    main()
