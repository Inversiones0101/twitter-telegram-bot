import os
import tweepy
import json
import requests

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Configuración de Twitter
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
TWITTER_API_KEY_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

# Cuentas de Twitter a seguir
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

def get_user_tweets(api, username):
    """Obtiene los tweets más recientes de un usuario"""
    try:
        # Obtener los últimos 5 tweets del usuario (excluyendo retweets)
        tweets = api.user_timeline(
            screen_name=username,
            count=5,
            exclude_replies=True,
            include_rts=False,
            tweet_mode='extended'
        )
        
        if tweets:
            return tweets
        else:
            print(f"No hay tweets recientes de @{username}")
            return None
            
    except tweepy.errors.NotFound:
        print(f"❌ Usuario @{username} no encontrado")
        return None
    except tweepy.errors.Unauthorized:
        print(f"❌ No tienes permiso para acceder a @{username}")
        return None
    except Exception as e:
        print(f"Error obteniendo tweets de @{username}: {e}")
        return None

def check_new_tweets():
    """Revisa si hay tweets nuevos usando la API oficial de Twitter"""
    
    # Verificar que todas las credenciales estén configuradas
    if not all([TWITTER_API_KEY, TWITTER_API_KEY_SECRET, 
                TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        print("❌ Error: Faltan credenciales de Twitter")
        print(f"API_KEY: {'✅' if TWITTER_API_KEY else '❌'}")
        print(f"API_KEY_SECRET: {'✅' if TWITTER_API_KEY_SECRET else '❌'}")
        print(f"ACCESS_TOKEN: {'✅' if TWITTER_ACCESS_TOKEN else '❌'}")
        print(f"ACCESS_TOKEN_SECRET: {'✅' if TWITTER_ACCESS_TOKEN_SECRET else '❌'}")
        return
    
    # Autenticación con OAuth 1.0a
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY,
        TWITTER_API_KEY_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET
    )
    api = tweepy.API(auth)
    
    # Verificar credenciales
    try:
        user = api.verify_credentials()
        print(f"✅ Conectado a Twitter como: @{user.screen_name}")
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return
    
    last_tweets = load_last_tweets()
    new_tweets_found = False
    
    for account in TWITTER_ACCOUNTS:
        print(f"Revisando @{account}...")
        
        tweets = get_user_tweets(api, account)
        
        if not tweets:
            continue
        
        # Obtener el tweet más reciente
        latest_tweet = tweets[0]
        tweet_id = str(latest_tweet.id)
        tweet_text = latest_tweet.full_text
        tweet_url = f"https://twitter.com/{account}/status/{tweet_id}"
        
        # Revisar si ya enviamos este tweet
        if account not in last_tweets or last_tweets[account] != tweet_id:
            # ¡Nuevo tweet encontrado!
            
            # Acortar el texto si es muy largo
            if len(tweet_text) > 300:
                tweet_text = tweet_text[:300] + "..."
            
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
    print("🤖 Iniciando bot de Twitter → Telegram (usando OAuth 1.0a)")
    check_new_tweets()
