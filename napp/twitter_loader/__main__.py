import requests
import json
from twitter_auth import BearerTokenAuth
import twitter
from napp.database import create_database

woeids = {
    "gb": 23424975, 
    "us": 23424977
}

trends_url = "https://api.twitter.com/1.1/trends/place.json"

def get_trends(auth, country_code):
    woeid = woeids[country_code]
    response = requests.get(trends_url, auth=auth, params={"id": woeid})
    response = response.json()

    for trend in response[0]["trends"]:
         yield trend["query"]


def get_tweets(api, keyword):
    query = "q={}%20&result_type=recent&since=2019-11-22&count=100&lang=en"
    results = api.GetSearch(raw_query=query.format(keyword))
    return results


def main():
    auth = BearerTokenAuth(
                consumer_key="SFkahJJkOcC5rAwcrqQq6cynl", 
                consumer_secret="WkVQVWVE09tfIIk6eFon5lfxyGF5llguooZz8JPq9ZQiWgELWj")

    api = twitter.Api(consumer_key="SFkahJJkOcC5rAwcrqQq6cynl",
                  consumer_secret="WkVQVWVE09tfIIk6eFon5lfxyGF5llguooZz8JPq9ZQiWgELWj",
                  access_token_key="2752888857-DgQSdhXKDCH4NWynUMmIW9DAcohjflgmvKEQnI4",
                  access_token_secret="sqJ798LQWtgC51HaTxLdcD1RxqgWrxRebN5ikeMqDjQRE")

    for trend in get_trends(auth, "gb"):
        tweets = get_tweets(api, trend)
        for tweet in tweets:
            print(trend, tweet.text[:80])

if __name__ == "__main__":
    main()

