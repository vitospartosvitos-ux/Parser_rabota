import requests
import random
import time
from bs4 import BeautifulSoup
from database import save_post, post_exists

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}

def parse_avito(query_url):
    print(f"[*] Запуск диагностики Авито...")
    try:
        time.sleep(random.uniform(5, 10))
        response = requests.get(query_url, headers=HEADERS, timeout=20)
        
        # Логируем результат для отладки
        print(f"[*] Ответ Авито: код {response.status_code}, длина контента {len(response.text)}")
        
        if response.status_code != 200:
            print(f"[!] Авито блокирует или ошибка: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Пробуем разные селекторы, если Авито сменил верстку
        items = soup.select('div[data-marker="item"]')
        print(f"[*] Найдено элементов через data-marker: {len(items)}")
        
        if len(items) == 0:
            # Если не нашли, выведем в логи кусок кода, чтобы я увидел, что там сейчас
            print("[!] Элементы не найдены! Скинь мне эту ошибку, я обновлю селектор.")
            return

        for item in items:
            title_tag = item.select_one('h3[itemprop="name"]')
            link_tag = item.select_one('a[itemprop="url"]')
            
            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = "https://www.avito.ru" + link_tag["href"]
                post_id = link.split("_")[-1]
                
                if not post_exists(post_id):
                    save_post(post_id, "ORDER", "avito", title, link)
                    print(f"[+] УСПЕХ! Найден лид: {title}")
                    
    except Exception as e:
        print(f"[!] Ошибка парсинга Авито: {e}")