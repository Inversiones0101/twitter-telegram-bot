import os
import feedparser
import requests
import time
from datetime import datetime

# --- CONFIGURACIÓN DE FUENTES ---
# Usamos rss.blue para convertir perfiles de BlueSky a RSS
FEEDS = {
    "Barchart": "https://www.barchart.com/news/authors/rss",
    "El Economista": "https://eleconomista.com.ar/finanzas/feed/",
    "TrendSpider": "https://rss.blue/user/trendspider.com",
    "BOA": "https://rss.blue/user/boa.com.ar"
}

# --- FUNCIONES DE TELEGRAM ---
def enviar_a_telegram(titulo, link, image_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Estética estilo "Fixup" / Pro
    caption = (
        f"📊 *{fuente.upper()}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 {titulo}\n\n"
        f"🔗 [Ver análisis completo]({link})"
    )
    
    if image_url:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {'chat_id': chat_id, 'photo': image_url, 'caption': caption, 'parse_mode': 'Markdown'}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': caption, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
    
    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

# --- UTILIDADES ---
def extraer_imagen(entrada):
    """Busca imágenes en diferentes formatos de RSS"""
    # 1. Buscar en media_content (BlueSky/TrendSpider)
    if 'media_content' in entrada:
        return entrada.media_content[0]['url']
    # 2. Buscar en enclosures (WordPress/El Economista)
    if 'enclosures' in entrada and entrada.enclosures:
        return entrada.enclosures[0]['url']
    # 3. Buscar en el contenido (algunos RSS de Barchart)
    if 'summary' in entrada and '<img src="' in entrada.summary:
        return entrada.summary.split('<img src="')[1].split('"')[0]
    return None

def gestionar_historial(url_noticia):
    """Evita enviar la misma noticia dos veces"""
    archivo_historial = "last_id_inicio.txt"
    if not os.path.exists(archivo_historial):
        open(archivo_historial, 'w').close()
    
    with open(archivo_historial, 'r') as f:
        historial = f.read().splitlines()
    
    if url_noticia in historial:
        return False # Ya se envió
    
    # Guardar nueva URL (mantenemos las últimas 50 para no llenar el archivo)
    historial.append(url_noticia)
    with open(archivo_historial, 'w') as f:
        f.write("\n".join(historial[-50:]))
    return True

def chequear_rava():
    """Alerta especial para el programa en vivo"""
    ahora = datetime.now()
    # Lunes a Viernes a las 09:45 (ajusta según la hora de tu servidor GitHub)
    if ahora.weekday() < 5 and ahora.hour == 9 and ahora.minute == 45:
        msg = "📺 *RAVA BURSÁTIL*\n🔔 ¡Comienza 'La Mañana del Mercado' en vivo!\n\n🔗 [Ver en YouTube](https://www.youtube.com/@RavaBursatil/live)"
        enviar_a_telegram("¡Programa en Vivo!", "https://www.youtube.com/@RavaBursatil/live", None, "RAVA")

# --- FLUJO PRINCIPAL ---
def main():
    print("Iniciando revisión de mercados...")
    
    for nombre, url in FEEDS.items():
        print(f"Chequeando {nombre}...")
        feed = feedparser.parse(url)
        
        # Revisamos las 3 entradas más recientes de cada fuente
        for entrada in feed.entries[:3]:
            link = entrada.link
            
            if gestionar_historial(link):
                titulo = entrada.title
                imagen = extraer_imagen(entrada)
                enviar_a_telegram(titulo, link, imagen, nombre)
                time.sleep(2) # Pausa breve para evitar spam
    
    chequear_rava()
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
