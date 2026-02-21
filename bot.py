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
    
    # --- CONFIGURACIÓN DE TIEMPO ---
    tz_ar = pytz.timezone('America/Argentina/Buenos_Aires')
    ahora_ar = datetime.now(tz_ar)
    fecha_hoy = ahora_ar.strftime("%Y-%m-%d")
    
    # --- 1. LÓGICA DE ALERTA RAVA (Solo una vez a partir de las 09:45 AM) ---
    archivo_rava = "ultimo_rava.txt"
    if ahora_ar.weekday() < 5 and (ahora_ar.hour == 9 and ahora_ar.minute >= 45 or ahora_ar.hour > 9):
        ultimo_envio = ""
        if os.path.exists(archivo_rava):
            with open(archivo_rava, "r") as f:
                ultimo_envio = f.read().strip()
        
        if ultimo_envio != fecha_hoy:
            link_vivo = "https://www.youtube.com/@RavaBursatil/live"
            mensaje_rava = (
                "🔔 <b>¡APERTURA DE MERCADO!</b>\n"
                "━━━━━━━━━━━━━━\n"
                "Inicia la jornada financiera. Sigan el análisis en vivo de <b>Rava Bursátil</b> aquí:\n\n"
                f"📺 <b>Ver Transmisión:</b> {link_vivo}\n"
            )
            
            url_imagen = "https://www.rava.com/assets/img/logo-rava.png"
            url_tele = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendPhoto"
            payload = {
                'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
                'photo': url_imagen,
                'caption': mensaje_rava,
                'parse_mode': 'HTML'
            }
            
            try:
                r = requests.post(url_tele, json=payload, timeout=20)
                if r.status_code != 200: raise Exception()
            except:
                enviar_telegram(mensaje_rava, None, "ALERTA RAVA")

            with open(archivo_rava, "w") as f:
                f.write(fecha_hoy)

    # --- 2. LÓGICA DEL MONITOR (Lunes a Viernes, de 10hs a 20hs) ---
    # Aquí es donde aplicamos el filtro estricto que pediste
    if ahora_ar.weekday() < 5 and 10 <= ahora_ar.hour <= 20:
        print(f"📊 {ahora_ar.strftime('%H:%M')} - Dentro de franja horaria. Enviando Monitor...")
        enviar_telegram(obtener_datos_monitor(), None, "MONITOR")
    else:
        print(f"⏳ {ahora_ar.strftime('%H:%M')} - Monitor fuera de horario (10-20hs L-V). Se omite envío.")

    # --- 3. LÓGICA DE FEEDS BLUESKY (Siempre disponible 24/7) ---
    # Esta parte no tiene filtros de horario, se ejecuta cada vez que el bot corre
    print("🌐 Procesando Feeds de BlueSky...")
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
        except Exception as e:
            print(f"Error en feed {nombre}: {e}")
            continue
            
if __name__ == "__main__":
    main()
