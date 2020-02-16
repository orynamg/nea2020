import json
from dateutil import parser
from eventregistry import EventRegistry, QueryArticlesIter
from models import News

class EventRegistrySource:
    def __init__(self, api_key, record_response_file=None, max_items=10):
        self.api = EventRegistry(apiKey=api_key)
        self.record_response_file = record_response_file
        self.max_items = max_items

    def __str__(self):
        return "EventRegistrySource"

    def news_from_api(self, api_news):
        return News(
            headline = api_news['title'],
            source = api_news['source']['title'],
            url = api_news['url'],
            image_url=api_news['image'],
            text = api_news['body'],
            published_at=parser.isoparse(api_news['dateTimePub'])
        )
    
    def load_news(self, language, country):
        q = QueryArticlesIter(
            lang="eng",
            dateStart="2020-02-12",
            sourceUri="bbc.co.uk"
        )

        articles = []
        for article in q.execQuery(self.api, sortBy = "rel", maxItems = self.max_items):
            articles.append(article)
        
        if self.record_response_file:
            with open(self.record_response_file, 'w') as f:
                json.dump(articles, f, indent=2)

        return [self.news_from_api(obj) for obj in articles]
    
    def load_news_from_file(self):
        with open(self.record_response_file) as f:
            articles = json.load(f)
        return [self.news_from_api(obj) for obj in articles]

