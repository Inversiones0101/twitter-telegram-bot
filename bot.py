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

# --- CONFIGURACIÓN DE ACTIVOS (Ordenado por Secciones) ---
MARKETS = {
    "WALL_STREET": {
        "^SPX": "S&P 500", 
        "^DJI": "Dow Jones", 
        "^IXIC": "NASDAQ", 
        "^VIX": "VIX", 
        "^TNX": "Tasa 10Y"
    },
    "COMMODITIES": {
        "GC=F": "🟡 Gold", 
        "ZS=F": "🟡 Soja", 
        "CL=F": "🛢️ Oil", 
        "SI=F": "⚪ Silver"
    },
    "CRYPTOS": {
        "BTC-USD": "BTC", 
        "ETH-USD": "ETH", 
        "SOL-USD": "SOL"
    }
}

def esta_abierto_wall_street():
    """Verifica si el mercado de NY está operando (9:30 - 16:00 EST)"""
    tz_ny = pytz.timezone('America/New_York')
    ahora_ny = datetime.now(tz_ny)
    if ahora_ny.weekday() >= 5: return False 
    apertura = ahora_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    cierre = ahora_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    return apertura <= ahora_ny <= cierre

def obtener_datos_monitor():
    """Genera el mensaje del Monitor con secciones separadas"""
    lineas = ["🏦 <b>MONITOR DE MERCADOS</b>", "━━━━━━━━━━━━━━"]
    
    # 1. Primero definimos el estado de Wall Street
    abierto = esta_abierto_wall_street()
    estado_ws = "🟢 <b>ABIERTO</b>" if abierto else "🔴 <b>CERRADO</b>"
    
    # --- SECCIÓN WALL STREET ---
    lineas.append(f"\n🇺🇸 <b>WALL STREET:</b> {estado_ws}")
    for ticker, nombre in MARKETS["WALL_STREET"].items():
        try:
            val = yf.Ticker(ticker).history(period="2d")
            if val.empty: continue
            precio = val['Close'].iloc[-1]
            cambio = ((precio / val['Close'].iloc[-2]) - 1) * 100
            emoji = "🟢" if cambio >= 0 else "🔴"
            # Formato especial para la Tasa 10Y
            formato = f"{precio:.2f}%" if ticker == "^TNX" else f"{precio:,.2f}"
            lineas.append(f"{emoji} {nombre}: {formato} ({cambio:+.2f}%)")
        except: continue

    # --- SECCIÓN COMMODITIES ---
    lineas.append(f"\n🧱 <b>COMMODITIES:</b> 🟢 <b>ABIERTO</b>")
    for ticker, nombre in MARKETS["COMMODITIES"].items():
        try:
            val = yf.Ticker(ticker).history(period="2d")
            if val.empty: continue
            precio = val['Close'].iloc[-1]
            cambio = ((precio / val['Close'].iloc[-2]) - 1) * 100
            emoji = "🟢" if cambio >= 0 else "🔴"
            lineas.append(f"{emoji} {nombre}: {precio:,.2f} ({cambio:+.2f}%)")
        except: continue

    # --- SECCIÓN CRYPTOS ---
    lineas.append(f"\n🪙 <b>CRYPTOS:</b> 🟢 <b>ABIERTO</b>")
    for ticker, nombre in MARKETS["CRYPTOS"].items():
        try:
            val = yf.Ticker(ticker).history(period="2d")
            if val.empty: continue
            precio = val['Close'].iloc[-1]
            cambio = ((precio / val['Close'].iloc[-2]) - 1) * 100
            emoji = "🟢" if cambio >= 0 else "🔴"
            lineas.append(f"{emoji} {nombre}: ${precio:,.2f} ({cambio:+.2f}%)")
        except: continue
        
    return "\n".join(lineas)

def enviar_telegram(titulo, link, fuente):
    """Envia mensajes con o sin Vista Previa de imagen"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not link:
        # Mensaje del Monitor (Texto puro)
        mensaje = f"🏦 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n{titulo}"
        disable_preview = True
    else:
        # Mensaje de BlueSky (Con link para generar vista previa)
        mensaje = f"🎯 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 {link}"
        disable_preview = False 

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'HTML',
        'disable_web_page_preview': disable_preview
    }
    try:
        requests.post(url, json=payload, timeout=25)
    except Exception as e:
        print(f"Error en Telegram: {e}")

def main():
    print("🚀 Iniciando Bot Informativo...")
    
    # 1. Enviar Monitor siempre que corra el script
    enviar_telegram(obtener_datos_monitor(), None, "MONITOR")
    
    # 2. Procesar Feeds de BlueSky
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h): open(archivo_h, "w").close()
    with open(archivo_h, "r") as f: historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            feed = feedparser.parse(requests.get(url, timeout=30).content)
            for entrada in reversed(feed.entries[:5]):
                link = entrada.get('link')
                if link and link not in historial:
                    desc = entrada.get('description', entrada.get('title', ''))
                    # Limpiamos HTML
                    texto_limpio = re.sub(r'<[^>]+>', '', desc)
                    
                    # Filtro exclusivo para Ámbito Dólar
                    if nombre == "AMBITO_DOLAR":
                        if "APERTURA" not in texto_limpio.upper() and "CIERRE" not in texto_limpio.upper():
                            continue
                    
                    enviar_telegram(texto_limpio[:450], link, nombre)
                    
                    with open(archivo_h, "a") as f: f.write(link + "\n")
                    historial.add(link)
                    time.sleep(2)
        except: continue

if __name__ == "__main__":
    main()
