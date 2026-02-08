import os
import tweepy
import requests

# Cuentas de baja frecuencia para no agotar el cupo
CUENTAS = ["eldaminato", "NicolasCappella", "TargetDeMercado", "brujodegalileo"]

def enviar_telegram(texto, imagen_url=None):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if imagen_url:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        try:
            r = requests.get(imagen_url)
            requests.post(url, data={'chat_id': chat_id, 'caption': texto, 'parse_mode': 'Markdown'}, files={'photo': r.content})
        except:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={'chat_id': chat_id, 'text': texto, 'parse_mode': 'Markdown'})
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={'chat_id': chat_id, 'text': texto, 'parse_mode': 'Markdown'})

def revisar_feeds():
    # Autenticación usando tus nombres exactos de Secrets
    try:
        client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_KEY_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )

        for usuario in CUENTAS:
            print(f"Revisando a {usuario}...")
            user = client.get_user(username=usuario)
            if not user or not user.data: continue
            
            tweets = client.get_users_tweets(
                id=user.data.id, 
                max_results=5,
                expansions='attachments.media_keys',
                media_fields=['url']
            )

            if not tweets.data: continue

            tweet = tweets.data[0]
            id_tweet = str(tweet.id)
            log_file = f"last_id_{usuario}.txt"

            if os.path.exists(log_file) and open(log_file).read().strip() == id_tweet:
                continue

            img = tweets.includes['media'][0].url if tweets.includes and 'media' in tweets.includes else None
            enviar_telegram(f"📢 *Nuevo de @{usuario}*\n\n{tweet.text}", img)

            with open(log_file, "w") as f:
                f.write(id_tweet)
            print(f"✅ {usuario} enviado.")

    except Exception as e:
        print(f"Error de autenticación: {e}")

if __name__ == "__main__":
    revisar_feeds()
