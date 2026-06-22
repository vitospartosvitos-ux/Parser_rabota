import cloudscraper
import random
import time
from bs4 import BeautifulSoup
from database import save_post, post_exists

def parse_avito(query_url):
    print(f"[*] Запуск парсинга Авито через CloudScraper...")
    
    # Создаем "умный" экземпляр сессии
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        time.sleep(random.uniform(5, 10))
        response = scraper.get(query_url, timeout=20)
        
        print(f"[*] Ответ Авито: код {response.status_code}")
        
        if response.status_code != 200:
            print(f"[!] Авито блокирует доступ: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select('div[data-marker="item"]')
        
        print(f"[*] Найдено карточек: {len(items)}")
        
        for item in items:
            title_tag = item.select_one('h3[itemprop="name"]')
            link_tag = item.select_one('a[itemprop="url"]')
            
            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = "https://www.avito.ru" + link_tag["href"]
                post_id = link.split("_")[-1]
                
                if not post_exists(post_id):
                    save_post(post_id, "ORDER", "avito", title, link)
                    print(f"[+] УСПЕХ! Лид найден: {title}")
                    
    except Exception as e:
        print(f"[!] Критическая ошибка CloudScraper: {e}")