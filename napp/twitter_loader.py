import config
import os
import traceback
import sqlite3
import twitter
from datetime import datetime, date, timedelta
from classifier import Classifier, normalize_text
import database as db
from models import *

woeid = {
    "gb": 23424975,
    "us": 23424977
}


def get_popular_tweets(api, keyword):
    query = "q={}&result_type=popular&count=100&lang=en"
    results = api.GetSearch(raw_query=query.format(keyword))
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


def match_event(conn, trend, keywords, events):
    """ Match existing or create new event based on twitter trend. """

    # search for an exising event that matches exactly by name
    event = next((ev for ev in events if ev.name == trend.name), None)
    if event:
        print(f'Found exisitng event by exact trend name: {event}')
    else:
        # search for an exising event with similar keywords
        max_similarity = 0
        for existing_event in events:
            similarity = len(existing_event.keywords.intersection(keywords))
            if similarity > max_similarity:
                max_similarity = similarity
                if max_similarity > 2: # must have at least three keywords
                    event = existing_event
        if event:
            print(f'Found exisitng event by matching keywords: {max_similarity}')

    with conn:
        if event:
            # update event if new keywords are found
            new_keywords = keywords.union(event.keywords)
            if len(new_keywords) > len(event.keywords):
                event.keywords = new_keywords
                db.save_event(conn, event)
                print(f'Updated event {event.name} with id {event.id}, keywords: {new_keywords}')
        else:
            # create event from this trend if no existing events matches 
            event = db.save_event(conn, Event(name=trend.name, keywords=keywords))
            assert event.id
            print(f'Inserted event {event.name} with id {event.id}, keywords: {keywords}')


    return event


def process_trend(conn, api, classifier, trend, events):
    try: 
        # load popular tweets
        tweets = [tweet_from_api(t) for t in get_popular_tweets(api, trend.query)]
        print(f'Loaded {len(tweets)} tweets')

        # form tweets keywords
        tweets_keywords = get_keywords(tweets, classifier)
        print(f'Formed keywords: {tweets_keywords}')

        event = match_event(conn, trend, tweets_keywords, events)
        assert event
        assert event.id

        for tweet in tweets:
            tweet.event_id = event.id
            with conn:
                db.save_tweet(conn, tweet)
                #print(f'{trend.name} tweet saved: {tweet.text}')

    except AssertionError:
        raise
    except Exception as e:
        print(f'Error processing twitter trend {trend.name}: {e}')
        traceback.print_exc()


def main():
    conn = sqlite3.connect('database/napp.db', 
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    # create database if does not exist
    with conn:
        db.create_database(conn)

    # load recent events from database (added in the lase 3 days)
    start_date = date.today() - timedelta(days=3)
    events = list(db.find_events_since(conn, start_date))
    print(f'Loaded {len(events)} existing recent events')

    # load NLP classifier
    classifier = Classifier()

    # connect to twitter API
    api = twitter.Api(consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
                      consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
                      access_token_key=os.environ['TWITTER_ACCESS_TOKEN'],
                      access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET'])

    # query regional trends from twitter
    trends = list(api.GetTrendsWoeid(woeid[config.country_code]))

    for trend in trends[:3]:
        print(f'Processing twitter trend: {trend.name}')
        process_trend(conn, api, classifier, trend, events)
    
    if conn:
        conn.close()


if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
