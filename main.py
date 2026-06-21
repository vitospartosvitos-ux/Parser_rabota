import os
import json
import requests
from bs4 import BeautifulSoup
import time
from threading import Thread
from flask import Flask

# Инициализируем микро-веб-сервер для обхода ограничений бесплатного тарифа Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает в штатном режиме", 200

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CHANNELS_TO_PARSE = ["poisk_masterov", "rabota_sbor_mebel"]
KEYWORDS = ["сборка", "собрать", "мебель", "шкаф", "кухня", "кровать", "монтаж", "тумба"]
CHECK_INTERVAL = 600 
DB_FILE = "parsed_history.json"


def load_history():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_history(history):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(list(history), f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[!] Ошибка сохранения истории: {e}")


def send_telegram_notification(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[!] Ошибка отправки в Telegram: {e}")
        return False


def parse_channels():
    print(f"\n[*] Цикл сканирования: {time.strftime('%H:%M:%S')}")
    history = load_history()
    is_first_run = not os.path.exists(DB_FILE) or len(history) == 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for channel in CHANNELS_TO_PARSE:
        url = f"https://t.me/s/{channel}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message")
            
            for msg in messages:
                post_id = msg.get("data-post")
                if not post_id or post_id in history:
                    continue
                
                text_block = msg.find("div", class_="tgme_widget_message_text")
                if not text_block:
                    continue
                
                text = text_block.get_text(separator="\n").strip()
                if any(keyword in text.lower() for keyword in KEYWORDS):
                    link_anchor = msg.find("a", class_="tgme_widget_message_date")
                    post_url = link_anchor.get("href") if link_anchor else f"https://t.me/{post_id}"
                    
                    history.add(post_id)
                    
                    if not is_first_run:
                        alert_text = f"🔥 ЗАКАЗ! 🔥\nИсточник: @{channel}\nСсылка: {post_url}\n\n{text[:3000]}"
                        send_telegram_notification(alert_text)
            time.sleep(1.5)
        except Exception:
            pass
    save_history(history)


def run_parser_loop():
    """Фоновый поток для парсера, чтобы он работал параллельно с веб-сервером."""
    while True:
        try:
            parse_channels()
        except Exception as e:
            print(f"[CRITICAL] Ошибка: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[CRITICAL] Нет токенов!")
        exit(1)

    # Запускаем парсер в отдельном потоке
    parser_thread = Thread(target=run_parser_loop)
    parser_thread.daemon = True
    parser_thread.start()
    
    # Запускаем веб-сервер на порту, который выдаст Render
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)