from classifier import Classifier
from newsapi import NewsApiClient

categories = ['business', 'entertainment', 'health', 'tech science', 'environment', 'lgbt', 'youth']

def main():
    model = Classifier()
    #print(model.predict('Apple arcade goes live for iOS 13 beta testers - The Verge'))
    
    newsapi = NewsApiClient(api_key='16b987ce39464b8296c81b36bc541075')
    response = newsapi.get_top_headlines(language='en', country='gb')

    for article in response['articles']:
        headline = article['title']
        cat = model.predict(headline)
        
        print('{0:<13} | {1}'.format(categories[cat], headline))

if __name__ == '__main__':
    main()

    