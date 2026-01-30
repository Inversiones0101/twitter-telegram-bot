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

def run_bot():
    print("🚀 Iniciando el bot con el nuevo puente...")
    
    # Cargamos historial para no repetir
    history = []
    if os.path.exists(LAST_TWEETS_FILE):
        with open(LAST_TWEETS_FILE, 'r') as f:
            history = json.load(f)

    # Leemos el feed
    feed = feedparser.parse(RSS_FEED_URL)
    
    if not feed.entries:
        print("📭 El feed sigue vacío. Probando método alternativo...")
        return

    new_count = 0
    for entry in reversed(feed.entries):
        if entry.link not in history:
            # Enviar a Telegram
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': entry.link}
            
            res = requests.post(url, data=payload)
            if res.ok:
                history.append(entry.link)
                new_count += 1
                print(f"✅ Enviado: {entry.link}")
                time.sleep(2) # Pausa para evitar spam

    # Guardar progreso
    with open(LAST_TWEETS_FILE, 'w') as f:
        json.dump(history[-50:], f)
    print(f"🏁 Finalizado. Se enviaron {new_count} tweets.")

if __name__ == "__main__":
    run_bot()
