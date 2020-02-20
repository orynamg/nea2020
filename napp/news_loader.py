import os
import sqlite3
import time
from datetime import datetime, date, timedelta
from database import NappDatabase
from models import News, Event
from classifier import Classifier, Categories
from newsapi_source import NewsApiSource
from eventregistry_source import EventRegistrySource

COUNTRY_CODE = 'gb'
PAUSE_SEC = 30


def match_event(news, events, classifier):
    event = None

    position = news.headline.find(" - ")
    headline = news.headline[:position if position else len(news.headline)]

    keywords = classifier.get_named_entities(headline)
    if not keywords:
        keywords = set(headline.split(" "))

    event = next((ev for ev in events if any(keyword in ev.keywords for keyword in keywords)), None)

    if event:
        print(f'{datetime.now()} Exisitng event {event.name} matches news keywords: {keywords}')
        new_keywords = keywords.difference(event.keywords)
        if new_keywords:
            event.name = event.name + ' ' + ' '.join(list(new_keywords)[:3])       
        new_keywords = keywords.union(event.keywords)
        event.keywords = new_keywords
    else:
        generated_name = ' '.join(list(keywords)[:10])
        keywords = set(k.lower() for k in keywords) # convert to lowercase
        event = Event(name=generated_name, keywords=keywords)
        print(f'Create event: {event.name}, keywords: {event.keywords}')

    return event


def process_news(db, news_list, classifier):
    # load recent events from database (added in the lase 3 days)
    start_date = date.today() - timedelta(days=3)   

    for news in news_list:
        # skip duplicates
        if db.find_news_headline(news.headline):
            print(f'{datetime.now()} Not saved. Duplicate news found in the database: {news.headline}')
            continue

        news.country_code = COUNTRY_CODE
        news.category_id = classifier.predict_category(news.headline)

        # load latest events
        events = list(db.find_events_since(start_date))
        print(f'{datetime.now()} Loaded {len(events)} existing recent events')

        event = match_event(news, events, classifier)
        assert event
        event = db.save_event(event)
        assert event.id
        print(f'Saved event id: {event.id} name: {event.name} , keywords: {event.keywords}')

        news.event_id = event.id

        # TODO: summary here
        if news.text:
            news.summary = news.text[:300]

        news = db.save_news(news)
        print(f'{datetime.now()} {Categories[news.category_id]:<14} {news.id:>4} {news.headline}')


def load_news(sources, action):
    # dictionary maps url to news to avoid duplicates from different sources
    news_list = {}
    for source in sources:
        news = action(source)
        print(f'{datetime.now()} Loaded {len(news)} news from {source}')
        news_list.update({n.url:n for n in news})

    return news_list.values()


def main():
    conn = sqlite3.connect('database/napp.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    db = NappDatabase(conn)

    classifier = Classifier()

    newsapi_org = NewsApiSource(
                api_key=os.getenv('NEWSAPI_KEY'), 
                record_response_file='tests/data/newsapi.json'
    )
    event_registry_api = EventRegistrySource(
                api_key=os.getenv('EVENT_REGISTRY_KEY'),
                record_response_file='tests/data/event_registry_org3.json',
                max_items=30
    )

    while True:
        news_list = load_news(
            sources=[
                # newsapi_org,
                event_registry_api
            ],
            # action=lambda source: source.load_news(language='en', country=COUNTRY_CODE)
            action=lambda source: source.load_news_from_file()
        )
        process_news(db, news_list, classifier)

        print('Pausing...')
        time.sleep(PAUSE_SEC)

    if conn:
        conn.close()


if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
                


