import os
import time
import requests

from bs4 import BeautifulSoup
from threading import Thread

from flask import Flask

from database import (
    init_db,
    save_post,
    post_exists,
    get_posts,
    get_stats
)

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CHECK_INTERVAL = 600

CHANNELS_TO_PARSE = [
    "poisk_masterov",
    "rabota_sbor_mebel"
]

ORDER_WORDS = [
    "сборка",
    "собрать",
    "шкаф",
    "кухня",
    "комод",
    "кровать",
    "стол",
    "тумба",
    "монтаж мебели",
    "сборка мебели"
]

VACANCY_WORDS = [
    "требуется сборщик",
    "ищем сборщика",
    "вакансия",
    "работа сборщик мебели",
    "монтажник мебели"
]


@app.route("/")
def home():

    stats = get_stats()

    return f"""
    <h1>Furniture CRM</h1>

    <p>Всего записей: {stats['total']}</p>
    <p>Заказов: {stats['orders']}</p>
    <p>Вакансий: {stats['vacancies']}</p>

    <hr>

    <a href='/orders'>Заказы</a><br>
    <a href='/vacancies'>Вакансии</a>
    """


@app.route("/orders")
def orders():

    posts = get_posts("ORDER")

    html = "<h1>Заказы</h1>"

    for post in posts:

        html += f"""
        <div style='margin-bottom:20px'>
        <a href='{post['url']}' target='_blank'>Открыть</a><br>
        <b>{post['channel']}</b><br>
        {post['text'][:500]}
        </div>
        <hr>
        """

    return html


@app.route("/vacancies")
def vacancies():

    posts = get_posts("VACANCY")

    html = "<h1>Вакансии</h1>"

    for post in posts:

        html += f"""
        <div style='margin-bottom:20px'>
        <a href='{post['url']}' target='_blank'>Открыть</a><br>
        <b>{post['channel']}</b><br>
        {post['text'][:500]}
        </div>
        <hr>
        """

    return html


def send_telegram_notification(text):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:

        requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=15
        )

    except Exception as e:
        print(e)


def detect_type(text):

    lower = text.lower()

    if any(x in lower for x in VACANCY_WORDS):
        return "VACANCY"

    if any(x in lower for x in ORDER_WORDS):
        return "ORDER"

    return None


def parse_channels():

    print("SCAN START")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for channel in CHANNELS_TO_PARSE:

        try:

            url = f"https://t.me/s/{channel}"

            response = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            messages = soup.find_all(
                "div",
                class_="tgme_widget_message"
            )

            for msg in messages:

                post_id = msg.get("data-post")

                if not post_id:
                    continue

                if post_exists(post_id):
                    continue

                text_block = msg.find(
                    "div",
                    class_="tgme_widget_message_text"
                )

                if not text_block:
                    continue

                text = text_block.get_text(
                    separator="\n"
                ).strip()

                post_type = detect_type(text)

                if not post_type:
                    continue

                link = msg.find(
                    "a",
                    class_="tgme_widget_message_date"
                )

                post_url = (
                    link.get("href")
                    if link
                    else f"https://t.me/{post_id}"
                )

                save_post(
                    post_id,
                    post_type,
                    channel,
                    text,
                    post_url
                )

                icon = "🔥"

                if post_type == "VACANCY":
                    icon = "💼"

                send_telegram_notification(
                    f"{icon} {post_type}\n\n{text[:3000]}"
                )

                print("saved", post_id)

                time.sleep(1)

        except Exception as e:

            print(
                f"error {channel}: {e}"
            )


def parser_loop():

    time.sleep(5)

    while True:

        try:
            parse_channels()
        except Exception as e:
            print(e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":

    init_db()

    parser_thread = Thread(
        target=parser_loop
    )

    parser_thread.daemon = True
    parser_thread.start()

    port = int(
        os.getenv("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )