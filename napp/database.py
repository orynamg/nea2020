import sqlite3
from classifier import Categories
from models import *

class NappDatabase:

    def __init__(self, conn):
        self.conn = conn
        # create database if does not exist
        with self.conn:
            self.create_database()

    def create_database(self):
        create_category_table = """
        CREATE TABLE IF NOT EXISTS Category(
            CategoryID INTEGER PRIMARY KEY,
            Name VARCHAR NOT NULL
        );
        """
        create_event_table = """
        CREATE TABLE IF NOT EXISTS Event(
            EventID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name VARCHAR NOT NULL UNIQUE,
            Summary VARCHAR,
            Keywords VARCHAR,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_news_table = """
            CREATE TABLE IF NOT EXISTS News(
                NewsID INTEGER PRIMARY KEY AUTOINCREMENT,
                Headline VARCHAR NOT NULL UNIQUE,
                Source VARCHAR NOT NULL, 
                URL VARCHAR NOT NULL,
                CountryCode CHAR(3) NOT NULL,
                CategoryID INTEGER, 
                EventID INTEGER,
                Text VARCHAR,
                ScrapedAt TIMESTAMP,
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(CategoryID) REFERENCES Category(CategoryID), 
            FOREIGN KEY(EventID) REFERENCES Event(EventID)
        );
        """

        create_tweet_table = """
        CREATE TABLE IF NOT EXISTS Tweet(
            TweetID INTEGER PRIMARY KEY AUTOINCREMENT,
            Text VARCHAR NOT NULL,
            Hashtags VARCHAR NOT NULL,
            User VARCHAR NOT NULL,
            URL VARCHAR,
            CategoryID INTEGER, 
            EventID INTEGER,
            PublishedAt TIMESTAMP NOT NULL,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(CategoryID) REFERENCES Category(CategoryID),
            FOREIGN KEY(EventID) REFERENCES Event(EventID)
        );
        """
        self.conn.execute(create_category_table)
        self.conn.execute(create_event_table)
        self.conn.execute(create_news_table)
        self.conn.execute(create_tweet_table)

        # seed categories
        self.conn.executemany(
            "INSERT INTO Category(CategoryID, Name) values (?, ?) ON CONFLICT DO NOTHING", enumerate(Categories))


    def save_news(self, news):
        sql = """ INSERT OR REPLACE INTO News(Headline, Source, URL, CountryCode, CategoryID, EventID, Text, ScrapedAt)
                VALUES(?,?,?,?,?,?,?,?); """
        
        cur = self.conn.cursor()
        cur.execute(sql, (news.headline, news.source, news.url, news.country_code, 
                            news.category_id, news.event_id, news.text, news.scraped_at))
        
        return self.find_news_headline(news.headline)


    def _news_from_row(self, row):
        return News(
            id = row[0],
            headline = row[1],
            source = row[2],
            url = row[3],
            country_code = row[4],
            category_id = row[5],
            event_id = row[6],
            text = row[7],
            scraped_at = row[8],
            created_at = row[9]
        )


    def find_news_headline(self, headline):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM News WHERE headline=?", (headline,))
        row = cur.fetchone()
        if row:
            return self._news_from_row(row)


    def find_news_by_id(self, news_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM News WHERE NewsID=?", (news_id,))
        row = cur.fetchone()
        if row:
            return self._news_from_row(row)


    def find_news(self, limit=10, offset=0):
        c = self.conn.cursor()
        c.execute("SELECT * FROM News ORDER BY CreatedAt DESC LIMIT ? OFFSET ?", (limit, offset))
        for row in c.fetchall():
            yield self._news_from_row(row)


    def find_news_since(self, start_date):
        c = self.conn.cursor()
        c.execute("SELECT * FROM News WHERE CreatedAt >= ?", (start_date,))
        for row in c.fetchall():
            yield self._news_from_row(row)


    def save_tweet(self, tweet):
        sql = """ INSERT OR REPLACE INTO Tweet(TweetID, Text, Hashtags, User, URL, CategoryID, EventID, PublishedAt)
                VALUES(?,?,?,?,?,?,?,?); """
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(sql, (tweet.id, tweet.text, tweet.hashtags, tweet.user, tweet.url, 
                                tweet.category_id, tweet.event_id, tweet.published_at))
            return tweet


    def _tweet_from_row(self, row):
        return Tweet(
            id = row[0],
            text = row[1],
            hashtags = row[2],
            user = row[3],
            url = row[4],
            category_id = row[5], 
            event_id = row[6],
            published_at = row[7],
            created_at = row[8]
        )


    def find_tweets(self, limit=10, offset=0):
        c = self.conn.cursor()
        c.execute("SELECT * FROM Tweet ORDER BY PublishedAt DESC LIMIT ? OFFSET ?", (limit, offset))
        for row in c.fetchall():
            yield self._tweet_from_row(row)


    def find_tweets_by_event_id(self, event_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM Tweet WHERE EventID = ? ORDER BY PublishedAt DESC", (event_id,))
        for row in c.fetchall():
            yield self._tweet_from_row(row)


    def save_event(self, event):
        keywords_text = ','.join(event.keywords)

        sql = "INSERT INTO Event(Name, Summary, Keywords) VALUES(?,?,?)"
        params = (event.name, event.summary, keywords_text)
        
        if event.id:
            sql = "UPDATE Event SET Name=?, Summary=?, Keywords=? WHERE EventID=?"
            params = (event.name, event.summary, keywords_text, event.id)

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(sql, params)

            # if not event.id and cur.rowcount == 1:
            #     event.id = cur.lastrowid
            for row in self.conn.execute("SELECT * FROM Event WHERE Name=?", (event.name,)):
                event.id = row[0]
                break

        return event


    def _event_from_row(self, row):
        return Event(
            id = row[0],
            name = row[1],
            summary = row[2] if row[2] else '',
            keywords = set(row[3].split(',')) if row[3] else set(),
            created_at = row[4]
        )


    def find_events(self, limit=10, offset=0):
        c = self.conn.cursor()
        c.execute("SELECT * FROM Event ORDER BY CreatedAt DESC LIMIT ? OFFSET ?", (limit, offset))
        for row in c.fetchall():
            yield self._event_from_row(row)


    def find_events_since(self, start_date):
        c = self.conn.cursor()
        c.execute("SELECT * FROM Event WHERE CreatedAt >= ?", (start_date,))
        for row in c.fetchall():
            yield self._event_from_row(row)
