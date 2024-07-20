import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
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
processed_guids_file = 'processed_guids_bbc.json'

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

# Extract news items and print in tweet format
def extract_news_items(feed_url):
    feed = feedparser.parse(feed_url)
    processed_guids = load_processed_guids()
    new_processed_guids = processed_guids[:]
    today = datetime.utcnow().date()
    tweets = []

    for entry in feed.entries:
        pub_date = datetime(*entry.published_parsed[:6]).date()
        if pub_date == today and entry.id not in processed_guids:
            title = BeautifulSoup(entry.title, 'html.parser').get_text()
            description = BeautifulSoup(entry.description, 'html.parser').get_text()
            description = description[:140 - len(title)]  # Ensure the tweet length limit
            link = entry.link
            hashtags = determine_category(title, description)
            tweet = f"{title}\n{description}\n{link}\n{hashtags}"
            # print(tweet)
            # print("---")
            tweets.append(tweet)
            new_processed_guids.append(entry.id)

    save_processed_guids(new_processed_guids)
    return tweets

# BBC RSS feed URL
bbc_rss_url = 'https://feeds.bbci.co.uk/news/rss.xml'

# Extract and print news items
def get_headlines():
    return extract_news_items(bbc_rss_url)
