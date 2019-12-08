import os
import twitter
from napp.database import create_database


def get_tweets(api, keyword):
    query = "q={}&result_type=popular&count=100&lang=en"
    results = api.GetSearch(raw_query=query.format(keyword))
    return results


def main():
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

    trends = api.GetTrendsWoeid(woeids["GB"])

    for trend in trends:
        tweets = get_tweets(api, trend.query)
        for tweet in tweets:
            print(trend.name, tweet.text[:80])


if __name__ == "__main__":
    main()
