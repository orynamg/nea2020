import sqlite3
from classifier import Categories
from models import *


def create_database(conn):
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
            Headline VARCHAR NOT NULL,
            Source VARCHAR NOT NULL, 
            URL VARCHAR NOT NULL,
            CountryCode CHAR(3) NOT NULL,
            CategoryID INTEGER, 
            EventID INTEGER,
            NewsBody INTEGER,
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
        CreatedAt TIMESTAMP DEFUALT CURRENT_TIMESTAMP,
        FOREIGN KEY(CategoryID) REFERENCES Category(CategoryID),
        FOREIGN KEY(EventID) REFERENCES Event(EventID)
    );
    """
    conn.execute(create_category_table)
    conn.execute(create_event_table)
    conn.execute(create_news_table)
    conn.execute(create_tweet_table)

    # seed categories
    conn.executemany(
        "INSERT INTO Category(CategoryID, Name) values (?, ?) ON CONFLICT DO NOTHING", enumerate(Categories))


def insert_news(conn, headline, source, url, coutry_code):

    sql = """ INSERT INTO News(Headline, Source, URL, CountryCode)
              VALUES(?,?,?,?); """

    cur = conn.cursor()
    cur.execute(sql, (headline, source, url, coutry_code))

    return cur.lastrowid


def check_headline(conn, headline):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM News WHERE headline=?", (headline,))

    result = cur.fetchone()[0]
    return result


def get_news(conn):
    c = conn.cursor()
    for row in c.execute('SELECT * FROM News'):
        yield row


def save_tweet(conn, tweet):
    sql = """ INSERT OR REPLACE INTO Tweet(TweetID, Text, Hashtags, User, URL, CategoryID, EventID, PublishedAt)
              VALUES(?,?,?,?,?,?,?,?); """

    cur = conn.cursor()
    cur.execute(sql, (tweet.id, tweet.text, tweet.hashtags, tweet.user, tweet.url, 
                        tweet.category_id, tweet.event_id, tweet.published_at))
    return tweet


def save_event(conn, event):
    sql = """ INSERT INTO Event(Name, Summary, Keywords)
              VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET 
                Summary=excluded.Summary,
                Keywords=excluded.Keywords; """

    keywords_text = ','.join(event.keywords)

    cur = conn.cursor()
    cur.execute(sql, (event.name, event.summary, keywords_text))

    # if not event.id and cur.rowcount == 1:
    #     event.id = cur.lastrowid
    for row in conn.execute("SELECT * FROM Event WHERE Name=?", (event.name,)):
        event.id = row[0]
        break

    return event


def _event_from_row(row):
    return Event(
        id = row[0],
        name = row[1],
        summary = row[2] if row[2] else '',
        keywords = set(row[3].split(',')) if row[3] else set(),
        created_at = row[4]
    )


def find_events_since(conn, start_date):
    c = conn.cursor()
    c.execute("SELECT * FROM Event WHERE CreatedAt >= ?", (start_date,))
    for row in c.fetchall():
        yield _event_from_row(row)
