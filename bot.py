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
    """Captura la URL de la imagen (la placa visual) del post"""
    if 'media_content' in entrada and entrada.media_content:
        return entrada.media_content[0]['url']
    if 'enclosures' in entrada and entrada.enclosures:
        return entrada.enclosures[0]['url']
    summary = entrada.get('summary', '')
    match = re.search(r'src="([^"]+)"', summary)
    if match:
        return match.group(1)
    return None

def enviar_telegram(titulo, link, img_url, fuente):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    caption = f"🎯 <b>{fuente}</b>\n━━━━━━━━━━━━━━\n{titulo}\n\n🔗 <a href='{link}'>Ver en BlueSky</a>"

    try:
        if img_url:
            # Manda la placa visual (Cuadro de Ámbito) como foto principal
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {'chat_id': chat_id, 'photo': img_url, 'caption': caption, 'parse_mode': 'HTML'}
        else:
            # Si no hay foto, manda el texto limpio sin previsualización molesta
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                'chat_id': chat_id, 
                'text': caption, 
                'parse_mode': 'HTML', 
                'disable_web_page_preview': True
            }
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Error en Telegram: {e}")

def main():
    print("🚀 Iniciando Bot Informador de Mercados...")
    archivo_h = "last_id_inicio.txt"
    if not os.path.exists(archivo_h):
        with open(archivo_h, "w") as f: f.write("")

    with open(archivo_h, "r") as f:
        historial = set(f.read().splitlines())

    for nombre, url in FEEDS.items():
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                for entrada in reversed(feed.entries[:5]):
                    link = entrada.get('link')
                    if link and link not in historial:
                        titulo_original = entrada.get('description', entrada.get('title', ''))
                        titulo_up = titulo_original.upper()
                        img = extraer_foto(entrada)
                        
                        # --- FILTRO FINCOINS: Solo los índices marcados ---
                        if nombre == "FINCOINS_GLOBAL":
                            lineas = titulo_original.split('\n')
                            items = [l.strip() for l in lineas if "🔴" in l or "🟢" in l]
                            if items:
                                titulo_final = "📊 <b>Resumen Mundial:</b>\n" + "\n".join(items)
                            else: continue
                        
                        # --- FILTRO ÁMBITO: Solo Apertura/Cierre con placa ---
                        elif nombre == "AMBITO_DOLAR":
                            if "APERTURA DE JORNADA" in titulo_up or "CIERRE DE JORNADA" in titulo_up:
                                titulo_final = f"💵 <b>{titulo_original.split('.')[0]}</b>"
                            else: continue
                        else:
                            titulo_final = f"📝 {titulo_original[:150]}..."

                        enviar_telegram(titulo_final, link, img, nombre)
                        with open(archivo_h, "a") as f: f.write(link + "\n")
                        historial.add(link)
                        time.sleep(2)
        except Exception as e:
            print(f"Error en {nombre}: {e}")

if __name__ == "__main__":
    main()
