import os
import sqlite3
import time
from datetime import datetime, date, timedelta
from newsapi import NewsApiClient
from database import NappDatabase
from models import News, Event
from classifier import Classifier, Categories

COUNTRY_CODE = 'gb'
PAUSE_SEC = 30


def news_from_api(api_news):
    return News(
        headline = api_news['title'],
        source = api_news['source']['name'],
        url = api_news['url']
    )


def match_event(news, events, classifier):
    event = None

    position = news.headline.find(" - ")
    headline = news.headline[:position if position else len(news.headline)]

    keywords = classifier.get_named_entities(headline)
    if not keywords:
        keywords = headline.split(" ")

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


def load_news(db, news_api, classifier):
    # load news headlines from newsapi.org
    response = news_api.get_top_headlines(language='en', country=COUNTRY_CODE)
    news_list = [news_from_api(obj) for obj in response['articles']]
    print(f'{datetime.now()} Loaded {len(news_list)} news headlines')

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
        news = db.save_news(news)
        print(f'{datetime.now()} {Categories[news.category_id]:<14} {news.id:>4} {news.headline}')

            
def main():
    conn = sqlite3.connect('database/napp.db', 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    
    db = NappDatabase(conn)
                
    news_api = NewsApiClient(api_key=os.environ['NEWSAPI_KEY'])

    classifier = Classifier()

    while True:
        load_news(db, news_api, classifier)
        print('Pausing...')
        time.sleep(PAUSE_SEC)

    if conn:
        conn.close()


if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
                


