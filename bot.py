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

# Lista de instancias de Nitter para probar en orden
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.cz",
    "https://nitter.net"
]

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
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    try:
        response = requests.post(url, data=data)
        return response.ok
    except:
        return False

def check_nitter():
    last_tweets = load_last_tweets()
    new_tweets_found = False

    for account in TWITTER_ACCOUNTS:
        print(f"--- Revisando @{account} ---")
        success_for_this_account = False
        
        # Probamos cada instancia hasta que una funcione
        for instance in NITTER_INSTANCES:
            feed_url = f"{instance}/{account}/rss"
            print(f"Probando instancia: {instance}...")
            
            try:
                feed = feedparser.parse(feed_url)
                
                # Si el feed tiene entradas, es que esta instancia funciona
                if feed.entries:
                    latest_tweet = feed.entries[0]
                    tweet_id = latest_tweet.link
                    tweet_text = latest_tweet.description
                    
                    if account not in last_tweets or last_tweets[account] != tweet_id:
                        message = f"🐦 <b>Nuevo tweet de @{account}</b>\n\n{tweet_text}\n\n🔗 <a href='{latest_tweet.link}'>Ver en X</a>"
                        
                        if send_telegram_message(message):
                            print(f"✅ ¡Éxito con {instance}!")
                            last_tweets[account] = tweet_id
                            new_tweets_found = True
                        
                    else:
                        print(f"☕ Sin tweets nuevos en {instance}")
                    
                    success_for_this_account = True
                    break # Salimos del bucle de instancias para esta cuenta
                else:
                    print(f"⚠️ {instance} no devolvió tweets, probando siguiente...")
            except Exception as e:
                print(f"❌ Error en {instance}: {e}")
            
            time.sleep(1) # Pausa técnica entre intentos

    if new_tweets_found:
        save_last_tweets(last_tweets)
    print("--- Proceso finalizado ---")

if __name__ == "__main__":
    check_nitter()
