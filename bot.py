import os
import tweepy
import json
import requests

# Configuración
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

# Cuentas de Twitter a seguir (puedes agregar más)
TWITTER_ACCOUNTS = [
    'Inversiones0101',
    'Barchart',
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

def get_user_tweets(client, username):
    """Obtiene los tweets más recientes de un usuario usando Tweepy"""
    try:
        # Buscar el usuario por su username
        user = client.get_user(username=username)
        
        if not user.data:
            print(f"Usuario @{username} no encontrado")
            return None
        
        user_id = user.data.id
        
        # Obtener los últimos tweets del usuario
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=5,
            tweet_fields=['created_at', 'text'],
            exclude=['retweets', 'replies']  # Excluir retweets y respuestas
        )
        
        if tweets.data:
            return tweets.data
        else:
            print(f"No hay tweets recientes de @{username}")
            return None
            
    except Exception as e:
        print(f"Error obteniendo tweets de @{username}: {e}")
        return None

def check_new_tweets():
    """Revisa si hay tweets nuevos usando la API oficial de Twitter"""
    
    if not TWITTER_BEARER_TOKEN:
        print("❌ Error: TWITTER_BEARER_TOKEN no configurado")
        return
    
    # Inicializar cliente de Tweepy
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
    
    last_tweets = load_last_tweets()
    new_tweets_found = False
    
    for account in TWITTER_ACCOUNTS:
        print(f"Revisando @{account}...")
        
        tweets = get_user_tweets(client, account)
        
        if not tweets:
            continue
        
        # Obtener el tweet más reciente
        latest_tweet = tweets[0]
        tweet_id = str(latest_tweet.id)
        tweet_text = latest_tweet.text
        tweet_url = f"https://twitter.com/{account}/status/{tweet_id}"
        
        # Revisar si ya enviamos este tweet
        if account not in last_tweets or last_tweets[account] != tweet_id:
            # ¡Nuevo tweet encontrado!
            
            # Acortar el texto si es muy largo
            if len(tweet_text) > 200:
                tweet_text = tweet_text[:200] + "..."
            
            message = f"""
🐦 <b>Nuevo tweet de @{account}</b>

{tweet_text}

🔗 {tweet_url}
"""
            
            result = send_telegram_message(message)
            if result:
                print(f"✅ Tweet enviado de @{account}")
                last_tweets[account] = tweet_id
                new_tweets_found = True
            else:
                print(f"❌ Error enviando tweet de @{account}")
        else:
            print(f"No hay tweets nuevos de @{account}")
    
    if new_tweets_found:
        save_last_tweets(last_tweets)
    
    print("✅ Revisión completada")

if __name__ == "__main__":
    print("🤖 Iniciando bot de Twitter → Telegram (usando API oficial)")
    check_new_tweets()
