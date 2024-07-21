import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from pathlib import Path
import os
import requests
import environment as env

home_dir = str(Path.home())

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# File to store processed GUIDs
processed_guids_file = os.path.join(home_dir, 'processed_guids_toi.json')

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

# Shorten URL using TinyURL
# def shorten_url(long_url):
#     api_url = "https://api.tinyurl.com/create"
#     token = f"Bearer {env.tinyurl_token}"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": token # Replace with your TinyURL API key
#     }
#     data = {
#         "url": long_url,
#         "domain": "tinyurl.com"
#     }
#     response = requests.post(api_url, headers=headers, json=data)
#     if response.status_code == 200:
#         return response.json()['data']['tiny_url']
#     else:
#         return long_url
    
def shorten_url(long_url):
    api_url = "https://api.short.io/links"
    headers = {
        "Content-Type": "application/json",
        "Authorization": env.shorturl_token
    }
    data = {
        "originalURL": long_url,
        "domain": "https://g1xz.short.gy"
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()['shortURL']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return long_url

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
            link = entry.link
            short_link = link
            short_link = shorten_url(link)
            hashtags = generate_hashtags(title + " " + description)
            print(hashtags)
            tweet = f"{title}\n{short_link}\n{hashtags}"
            tweet = truncate_tweet(tweet)
            tweets.append(tweet)
            new_processed_guids.append(entry.id)

    save_processed_guids(new_processed_guids)
    return tweets

# Times of India RSS feed URL
toi_rss_url = 'https://timesofindia.indiatimes.com/rssfeedmostshared.cms'

# Extract and print news items
def get_headlines():
    return extract_news_items(toi_rss_url)

print(get_headlines())
