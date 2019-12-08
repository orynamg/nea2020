import sqlite3

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
        Name VARCHAR NOT NULL,
        Summary VARCHAR,
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
        Tweet VARCHAR NOT NULL,
        Hashtag VARCHAR NOT NULL, 
        URL VARCHAR,
        User VARCHAR NOT NULL,
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


def insert_tweet(conn, text, hashtags, url, author, published_at):
    sql = """ INSERT INTO Tweet(Tweet, Hashtag, URL, User, PublishedAt)
              VALUES(?,?,?,?,?); """

    cur = conn.cursor()
    cur.execute(sql, (text, hashtags, url, author, published_at))
    return cur.lastrowid