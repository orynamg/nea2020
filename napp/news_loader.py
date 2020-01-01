import os
import sqlite3
import time
from datetime import datetime
from newsapi import NewsApiClient
from attrdict import AttrDict
from database import create_database, insert_news, check_headline


class NewsLoader:
    def __init__(self, api_key):
        self.newsapi = NewsApiClient(api_key=api_key)

    def get_news(self, country):
        response = self.newsapi.get_top_headlines(language='en', country=country)
        return AttrDict(response)


def load_news(conn, news_loader, country_code):
    print('{} Loading News...'.format(datetime.now()))
    response = news_loader.get_news(country_code)

    for article in response.articles:
        headline = article.title
        source = article.source.name
        url = article.url
        if check_headline(conn, headline) == 0:
            news_id = insert_news(conn, headline, source, url, country_code)
            print(news_id, source, headline)


def main():
    conn = sqlite3.connect('database/napp.db')
    news_loader = NewsLoader(os.environ['NEWSAPI_KEY'])
    country_code = 'gb'

    with conn:
        create_database(conn)

        while True:
            load_news(conn, news_loader, country_code)
            conn.commit()
            time.sleep(10)


if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
                


