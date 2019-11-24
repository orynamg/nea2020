import sqlite3
from database import create_database, insert_news, check_headline
from news import NewsLoader
import schedule
from datetime import datetime
import time

def main():
    conn = sqlite3.connect('database/napp.db')
    newsloader = NewsLoader('16b987ce39464b8296c81b36bc541075')

    with conn:
        create_database(conn)
        country_code = 'gb'

        while True:
            load_news(conn, newsloader, country_code)
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
            print(news_id)


if __name__ == "__main__":
   try:
       main()
   except KeyboardInterrupt:
        print(' Exiting...')
        