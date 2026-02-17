import os
import feedparser
import requests
import time
import re

# --- CONFIGURACIÓN DE FEEDS ---
FEEDS = {
    "ECONOMISTA_AR": "https://bsky.app/profile/eleconomista.com.ar.web.brid.gy/rss",
    "FINCOINS_GLOBAL": "https://bsky.app/profile/fincoins.bsky.social/rss",
    "AMBITO_DOLAR": "https://bsky.app/profile/ambitodolar.bsky.social/rss",
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss",
    "BARCHART_BSKY": "https://bsky.app/profile/barchart.com/rss"
}

def extraer_foto(entrada):
    """Busca la URL de la imagen en los campos comunes del RSS de BlueSky."""
    # Opción 1: Media content (estándar)
    if 'media_content' in entrada and entrada.media_content:
        return entrada.media_content[0]['url']
    # Opción 2: Enclosures (adjuntos)
    if 'enclosures' in entrada and entrada.enclosures:
        return entrada.enclosures[0]['url']
    # Opción 3: Buscar en el resumen (summary) con regex
    summary = entrada.get('summary', '')
    match = re.search(r'src="([^"]+)"', summary)
    if match:
        return match.group(1)
    return None

def enviar_telegram(titulo, link, img_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Diseño limpio: Título en negrita y link discreto
    caption = f"🎯 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n📝 {titulo}\n\n🔗 <a href='{link}'>Ver en BlueSky</a>"

    try:
        if img_url:
            # SI HAY IMAGEN: Se manda como FOTO (Modo Tarjeta)
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {
                'chat_id': chat_id,
                'photo': img_url,
                'caption': caption,
                'parse_mode': 'HTML'
            }
        else:
            # SI NO HAY IMAGEN: Solo texto y MATAMOS la previsualización fea
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': caption,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def main():
    print("🚀 Iniciando Bot Informador Visual...")
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
                
                # Procesamos las últimas entradas
                for entrada in reversed(feed.entries[:5]):
                    link = entrada.get('link')
                    if link and link not in historial:
                        titulo = entrada.get('title', '')
                        titulo_up = titulo.upper()
                        
                        # --- FILTRO ÁMBITO DÓLAR (Solo lo visual) ---
                        if nombre == "AMBITO_DOLAR":
                            if "APERTURA DE JORNADA" not in titulo_up and "CIERRE DE JORNADA" not in titulo_up:
                                continue 
                        
                        # Intentamos capturar la imagen
                        img = extraer_foto(entrada)
                        
                        enviar_telegram(titulo, link, img, nombre)
                        
                        # Guardar en historial
                        with open(archivo_h, "a") as f:
                            f.write(link + "\n")
                        historial.add(link)
                        time.sleep(2)
        except Exception as e:
            print(f"Error procesando {nombre}: {e}")

if __name__ == "__main__":
    main()
