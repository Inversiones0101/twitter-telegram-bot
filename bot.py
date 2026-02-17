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

# --- CONFIGURACIÓN DE ACTIVOS (Tickers Optimizados) ---
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
    tz_ny = pytz.timezone('America/New_York')
    ahora_ny = datetime.now(tz_ny)
    if ahora_ny.weekday() >= 5: return False 
    apertura = ahora_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    cierre = ahora_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    return apertura <= ahora_ny <= cierre

def obtener_datos_monitor():
    lineas = ["🏦 <b>MONITOR DE MERCADOS</b>", "━━━━━━━━━━━━━━"]
    
    # 1. Estado de Wall Street
    abierto = esta_abierto_wall_street()
    estado_ws = "🟢 <b>ABIERTO</b>" if abierto else "🔴 <b>CERRADO</b>"
    
    # --- SECCIÓN WALL STREET ---
    lineas.append(f"\n🇺🇸 <b>WALL STREET:</b> {estado_ws}")
    for ticker, nombre in MARKETS["WALL_STREET"].items():
        try:
            # Usamos period="5d" para asegurar que siempre haya datos de cierre previo
            val = yf.Ticker(ticker).history(period="5d")
            if len(val) < 2: continue
            precio = val['Close'].iloc[-1]
            cambio = ((precio / val['Close'].iloc[-2]) - 1) * 100
            emoji = "🟢" if cambio >= 0 else "🔴"
            
            if ticker == "^TNX":
                lineas.append(f"{emoji} {nombre}: {precio:.2f}% ({cambio:+.2f}%)")
            else:
                lineas.append(f"{emoji} {nombre}: {precio:,.2f} ({cambio:+.2f}%)")
        except: continue

    # --- SECCIÓN COMMODITIES ---
    lineas.append(f"\n🧱 <b>COMMODITIES:</b> 🟢 <b>ABIERTO</b>")
    for ticker, nombre in MARKETS["COMMODITIES"].items():
        try:
            val = yf.Ticker(ticker).history(period="5d")
            if len(val) < 2: continue
            precio = val['Close'].iloc[-1]
            cambio = ((precio / val['Close'].iloc[-2]) - 1) * 100
            emoji = "🟢" if cambio >= 0 else "🔴"
            lineas.append(f"{emoji} {nombre}: {precio:,.2f} ({cambio:+.2f}%)")
        except: continue

    # --- SECCIÓN CRYPTOS ---
    lineas.append(f"\n🪙 <b>CRYPTOS:</b> 🟢 <b>ABIERTO</b>")
    for ticker, nombre in MARKETS["CRYPTOS"].items():
        try:
            val = yf.Ticker(ticker).history(period="5d")
            if len(val) < 2: continue
            precio = val['Close'].iloc[-1]
            cambio = ((precio / val['Close'].iloc[-2]) - 1) * 100
            emoji = "🟢" if cambio >= 0 else "🔴"
            lineas.append(f"{emoji} {nombre}: ${precio:,.2f} ({cambio:+.2f}%)")
        except: continue
        
    return "\n".join(lineas)

def enviar_telegram(titulo, link, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not link:
        mensaje = f"🏦 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n{titulo}"
        disable_preview = True
    else:
        mensaje = f"🎯 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 {link}"
        disable_preview = False 

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'HTML',
        'disable_web_page_preview': disable_preview
    }
    requests.post(url, json=payload, timeout=25)

def main():
    print("🚀 Ejecutando Monitor y Radar...")
    
    # --- LÓGICA DE ALERTA RAVA (Primera ejecución de la mañana) ---
    tz_ar = pytz.timezone('America/Argentina/Buenos_Aires')
    ahora_ar = datetime.now(tz_ar)
    fecha_hoy = ahora_ar.strftime("%Y-%m-%d")
    archivo_rava = "ultimo_rava.txt"
    
    # Si la hora es después de las 9:00 AM y antes de las 11:00 AM
    if 9 <= ahora_ar.hour < 11:
        # Revisamos si ya enviamos la alerta hoy
        ultimo_envio = ""
        if os.path.exists(archivo_rava):
            with open(archivo_rava, "r") as f:
                ultimo_envio = f.read().strip()
        
        if ultimo_envio != fecha_hoy:
            mensaje_rava = (
                "🔔 <b>¡APERTURA DE MERCADO!</b>\n"
                "━━━━━━━━━━━━━━\n"
                "Inicia la jornada financiera. Sigan el análisis en vivo en el canal de <b>Rava Bursátil</b>.\n\n"
                "📺 <b>Ver aquí:</b> https://www.youtube.com/@RavaBursatil"
            )
            enviar_telegram(mensaje_rava, None, "ALERTA RAVA")
            # Guardamos la fecha para no repetir hoy
            with open(archivo_rava, "w") as f:
                f.write(fecha_hoy)

    # --- RESTO DEL BOT (Monitor y Feeds) ---
    # 1. Enviar el Monitor Pro
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
                    texto_limpio = re.sub(r'<[^>]+>', '', desc)
                    
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
