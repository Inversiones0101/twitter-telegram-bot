import os
import json
import requests
import feedparser
import time

# --- CONFIGURACIÓN ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
RSS_FEED_URL = os.environ.get('RSS_FEED_URL')

LAST_TWEETS_FILE = 'last_tweets.json'

def send_telegram(link):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': link}, timeout=20)
        return res.ok
    except:
        return False

def run_bot():
    print("🕵️ Modo infiltrado activado...")
    
    if not RSS_FEED_URL:
        print("❌ Error: Falta RSS_FEED_URL.")
        return

    clean_url = RSS_FEED_URL.replace('/add ', '').strip()
    
    # Cabeceras de un navegador real para evitar bloqueos
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        # Descargamos el contenido como un humano
        session = requests.Session()
        response = session.get(clean_url, headers=headers, timeout=30)
        
        print(f"📡 Respuesta del Bridge: {response.status_code}")
        
        # Si recibimos HTML en lugar de XML (Tweets), hay un problema de link
        if "<!DOCTYPE html" in response.text[:100]:
            print("❌ EL BRIDGE ENVIÓ UNA PÁGINA DE ERROR. El link de los Secrets está mal.")
            return

        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("📭 Feed vacío. El Bridge no encontró tweets en esa lista.")
            return

        print(f"✅ ¡Conseguido! {len(feed.entries)} tweets encontrados.")
        
        history = []
        if os.path.exists(LAST_TWEETS_FILE):
            with open(LAST_TWEETS_FILE, 'r') as f: history = json.load(f)

        new_count = 0
        for entry in reversed(feed.entries):
            if entry.link not in history:
                if send_telegram(entry.link):
                    history.append(entry.link)
                    new_count += 1
                    print(f"🚀 Enviado: {entry.link}")
                    time.sleep(2)

        with open(LAST_TWEETS_FILE, 'w') as f: json.dump(history[-50:], f)
        print(f"🏁 Finalizado con {new_count} envíos.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_bot()
