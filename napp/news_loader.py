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
    keywords = classifier.get_named_entities(news.headline)
    event = None
    if keywords:
        event = next((ev for ev in events if keywords.issubset(ev.keywords)), None)
    if not event:
        if not keywords:
            keywords = classifier.get_keywords(news.headline)
        generated_name = ' '.join(list(keywords)[:5])
        keywords = set(k.lower() for k in keywords) # convert to lowercase
        with conn:
            event = db.save_event(conn, Event(name=generated_name, keywords=keywords))
            assert event.id
            print(f'Inserted event {event.name} with id {event.id}, keywords: {keywords}')

    if event:
        news.event_id = event.id
        print(f'{datetime.now()} Exisitng event {event.name} matches news keywords: {keywords}')


def load_news(conn, api, classifier):
    # load news headlines from newsapi.org
    response = api.get_top_headlines(language='en', country=config.country_code)
    news_list = [news_from_api(obj) for obj in response['articles']]
    print(f'{datetime.now()} Loaded {len(news_list)} news headlines')

    # load recent events from database (added in the lase 3 days)
    start_date = date.today() - timedelta(days=3)
    events = list(db.find_events_since(conn, start_date))
    print(f'{datetime.now()} Loaded {len(events)} existing recent events')

    for news in news_list:
        news.country_code = config.country_code
        news.category_id = classifier.predict_category(news.headline)
        match_event(conn, news, events, classifier)

        if not db.find_news_headline(conn, news.headline):
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
        time.sleep(config.news_loader_sleep_sec)

    if conn:
        conn.close()

if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
                


