from newsapi import NewsApiClient
from attrdict import AttrDict


class NewsLoader:
    def __init__(self, api_key):
        self.newsapi = NewsApiClient(api_key=api_key)

    def get_news(self, county):
        response = self.newsapi.get_top_headlines(language='en', country='us')
        return AttrDict(response)

        


