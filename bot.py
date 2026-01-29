import os
import json
import requests
import feedparser
import time
import random

# --- CONFIGURACIÓN DE IDENTIDAD ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
]

# --- CARGA DE CONFIGURACIÓN DESDE SECRETS ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
RSS_FEED_URL = os.environ.get('RSS_FEED_URL')

LAST_TWEETS_FILE = 'last_tweets.json'

def load_history():
    if os.path.exists(LAST_TWEETS_FILE):
        try:
            with open(LAST_TWEETS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(LAST_TWEETS_FILE, 'w') as f:
        json.dump(history[-50:], f)

def send_telegram(link):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': link
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.ok
    except:
        return False

def run_bot():
    print("🛰️ Iniciando escaneo de nuevos tweets...")
    
    if not RSS_FEED_URL:
        print("❌ ERROR: No se encontró la URL del Bridge en los Secrets.")
        return

    history = load_history()
    ua = random.choice(USER_AGENTS)
    
    # Leemos el Feed del Bridge
    feed = feedparser.parse(RSS_FEED_URL, agent=ua)
    
    if not feed.entries:
        print("📭 El feed está vacío o el link es incorrecto.")
        return

    new_count = 0
    # Procesamos del más antiguo al más nuevo para mantener el orden
    for entry in reversed(feed.entries):
        tweet_link = entry.link
        
        if tweet_link not in history:
            print(f"🆕 Enviando: {tweet_link}")
            if send_telegram(tweet_link):
                history.append(tweet_link)
                new_count += 1
                time.sleep(1) 
        
    if new_count > 0:
        save_history(history)
        print(f"✅ ¡Éxito! {new_count} tweets nuevos enviados.")
    else:
        print("☕ Todo al día. Nada nuevo por ahora.")

if __name__ == "__main__":
    run_bot()
