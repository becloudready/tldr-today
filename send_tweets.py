import tweepy
import environment as env
# import rss_feed_nyt as nyt
# import rss_feed_google as google
import nlp_bbc as bbc
import nlp_toi as toi
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
        sleep_time = random.randint(1200,2400)
        print(sleep_time)
        print("Random Sleep time between tweets")
        response = client.create_tweet(text=f"{tweet}")
        print(f"https://twitter.com/user/status/{response.data['id']}")
        time.sleep(sleep_time)

for feed in [bbc,toi]:
    send_tweets(feed)