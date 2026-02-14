import os
import requests

def test_telegram():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    mensaje = "🤖 ¡Hola! Si lees esto, la conexión con Telegram funciona perfectamente."
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': mensaje}
    
    print(f"Intentando enviar a ID: {chat_id}")
    r = requests.post(url, json=payload)
    print(f"Resultado: {r.status_code} - {r.text}")

if __name__ == "__main__":
    test_telegram()
