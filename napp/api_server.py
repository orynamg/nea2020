import uvicorn
from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
import sqlite3
from database import NappDatabase
from datetime import datetime

app = FastAPI()

conn = sqlite3.connect('database/napp.db', 
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

db = NappDatabase(conn)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/news/{news_id}")
async def get_news_by_id(news_id):
    return db.find_news_by_id(news_id)


@app.get("/news")
async def get_news(limit: int = 10, offset: int = 0, since = None):
    if since:
        since_dt = datetime.fromisoformat(since)
        return db.find_news_since(since_dt)
    return db.find_news(limit, offset)


@app.get("/events")
async def get_events(limit: int = 10, offset: int = 0, since = None):
    if since:
        since_dt = datetime.fromisoformat(since)
        return db.find_events_since(since_dt)
    return db.find_events(limit, offset)


@app.get("/tweets")
async def get_tweets(limit: int = 10, offset: int = 0, event_id = None):
    if event_id:
        evnt_id = int(event_id)
        return db.find_tweets_by_event_id(event_id)
    return db.find_tweets(limit, offset)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
