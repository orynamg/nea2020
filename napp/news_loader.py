import os
import sqlite3
import time
import config
from datetime import datetime, date, timedelta
from newsapi import NewsApiClient
import database as db
from models import News, Event
from classifier import Classifier, Categories


def news_from_api(api_news):
    return News(
        headline = api_news['title'],
        source = api_news['source']['name'],
        url = api_news['url']
    )


def match_event(conn, news, events, classifier):
    event = None

    position = news.headline.find(" - ")
    headline = news.headline[:position if position else len(news.headline)]

    keywords = classifier.get_named_entities(headline)
    if not keywords:
            keywords = headline.split(" ")

    event = next((ev for ev in events if any(keyword in ev.keywords for keyword in keywords)), None)

    if event:
        print(f'{datetime.now()} Exisitng event {event.name} matches news keywords: {keywords}')
    else:
        generated_name = ' '.join(list(keywords)[:10])
        keywords = set(k.lower() for k in keywords) # convert to lowercase
        with conn:
            event = db.save_event(conn, Event(name=generated_name, keywords=keywords))
            assert event.id
            print(f'Inserted event {event.name} with id {event.id}, keywords: {keywords}')

    news.event_id = event.id


def load_news(conn, api, classifier):
    # load news headlines from newsapi.org
    response = api.get_top_headlines(language='en', country=config.country_code)
    news_list = [news_from_api(obj) for obj in response['articles']]
    print(f'{datetime.now()} Loaded {len(news_list)} news headlines')

    # load recent events from database (added in the lase 3 days)
    start_date = date.today() - timedelta(days=3)   

    for news in news_list:
        # skip duplicates
        if db.find_news_headline(conn, news.headline):
            print(f'{datetime.now()} Not saved. Duplicate news found in the database: {news.headline}')
            continue

        news.country_code = config.country_code
        news.category_id = classifier.predict_category(news.headline)

        # load latest events
        events = list(db.find_events_since(conn, start_date))
        print(f'{datetime.now()} Loaded {len(events)} existing recent events')

        match_event(conn, news, events, classifier)

        with conn:
            news = db.save_news(conn, news)
            print(f'{datetime.now()} {Categories[news.category_id]:<14} {news.id:>4} {news.headline}')

            


def main():
    conn = sqlite3.connect('database/napp.db', 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
                
    api = NewsApiClient(api_key=os.environ['NEWSAPI_KEY'])

    classifier = Classifier()

    with conn:
        db.create_database(conn)

    while True:
        load_news(conn, api, classifier)
        print('Pausing...')
        time.sleep(config.news_loader_sleep_sec)

    if conn:
        conn.close()

if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
                


