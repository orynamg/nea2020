import os
import json
import traceback
import sqlite3
import twitter
import time
from datetime import datetime, date, timedelta
from classifier import Classifier
from database import NappDatabase
from models import *

MIN_KEYWORDS_COUNT = 5
COUNTRY_CODE = 'gb'
PAUSE_SEC = 60

woeid = {
    "gb": 23424975,
    "us": 23424977
}

count = 0

def get_popular_tweets(api, keyword):
    query = "q={}&result_type=popular&count=100&lang=en"
    results = api.GetSearch(raw_query=query.format(keyword))

    # global count
    # with open(f'twitter_trend_{count}.json', 'w') as f:
    #     l = [json.loads(i.AsJsonString()) for i in results]
    #     json.dump(l, f, indent=2)
    #     count += 1

    return results


def get_keywords(tweets, classifier):
    keywords = set()
    for tweet in tweets:
        keywords = keywords.union(classifier.get_named_entities(tweet.text))
    return keywords


def remove_newlines(text):
    return text.replace('\n', ' ').replace('\r', '')


def tweet_from_api(api_tweet):
    return Tweet(
        id = api_tweet.id,
        text = remove_newlines(api_tweet.text),
        hashtags = ','.join(h.text for h in api_tweet.hashtags),
        url = api_tweet.urls[0].url if api_tweet.urls else "",
        user = api_tweet.user.screen_name,
        published_at = datetime.fromtimestamp(api_tweet.created_at_in_seconds)
    )


def match_event(trend, keywords, events):
    """ Match existing or create new event based on twitter trend. """

    event = None

    # search for an exising event with similar keywords
    max_similarity = 0
    for existing_event in events:
        similarity = len(existing_event.keywords.intersection(keywords))
        if similarity > max_similarity:
            max_similarity = similarity
            if max_similarity >= MIN_KEYWORDS_COUNT:
                event = existing_event

    if event:
        print(f'Found exisitng event {event.name} by matching {max_similarity} keywords')

    if event:
        # update event name
        event.name = event.name + ' ' + trend.name 
        # and keywords if new keywords are found
        new_keywords = keywords.union(event.keywords)
        if len(new_keywords) > len(event.keywords):
            event.keywords = new_keywords
    else:
        # create event from this trend if no existing events matches
        event = Event(name=trend.name, keywords=keywords)
        print(f'Create event: {event.name}, keywords: {keywords}')

    return event


def process_trend(db, api, classifier, trend):
    try: 
        # load recent events from database (added in the last 3 days)
        start_date = date.today() - timedelta(days=3)
        events = list(db.find_events_since(start_date))
        print(f'Loaded {len(events)} existing recent events')

        # load popular tweets of the trend
        tweets = [tweet_from_api(t) for t in get_popular_tweets(api, trend.query)]
        print(f'Loaded {len(tweets)} tweets')
        if not tweets:
            return

        # form trend keywords
        keywords = get_keywords(tweets, classifier)
        print(f'Formed {len(keywords)} keywords')
        if len(keywords) < MIN_KEYWORDS_COUNT:
            return

        event = match_event(trend, keywords, events)
        assert event
        event = db.save_event(event)
        assert event.id
        print(f'Saved event id: {event.id} name: {event.name} , keywords: {event.keywords}')

        for tweet in tweets:
            tweet.event_id = event.id
            tweet.category_id = classifier.predict_category(tweet.text)
            db.save_tweet(tweet)
            #print(f'{trend.name} tweet saved: {tweet.text}')
        
        if not any(ev for ev in events if ev.id == event.id):
            events.append(event)

    except Exception as e:
        print(f'Error processing twitter trend {trend.name}: {e}')
        traceback.print_exc()


def main():
    conn = sqlite3.connect('database/napp.db', 
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    db = NappDatabase(conn)

    # load NLP classifier
    classifier = Classifier()

    # connect to twitter API
    api = twitter.Api(consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
                      consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
                      access_token_key=os.environ['TWITTER_ACCESS_TOKEN'],
                      access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET'])

    while True:
        # query regional trends from twitter
        trends = list(api.GetTrendsWoeid(woeid[COUNTRY_CODE]))

        # with open('twitter_trends.json', 'w') as f:
        #     l = [json.loads(i.AsJsonString()) for i in trends]
        #     json.dump(l, f, indent=2)

        for trend in trends:
            print(f'Processing twitter trend: {trend.name}')
            process_trend(db, api, classifier, trend)

        # wait some time then repeat
        print(f'Pausing...')
        time.sleep(PAUSE_SEC) 

    if conn:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(' Exiting...')
