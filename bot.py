import os
import json
import requests
import feedparser
import time

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Cuentas de Twitter a seguir
TWITTER_ACCOUNTS = ['Inversiones0101', 'Barchart']

# Instancia de Nitter (si una falla, puedes cambiarla por nitter.poast.org o nitter.cz)
NITTER_INSTANCE = "https://nitter.net"

LAST_TWEETS_FILE = 'last_tweets.json'

def load_last_tweets():
    try:
        with open(LAST_TWEETS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_last_tweets(last_tweets):
    with open(LAST_TWEETS_FILE, 'w') as f:
        json.dump(last_tweets, f)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=data)
    return response.ok

def check_nitter():
    last_tweets = load_last_tweets()
    new_tweets_found = False

    for account in TWITTER_ACCOUNTS:
        print(f"Revisando @{account} vía Nitter...")
        # Construimos la URL del feed RSS
        feed_url = f"{NITTER_INSTANCE}/{account}/rss"
        
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                print(f"No se encontraron tweets para {account}")
                continue

            # El primer elemento es el tweet más reciente
            latest_tweet = feed.entries[0]
            tweet_id = latest_tweet.link # Usamos el link como ID único
            tweet_text = latest_tweet.description
            
            # Limpiar el texto (Nitter a veces mete HTML)
            if account not in last_tweets or last_tweets[account] != tweet_id:
                message = f"🐦 <b>Nuevo tweet de @{account}</b>\n\n{tweet_text}\n\n🔗 <a href='{latest_tweet.link}'>Ver en X</a>"
                
                if send_telegram_message(message):
                    print(f"✅ Enviado: @{account}")
                    last_tweets[account] = tweet_id
                    new_tweets_found = True
                
                # Pausa breve para no saturar a Telegram
                time.sleep(1)
        except Exception as e:
            print(f"Error con @{account}: {e}")

    if new_tweets_found:
        save_last_tweets(last_tweets)

if __name__ == "__main__":
    check_nitter()
