import os
import sqlite3
import time
from datetime import datetime
from napp.database import create_database, insert_news, check_headline
from napp.news_loader.news import NewsLoader

def main():
    conn = sqlite3.connect('database/napp.db')
    newsloader = NewsLoader(os.environ['NEWSAPI_KEY'])

    with conn:
        create_database(conn)
        country_code = 'gb'

        while True:
            load_news(conn, newsloader, country_code)
            conn.commit()
            time.sleep(10)


def load_news(conn, newsloader, country_code):
    print('{} Loading News...'.format(datetime.now()))
    response = newsloader.get_news(country_code)

    for article in response.articles:
        headline = article.title
        source = article.source.name
        url = article.url
        if check_headline(conn, headline) == 0:
            news_id = insert_news(conn, headline, source, url, country_code)
            print(news_id, source, headline)


if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
        