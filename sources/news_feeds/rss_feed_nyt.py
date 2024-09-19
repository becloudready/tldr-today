import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import re
import json

# Define expanded keywords for different categories
news_categories = {
    'Technology': [
        'tech', 'technology', 'IT', 'software', 'hardware', 'AI', 'cyber', 'internet', 'digital', 'innovation',
        'gadget', 'robotics', 'cloud', 'computing', 'virtual', 'VR', 'AR', 'blockchain', 'crypto', 'coding', 'programming'
    ],
    'Health': [
        'health', 'doctor', 'NHS', 'medical', 'virus', 'pandemic', 'hospital', 'surgery', 'vaccine', 'disease',
        'wellness', 'fitness', 'nutrition', 'mental health', 'pharmacy', 'clinic', 'treatment', 'therapy', 'epidemic', 'infection'
    ],
    'Sports': [
        'sports', 'football', 'cricket', 'Olympics', 'tournament', 'match', 'game', 'athlete', 'team', 'score',
        'basketball', 'baseball', 'tennis', 'golf', 'soccer', 'race', 'medal', 'championship', 'league', 'coach'
    ],
    'Politics': [
        'politics', 'government', 'election', 'policy', 'minister', 'president', 'congress', 'parliament', 'senate', 'vote',
        'campaign', 'democracy', 'republic', 'legislation', 'bill', 'law', 'diplomacy', 'foreign', 'parliament', 'governance'
    ],
    'Business': [
        'business', 'market', 'economy', 'stock', 'finance', 'investment', 'bank', 'trade', 'industry', 'corporate',
        'entrepreneur', 'startup', 'venture', 'profit', 'loss', 'revenue', 'sales', 'merger', 'acquisition', 'commerce'
    ],
    'Entertainment': [
        'entertainment', 'movie', 'film', 'music', 'celebrity', 'actor', 'actress', 'concert', 'show', 'TV',
        'series', 'album', 'song', 'festival', 'award', 'theater', 'performance', 'dance', 'art', 'media'
    ],
    'World': [
        'world', 'international', 'global', 'country', 'nation', 'war', 'peace', 'diplomacy', 'UN', 'foreign',
        'conflict', 'treaty', 'border', 'crisis', 'aid', 'refugee', 'disaster', 'cooperation', 'summit', 'alliance'
    ],
    'Science': [
        'science', 'research', 'study', 'experiment', 'discovery', 'space', 'biology', 'chemistry', 'physics', 'innovation',
        'laboratory', 'scientist', 'theory', 'data', 'analysis', 'genetics', 'astronomy', 'geology', 'ecology', 'environment'
    ]
}

# File to store processed GUIDs
processed_guids_file = 'processed_guids_nyt.json'

# Load processed GUIDs from file
def load_processed_guids():
    try:
        with open(processed_guids_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Save processed GUIDs to file
def save_processed_guids(processed_guids):
    with open(processed_guids_file, 'w') as file:
        json.dump(processed_guids, file)

# Determine category hashtags based on keywords in title and description
def determine_category(title, description):
    hashtags = []
    for category, keywords in news_categories.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', title, re.IGNORECASE) or re.search(r'\b' + re.escape(keyword) + r'\b', description, re.IGNORECASE):
                hashtags.append(f'#{category}')
                break
    return ' '.join(hashtags)

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
        guid = item.find('guid').text if item.find('guid') is not None else item.find('link').text

        news_items.append({
            'guid': guid,
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
    processed_guids = load_processed_guids()
    new_processed_guids = processed_guids[:]

    for news in recent_news:
        if news['guid'] not in processed_guids:
            formatted_date = format_date(news['pub_date'])
            headline = truncate_text(news['headline'], 100)
            description = truncate_text(news['description'], 140)
            hashtags = determine_category(news['headline'], news['description'])
            tweet = f"{headline}\nDescription: {description}\nDate: {formatted_date}\n{hashtags}\nPublisher: NYT"
            if len(tweet) > 280:
                tweet = truncate_text(tweet, 280)
            tweets.append(tweet)
            new_processed_guids.append(news['guid'])
    
    save_processed_guids(new_processed_guids)
    return tweets

# Example of getting headlines and printing them
for tweet in get_headlines():
    print(tweet)
    print('-' * 40)
