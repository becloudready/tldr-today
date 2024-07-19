import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def fetch_news_feed(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the feed: {response.status_code}")
        return []
    
    root = ET.fromstring(response.content)
    items = root.findall('.//item')
    
    news_items = []
    for item in items:
        headline = item.find('title').text
        description = item.find('description').text
        pub_date_str = item.find('pubDate').text
        pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
        news_items.append({
            'headline': headline,
            'description': description,
            'pub_date': pub_date
        })
    
    return news_items

def filter_recent_news(news_items, days=1):
    today = datetime.now().astimezone()
    start_date = today - timedelta(days=days)
    recent_news = [news for news in news_items if start_date <= news['pub_date'] <= today]
    return recent_news

def format_date(date):
    return date.strftime('%B %d %Y')

def truncate_text(text, max_length):
    if len(text) > max_length:
        return text[:max_length-3] + '...'
    return text

url = 'https://rss.nytimes.com/services/xml/rss/nyt/Americas.xml'
news_feed = fetch_news_feed(url)
recent_news = filter_recent_news(news_feed, days=1)

def get_headlines():
    tweets = []
    for news in recent_news:
        formatted_date = format_date(news['pub_date'])
        headline = truncate_text(news['headline'], 100)
        description = truncate_text(news['description'], 140)
        tweet = f"{headline}\nDescription: {description}\nDate: {formatted_date}\nPublisher: NYT"
        if len(tweet) > 280:
            tweet = truncate_text(tweet, 280)
        tweets.append(tweet)    
        # print(tweet)
        # print('-' * 40)
    return tweets
