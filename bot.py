import os
import feedparser
import requests
import time
import re
import yfinance as yf

# --- CONFIGURACIÓN DE FEEDS (Agregamos El País para testear imágenes) ---
FEEDS = {
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss",
    "BARCHART_BSKY": "https://bsky.app/profile/barchart.com/rss"
}

def extraer_imagen_premium(entrada):
    # 1. Prioridad: Media content (BlueSky nativo)
    if 'media_content' in entrada and entrada.media_content:
        return entrada.media_content[0]['url']
    
    # 2. Enclosures (RSS estándar)
    if 'enclosures' in entrada and entrada.enclosures:
        return entrada.enclosures[0]['url']
    
    # 3. REFUERZO: Buscar en el sumario (Ideal para El País / Noticias)
    if 'summary' in entrada:
        img_match = re.search(r'src="([^"]+)"', entrada.summary)
        if img_match: return img_match.group(1)
        
    return None

def enviar_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not link:
        # Formato para el Monitor de Precios
        mensaje = f"🏦 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n{titulo}"
        disable_preview = True
    else:
        # Formato con link para que Telegram genere la card automáticamente
        mensaje = f"🎯 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 {link}"
        disable_preview = False 

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'HTML',
        'disable_web_page_preview': disable_preview
    }
    requests.post(url, json=payload, timeout=20)

def obtener_cuadro_mercado():
    activos = {
        "🇦🇷 MERVAL": "^MERV",
        "🇺🇸 S&P 500": "^GSPC",
        "🗽 DÓLAR CCL": "GGAL.BA", 
        "📉 AL30": "AL30.BA"
    }
    
    mensaje = "🏦 <b>MONITOR DE PRECIOS</b>\n━━━━━━━━━━━━━━\n"
    
    for nombre, ticker in activos.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if len(data) >= 2:
                actual = data['Close'].iloc[-1]
                anterior = data['Close'].iloc[-2]
                var = ((actual - anterior) / anterior) * 100
                color = "🟢" if var > 0 else "🔴"
                # Formato tipo tarjeta
                mensaje += f"<b>{nombre}</b> | {actual:,.2f} | {color} {var:+.2f}%\n"
        except:
            continue
            
    return mensaje + "━━━━━━━━━━━━━━"

def main():
    print("🚀 Iniciando Radar BlueSky...")
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h):
        with open(archivo_h, "w") as f: f.write("")

    with open(archivo_h, "r") as f:
        historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                for entrada in reversed(feed.entries[:3]):
                    link = entrada.get('link')
                    if link and link not in historial:
                        titulo = entrada.get('title') or (entrada.get('description', '')[:70] + "...")
                        img = extraer_imagen_premium(entrada)
                        enviar_telegram(titulo, link, img, nombre)
                        with open(archivo_h, "a") as f: f.write(link + "\n")
                        historial.add(link)
                        time.sleep(2)
        except Exception as e:
            print(f"Error en {nombre}: {e}")

if __name__ == "__main__":
    # 1. Buscamos novedades en BlueSky
    main()
    
    # 2. Mandamos el Monitor de Precios
    print("📊 Enviando Monitor...")
    reporte = obtener_cuadro_mercado()
    enviar_telegram(reporte, None, None, "SISTEMA_MONITOR")
