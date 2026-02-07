import os
import tweepy
import requests

# Lista de cuentas sugeridas por su baja frecuencia
CUENTAS = ["eldaminato", "NicolasCappella", "TargetDeMercado", "brujodegalileo"]

def enviar_telegram(texto, imagen_url=None):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if imagen_url:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {'chat_id': chat_id, 'caption': texto, 'parse_mode': 'Markdown'}
        try:
            r = requests.get(imagen_url)
            files = {'photo': r.content}
            requests.post(url, data=payload, files=files)
        except:
            pass
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': texto, 'parse_mode': 'Markdown'}
        requests.post(url, json=payload)

def revisar_feeds():
    # Usamos el Bearer Token de OAuth 2.0
    bearer_token = os.getenv('X_BEARER_TOKEN')
    client = tweepy.Client(bearer_token=bearer_token)

    for usuario in CUENTAS:
        try:
            print(f"Revisando a {usuario}...")
            # 1. Buscamos el ID del usuario
            user = client.get_user(username=usuario)
            if not user.data:
                continue
            user_id = user.data.id

            # 2. Obtenemos el último tweet con imágenes
            tweets = client.get_users_tweets(
                id=user_id, 
                max_results=5,
                expansions='attachments.media_keys',
                media_fields=['url', 'preview_image_url']
            )

            if not tweets.data:
                continue

            ultimo_tweet = tweets.data[0]
            id_actual = str(ultimo_tweet.id)

            # 3. Memoria por cuenta para no repetir
            log_file = f"last_id_{usuario}.txt"
            if os.path.exists(log_file) and open(log_file).read().strip() == id_actual:
                print(f"Sin novedades para {usuario}")
                continue

            # 4. Preparar contenido
            texto = f"📢 *Nuevo de @{usuario}*\n\n{ultimo_tweet.text}"
            imagen_url = None
            
            if tweets.includes and 'media' in tweets.includes:
                media = tweets.includes['media'][0]
                imagen_url = media.url if media.url else media.preview_image_url

            enviar_telegram(texto, imagen_url)

            # 5. Guardar en memoria
            with open(log_file, "w") as f:
                f.write(id_actual)
            print(f"¡Tweet de {usuario} enviado!")

        except Exception as e:
            print(f"Error con {usuario}: {e}")

if __name__ == "__main__":
    revisar_feeds()
