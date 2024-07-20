import tweepy
import environment as env
import rss_feed_nyt as nyt
import rss_feed_google as google
import rss_feed_bbc as bbc
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
        response = client.create_tweet(text=f"#News {tweet}")
        print(f"https://twitter.com/user/status/{response.data['id']}")
        time.sleep(random.randint(60,100))

for feed in [bbc,nyt,google]:
    send_tweets(feed)