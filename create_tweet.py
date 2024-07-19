import tweepy
import environment as env
import news_feeds_nyt as nyt
import time,random



client = tweepy.Client(
    consumer_key=env.consumer_key, consumer_secret=env.consumer_secret,
    access_token=env.access_token, access_token_secret=env.access_token_secret
)


def send_tweets(news_feed):
    tweets = news_feed.get_headlines()
    # print(tweets)
    for tweet in tweets:
        # print(tweet)
        response = client.create_tweet(text=tweet)
        print(f"https://twitter.com/user/status/{response.data['id']}")
        time.sleep(random.randint(5, 10))



for feed in [nyt]:
    send_tweets(feed)