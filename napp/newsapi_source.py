import json
from dateutil import parser
from newsapi import NewsApiClient
from models import News

class NewsApiSource:
    def __init__(self, api_key, record_response_file=None):
        self.api = NewsApiClient(api_key=api_key)
        self.record_response_file=record_response_file
    
    def __str__(self):
        return "NewsApiSource"

    def news_from_api(self, api_news):
        return News(
            headline = api_news['title'],
            source = api_news['source']['name'],
            url = api_news['url'],
            image_url=api_news['urlToImage'],
            text = api_news['content'] if api_news['content'] else api_news['description'],
            published_at=parser.isoparse(api_news['publishedAt'])
        )
    
    def load_news(self, language, country):
        response = self.api.get_top_headlines(language=language, country=country)
        articles = response['articles']

        if self.record_response_file:
            with open(self.record_response_file, 'w') as f:
                json.dump(articles, f, indent=2)

        return [self.news_from_api(obj) for obj in articles]
    
    def load_news_from_file(self):
        with open(self.record_response_file) as f:
            articles = json.load(f)
        return [self.news_from_api(obj) for obj in articles]
