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
    """Busca la imagen de la placa en todos los rincones del post"""
    # 1. Buscar en links adjuntos
    if 'links' in entrada:
        for link in entrada.links:
            if 'image' in link.get('type', ''): return link.href
    # 2. Buscar en media_content
    if 'media_content' in entrada and entrada.media_content:
        return entrada.media_content[0]['url']
    # 3. Buscar con lupa (regex) en el contenido HTML del post
    summary = entrada.get('summary', '') or entrada.get('description', '')
    match = re.search(r'src="([^"]+)"', summary)
    if match: return match.group(1)
    return None

def enviar_telegram(titulo, link, img_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Caption limpio y prolijo
    caption = f"🎯 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n{titulo}\n\n🔗 <a href='{link}'>Ver en BlueSky</a>"

    try:
        if img_url:
            # SI HAY FOTO: La manda como el cuadro principal
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {'chat_id': chat_id, 'photo': img_url, 'caption': caption, 'parse_mode': 'HTML'}
        else:
            # SI NO HAY FOTO: Manda texto y MATA la previsualización fea
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                'chat_id': chat_id, 
                'text': caption, 
                'parse_mode': 'HTML', 
                'disable_web_page_preview': True
            }
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("🚀 Iniciando Bot con fijación de imágenes...")
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h):
        with open(archivo_h, "w") as f: f.write("")

    with open(archivo_h, "r") as f:
        historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            feed = feedparser.parse(resp.content)
            for entrada in reversed(feed.entries[:5]):
                link = entrada.get('link')
                if link and link not in historial:
                    desc = entrada.get('description', entrada.get('title', ''))
                    img = extraer_foto(entrada)
                    
                    # --- LÓGICA DE FILTRADO POR CUENTA ---
                    if nombre == "FINCOINS_GLOBAL":
                        # Extraer solo líneas con círculos
                        items = [l.strip() for l in desc.split('\n') if "🔴" in l or "🟢" in l]
                        if not items: continue
                        titulo_final = "📊 <b>Mercados Mundiales:</b>\n" + "\n".join(items)
                    
                    elif nombre == "AMBITO_DOLAR":
                        # Solo Apertura/Cierre y forzamos que sea breve
                        if "APERTURA" not in desc.upper() and "CIERRE" not in desc.upper(): continue
                        titulo_final = f"💵 <b>{desc.split('.')[0]}</b>"
                    
                    else:
                        titulo_final = f"📝 {desc[:150]}..."

                    enviar_telegram(titulo_final, link, img, nombre)
                    with open(archivo_h, "a") as f: f.write(link + "\n")
                    historial.add(link)
                    time.sleep(2)
        except Exception as e: print(f"Error en {nombre}: {e}")

if __name__ == "__main__":
    main()
