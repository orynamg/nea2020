import sqlite3
from classifier import Categories
from models import *
from dateutil import parser

def _sqlite_convert_timestamp(val):
    return parser.isoparse(val)

sqlite3.register_converter("timestamp", _sqlite_convert_timestamp)

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
            Name TEXT NOT NULL
        );
        """
        create_event_table = """
        CREATE TABLE IF NOT EXISTS Event(
            EventID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL UNIQUE,
            Summary TEXT,
            Keywords TEXT,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_news_table = """
            CREATE TABLE IF NOT EXISTS News(
                NewsID INTEGER PRIMARY KEY AUTOINCREMENT,
                Headline TEXT NOT NULL UNIQUE,
                Source TEXT NOT NULL, 
                URL TEXT NOT NULL,
                ImageURL TEXT,
                CountryCode CHAR(3) NOT NULL,
                CategoryID INTEGER, 
                EventID INTEGER,
                Text TEXT,
                Summary TEXT,
                PublishedAt TIMESTAMP,
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(CategoryID) REFERENCES Category(CategoryID), 
            FOREIGN KEY(EventID) REFERENCES Event(EventID)
        );
        """

        create_tweet_table = """
        CREATE TABLE IF NOT EXISTS Tweet(
            TweetID INTEGER PRIMARY KEY AUTOINCREMENT,
            Text TEXT NOT NULL,
            Hashtags TEXT NOT NULL,
            User TEXT NOT NULL,
            URL TEXT,
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
        sql = """ INSERT OR REPLACE INTO News(Headline, Source, URL, ImageURL, CountryCode, CategoryID, EventID, Text, Summary, PublishedAt)
                VALUES(?,?,?,?,?,?,?,?,?,?); """
        
        cur = self.conn.cursor()
        cur.execute(sql, (news.headline, news.source, news.url, news.image_url, news.country_code, 
                            news.category_id, news.event_id, news.text, news.summary, news.published_at))
        
        return self.find_news_headline(news.headline)


    def _news_from_row(self, row):
        return News(
            id = row[0],
            headline = row[1],
            source = row[2],
            url = row[3],
            image_url = row[4],
            country_code = row[5],
            category_id = row[6],
            event_id = row[7],
            text = row[8],
            summary = row[9],
            published_at = row[10],
            created_at = row[11],
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
