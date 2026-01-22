import os
import requests
import feedparser
import json
from datetime import datetime

# Configuración
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Cuentas de Twitter a seguir (puedes agregar más)
TWITTER_ACCOUNTS = [
    'Inversiones0101',
    'Barchart',
    '',
    # Agrega más cuentas aquí
]

# Archivo para recordar qué tweets ya enviamos
LAST_TWEETS_FILE = 'last_tweets.json'

def load_last_tweets():
    """Carga los últimos tweets enviados"""
    try:
        with open(LAST_TWEETS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_last_tweets(last_tweets):
    """Guarda los últimos tweets enviados"""
    with open(LAST_TWEETS_FILE, 'w') as f:
        json.dump(last_tweets, f)

def send_telegram_message(message):
    """Envía un mensaje a Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return None

def get_twitter_feed(username):
    """Obtiene el feed RSS de una cuenta de Twitter"""
    # Usando Nitter como fuente RSS
    nitter_instances = [
        f'https://nitter.net/{username}/rss',
        f'https://nitter.privacydev.net/{username}/rss',
    ]
    
    for rss_url in nitter_instances:
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                return feed
        except:
            continue
    return None

def check_new_tweets():
    """Revisa si hay tweets nuevos"""
    last_tweets = load_last_tweets()
    new_tweets_found = False
    
    for account in TWITTER_ACCOUNTS:
        print(f"Revisando @{account}...")
        feed = get_twitter_feed(account)
        
        if not feed or not feed.entries:
            print(f"No se pudo obtener feed de @{account}")
            continue
        
        # Obtener el tweet más reciente
        latest_tweet = feed.entries[0]
        tweet_link = latest_tweet.link
        
        # Revisar si ya enviamos este tweet
        if account not in last_tweets or last_tweets[account] != tweet_link:
            # ¡Nuevo tweet encontrado!
            message = f"""
🐦 <b>Nuevo tweet de @{account}</b>

{latest_tweet.title}

🔗 {tweet_link}
"""
            
            result = send_telegram_message(message)
            if result:
                print(f"✅ Tweet enviado de @{account}")
                last_tweets[account] = tweet_link
                new_tweets_found = True
            else:
                print(f"❌ Error enviando tweet de @{account}")
        else:
            print(f"No hay tweets nuevos de @{account}")
    
    if new_tweets_found:
        save_last_tweets(last_tweets)
    
    print("✅ Revisión completada")

if __name__ == "__main__":
    print("🤖 Iniciando bot de Twitter → Telegram")
    check_new_tweets()
