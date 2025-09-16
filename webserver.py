from flask import Flask
import os
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run():
    port = int(os.environ.get('PORT', 8081))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,           # Включить режим отладки для авто-перезапуска
        use_reloader=True     # Явно включить перезапуск
    )

def keep_alive():  
    t = Thread(target=run)
    t.start()