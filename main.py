import feedparser
import time
from typing import List, Callable, Set
from functools import wraps
from bs4 import BeautifulSoup


class NewsItem:
    def __init__(self, title: str, link: str, description: str):
        self.title = title
        self.link = link
        self.description = description

        def extract_image_and_clean_text(description: str):
            soup = BeautifulSoup(description, 'html.parser')
            img_tag = soup.find('img', class_='webfeedsFeaturedVisual')
            img_url = img_tag['src'] if img_tag else None
            clean_text = soup.get_text()
            return img_url, clean_text

        self.image_url, self.description = extract_image_and_clean_text(description)


class RSSNewsSubject:
    def __init__(self, rss_url: str):
        self._handlers: List[Callable] = []
        self.rss_url = rss_url
        self._posted_news: Set[str] = set()
    
    def add_handler(self, handler: Callable):
        """Декоратор для додавання обробників новин"""
        @wraps(handler)
        def wrapper(*args, **kwargs):
            return handler(*args, **kwargs)
        
        self._handlers.append(wrapper)
        return wrapper
    
    def notify(self, news_item: dict):
        """Сповіщення всіх обробників про нову новину"""
        for handler in self._handlers:
            handler(news_item)
    
    def check_news(self):
        """Перевірка RSS на наявність нових новин"""
        try:
            feed = feedparser.parse(self.rss_url)
            
            for entry in feed.entries:
                news_id = entry.get('id', entry.link)
                
                if news_id not in self._posted_news:
                    print(entry.summary)
                    news_item = NewsItem(
                        title=entry.title,
                        link=entry.link,
                        description=entry.summary
                    )
                    self.notify(news_item)
                    self._posted_news.add(news_id)
                    
        except Exception as e:
            print(f"Error while parsing RSS: {e}")


class NewsAutoPostingSystem:
    def __init__(self, rss_url: str, check_interval: int = 300):
        self.rss_subject = RSSNewsSubject(rss_url)
        self.check_interval = check_interval
        
    def add_poster(self):
        """Декоратор для додавання нових обробників новин"""
        def decorator(handler: Callable):
            return self.rss_subject.add_handler(handler)
        return decorator
    
    def start(self):
        """Запуск системи"""
        print("Starting news auto-posting system...")
        while True:
            self.rss_subject.check_news()
            time.sleep(self.check_interval)


# Приклад використання
if __name__ == "__main__":
    # Створюємо систему
    system = NewsAutoPostingSystem(
        rss_url="https://lyceum.ztu.edu.ua/rss",
        check_interval=300
    )
    
    # Додаємо обробники новин за допомогою декоратора
    @system.add_poster()
    def post_to_facebook(news_item: NewsItem):
        print(f"Facebook posting: {news_item.title}")
        # Тут буде логіка публікації в Facebook через API
    
    @system.add_poster()
    def post_to_telegram(news_item: NewsItem):
        print(f"Telegram posting: {news_item.title}")
        # Тут буде логіка публікації в Telegram через API
    
    @system.add_poster()
    def post_to_twitter(news_item: NewsItem):
        print(f"Twitter posting: {news_item.title}")
        # Тут буде логіка публікації в Twitter через API
    
    # Додатковий приклад: логування всіх новин
    @system.add_poster()
    def log_news(news_item: NewsItem):
        print(news_item.image_url, news_item.description)
    
    # Запускаємо систему
    system.start()