import tweepy
import environment as env
import sources.news_feeds.cnbc_feed as cnbc
import sources.news_feeds.nlp_bbc as bbc
import sources.news_feeds.nlp_toi as toi
import time,random



client = tweepy.Client(
    consumer_key=env.consumer_key, consumer_secret=env.consumer_secret,
    access_token=env.access_token, access_token_secret=env.access_token_secret
)


def send_tweets(news_feed):
    tweets = news_feed.get_headlines()
    # print(tweets)
    for tweet in tweets:
        print(tweet)
        print("---")
        sleep_time = random.randint(600,1200)
        print(sleep_time)
        print("Random Sleep time between tweets")
        response = client.create_tweet(text=f"{tweet}")
        print(f"https://twitter.com/user/status/{response.data['id']}")
        time.sleep(sleep_time)

for feed in [bbc,cnbc]:
    send_tweets(feed)