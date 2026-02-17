import os
import feedparser
import requests
import time
import re
import yfinance as yf
from datetime import datetime
import pytz

# --- CONFIGURACIÓN DE FEEDS ---
FEEDS = {
    "AMBITO_DOLAR": "https://bsky.app/profile/ambitodolar.bsky.social/rss",
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss",
    "BARCHART_BSKY": "https://bsky.app/profile/barchart.com/rss"
}

# --- CONFIGURACIÓN DE ACTIVOS (Monitor Inteligente) ---
MARKETS = {
    "WALL_STREET": {
        "^SPX": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ", 
        "^VIX": "VIX", "^TNX": "Tasa 10Y", "ZS=F": "Soja"
    },
    "24_7_MARKET": {
        "CL=F": "Petróleo", "GC=F": "Oro", "SI=F": "Plata",
        "BTC-USD": "BTC", "ETH-USD": "ETH", "SOL-USD": "SOL"
    }
}

def esta_abierto_wall_street():
    """Verifica el horario de Wall Street (9:30-16:00 EST)"""
    tz_ny = pytz.timezone('America/New_York')
    ahora_ny = datetime.now(tz_ny)
    if ahora_ny.weekday() >= 5: return False 
    apertura = ahora_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    cierre = ahora_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    return apertura <= ahora_ny <= cierre

def obtener_datos_monitor():
    """Genera el texto del monitor con colores y estado del mercado"""
    lineas = ["🏦 <b>MONITOR DE MERCADOS</b>", "━━━━━━━━━━━━━━"]
    ws_abierto = esta_abierto_wall_street()
    estado_ws = "🟢 <b>ABIERTO</b>" if ws_abierto else "🔴 <b>CERRADO</b>"
    
    lineas.append(f"\n🇺🇸 <b>Wall Street:</b> {estado_ws}")
    for ticker, nombre in MARKETS["WALL_STREET"].items():
        try:
            val = yf.Ticker(ticker).history(period="2d")
            precio = val['Close'].iloc[-1]
            cambio = ((precio / val['Close'].iloc[-2]) - 1) * 100
            emoji = "🟢" if cambio >= 0 else "🔴"
            lineas.append(f"{emoji} {nombre}: {precio:,.2f} ({cambio:+.2f}%)")
        except: continue

    lineas.append(f"\n🌍 <b>Global 24/7:</b> 🟢 <b>ABIERTO</b>")
    for ticker, nombre in MARKETS["24_7_MARKET"].items():
        try:
            val = yf.Ticker(ticker).history(period="2d")
            precio = val['Close'].iloc[-1]
            cambio = ((precio / val['Close'].iloc[-2]) - 1) * 100
            emoji = "🟢" if cambio >= 0 else "🔴"
            lineas.append(f"{emoji} {nombre}: {precio:,.2f} ({cambio:+.2f}%)")
        except: continue
    return "\n".join(lineas)

def extraer_foto(entrada):
    """Detecta imágenes en feeds internacionales y locales"""
    if 'media_content' in entrada and entrada.media_content: return entrada.media_content[0]['url']
    if 'enclosures' in entrada and entrada.enclosures: return entrada.enclosures[0]['url']
    summary = entrada.get('summary', '') or entrada.get('description', '')
    match = re.search(r'src="([^"]+)"', summary)
    return match.group(1) if match else None

def enviar_telegram(titulo, link, img_url, fuente):
    """Envía el contenido a Telegram con formato profesional"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Encabezado con emoji según fuente
    emoji_fuente = "📊" if fuente == "MONITOR" else "🎯"
    caption = f"{emoji_fuente} <b>{fuente}</b>\n━━━━━━━━━━━━━━\n{titulo}"
    if link: caption += f"\n\n🔗 <a href='{link}'>Ver en BlueSky</a>"

    try:
        if img_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {'chat_id': chat_id, 'photo': img_url, 'caption': caption, 'parse_mode': 'HTML'}
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
        requests.post(url, json=payload, timeout=30)
    except Exception as e: print(f"Error: {e}")

def main():
    print("🚀 Iniciando Súper Bot Financiero (Monitor + Radar)...")
    
    # 1. Enviar el Monitor Inteligente siempre
    enviar_telegram(obtener_datos_monitor(), None, None, "MONITOR")
    
    # 2. Procesar Feeds de BlueSky
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h): open(archivo_h, "w").close()
    with open(archivo_h, "r") as f: historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            resp = requests.get(url, timeout=30)
            feed = feedparser.parse(resp.content)
            for entrada in reversed(feed.entries[:3]):
                link = entrada.get('link')
                if link and link not in historial:
                    contenido = entrada.get('description', entrada.get('title', ''))
                    
                    # Filtro específico para Ámbito Dólar
                    if nombre == "AMBITO_DOLAR":
                        if "APERTURA" not in contenido.upper() and "CIERRE" not in contenido.upper():
                            continue
                    
                    img = extraer_foto(entrada)
                    enviar_telegram(contenido[:250], link, img, nombre)
                    
                    with open(archivo_h, "a") as f: f.write(link + "\n")
                    historial.add(link)
                    time.sleep(2)
        except Exception as e: print(f"Error en {nombre}: {e}")

if __name__ == "__main__":
    main()
