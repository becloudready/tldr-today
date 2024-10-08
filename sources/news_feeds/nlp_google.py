import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import pos_tag

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# File to store processed GUIDs
processed_guids_file = 'processed_guids_google.json'

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

# Extract keywords using NLTK and filter only nouns
def extract_keywords(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_words = [w for w in word_tokens if w.lower() not in stop_words and w.isalpha()]
    nouns = [word for (word, pos) in pos_tag(filtered_words) if pos.startswith('NN')]
    return nouns

# Generate hashtags based on extracted keywords
def generate_hashtags(text):
    keywords = extract_keywords(text)
    hashtags = [f"#{keyword.capitalize()}" for keyword in keywords[:2]]  # Limit to top 2 keywords
    return ' '.join(hashtags)

# Truncate tweet to fit within Twitter's character limit
def truncate_tweet(tweet):
    max_length = 280
    if len(tweet) > max_length:
        return tweet[:max_length-3] + '...'
    return tweet

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
            source = entry.source['title'] if 'source' in entry else 'Unknown'
            hashtags = generate_hashtags(title + " " + description)
            print(hashtags)
            tweet = f"{title}\n{description}\n{link}\n{hashtags}\nSource: {source}"
            tweet = truncate_tweet(tweet)
            tweets.append(tweet)
            new_processed_guids.append(entry.id)

    save_processed_guids(new_processed_guids)
    return tweets

# Google RSS feed URL
google_rss_url = 'https://news.google.com/rss/search?q=cars&hl=en-CA&gl=CA&ceid=CA:en'

# Extract and print news items
def get_headlines():
    return extract_news_items(google_rss_url)

# Example of getting headlines and printing them
for tweet in get_headlines():
    print(tweet)
    print('-' * 40)
