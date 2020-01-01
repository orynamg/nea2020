import os
import sqlite3
import twitter
from datetime import datetime
from database import create_database, insert_tweet


def get_tweets(api, keyword):
    query = "q={}&result_type=popular&count=100&lang=en"
    results = api.GetSearch(raw_query=query.format(keyword))
    return results


def save_tweet(conn, tweet):
    hashtags = ','.join(h.text for h in tweet.hashtags)
    url = tweet.urls[0].url if tweet.urls else None 
    published_at = datetime.fromtimestamp(tweet.created_at_in_seconds)
    return insert_tweet(conn, tweet.text, hashtags, url, tweet.user.screen_name, published_at)


def main():
    conn = sqlite3.connect('database/napp.db')

    consumer_key = os.environ['TWITTER_CONSUMER_KEY']
    consumer_secret = os.environ['TWITTER_CONSUMER_SECRET']
    access_token = os.environ['TWITTER_ACCESS_TOKEN']
    access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']

    api = twitter.Api(consumer_key=consumer_key,
                      consumer_secret=consumer_secret,
                      access_token_key=access_token,
                      access_token_secret=access_token_secret)

    woeids = {
        "GB": 23424975,
        "US": 23424977
    }

    with conn:
        create_database(conn)

        trends = api.GetTrendsWoeid(woeids["GB"])

        for trend in trends:
            # print(trend)
            # continue
            tweets = get_tweets(api, trend.query)
            for tweet in tweets:
                tweet_db_id = save_tweet(conn, tweet)
                print(trend.name, tweet_db_id, tweet.text[:80])
            break


if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
