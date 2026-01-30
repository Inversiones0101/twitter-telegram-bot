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
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': link}
    try:
        response = requests.post(url, data=payload, timeout=20)
        return response.ok
    except:
        return False

def run_bot():
    print("🛰️ Iniciando escaneo profundo de tweets...")
    
    if not RSS_FEED_URL:
        print("❌ Error: No hay URL en los Secrets.")
        return

    # Limpieza extrema del link
    clean_url = RSS_FEED_URL.replace('/add ', '').strip()
    
    # Usamos un "disfraz" de navegador para que el Bridge no nos bloquee
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # Primero descargamos el contenido crudo
        response = requests.get(clean_url, headers=headers, timeout=30)
        print(f"📡 Estado del Bridge: {response.status_code}")
        
        # Luego lo pasamos al lector de feeds
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("📭 El feed sigue pareciendo vacío. Intenta generar el link SOLO con ListID.")
            # Imprimimos parte del error para debug
            print(f"DEBUG: Contenido recibido: {response.text[:100]}...")
            return

        print(f"✅ ¡Éxito! Se detectaron {len(feed.entries)} entradas.")
        
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
        print(f"🏁 Proceso finalizado. {new_count} tweets nuevos.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    run_bot()
