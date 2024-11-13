import feedparser
import time
import json
from typing import List, Callable, Set
from functools import wraps
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import requests

load_dotenv()
INSTAGRAM_TOKEN = os.getenv("INSTAGRAM_TOKEN")
FB_POST_URL = os.getenv("FB_POST_URL")
IG_UPLOAD_URL = os.getenv("IG_UPLOAD_URL")
IG_POST_URL = os.getenv("IG_POST_URL")

PERSIST_FILE = "last_news.json"

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
        self._posted_news: Set[str] = self._load_posted_news()
    
    def _load_posted_news(self) -> Set[str]:
        """Load posted news from file"""
        try:
            if os.path.exists(PERSIST_FILE):
                with open(PERSIST_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('posted_news', []))
        except Exception as e:
            print(f"Error loading posted news: {e}")
        return set()
    
    def _save_posted_news(self):
        """Save posted news to file"""
        try:
            with open(PERSIST_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'posted_news': list(self._posted_news),
                    'last_update': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving posted news: {e}")
   
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
            entry = feed.entries[0]
            news_id = entry.get('id', entry.link)
           
            if news_id not in self._posted_news:
                news_item = NewsItem(
                    title=entry.title,
                    link=entry.link,
                    description=entry.summary
                )
                self.notify(news_item)
                self._posted_news.add(news_id)
                self._save_posted_news()  # Save after each new post
                   
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
            try:
                self.rss_subject.check_news()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(self.check_interval)

system = NewsAutoPostingSystem(
    rss_url="https://lyceum.ztu.edu.ua/rss",
    check_interval=30
)

@system.add_poster()
def post_to_facebook(news_item: NewsItem):
    print(f"Facebook posting: {news_item.title}")
    payload = {
        "url": news_item.image_url,
        "access_token": INSTAGRAM_TOKEN
    }
    payload["message"] = f"{news_item.title}\n\n{news_item.link}"
    payload2 = {
        "fields": "permalink_url",
        "access_token": INSTAGRAM_TOKEN
    }
    r = requests.post(FB_POST_URL, params=payload)
    print(r.text)
    r = requests.get(f"https://graph.facebook.com/v19.0/{r.json()['post_id']}", params=payload2)
    print(r.text)

if __name__ == "__main__":
    system.start()