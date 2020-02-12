import os
import pickle
import csv
import re
import spacy
from newsapi import NewsApiClient

Categories = ['business', 'entertainment', 'health', 'tech & science', 'environment', 'lgbt', 'youth']

def clean_text(s):
    return(remove_extra_space(s.lower()))

def remove_extra_space(s):
    s = re.sub(r'\s\W',' ',s)
    s = re.sub(r'\W\s',' ',s)
    return re.sub(r'\s+',' ',s)

class Classifier:
    def __init__(self, model_filename='model/nb.model', vectoriser_filename='model/nb.vectorizer'):
        self.model = pickle.load(open(model_filename, 'rb'))
        self.vectoriser = pickle.load(open(vectoriser_filename, 'rb'))
        self.env_terms = self.load_terms('model/env_terms.csv', lambda row: row[1])
        self.lgbt_terms = self.load_terms('model/lgbt_terms.csv', lambda row: row[0])
        self.youth_terms = self.load_terms('model/youth_terms.csv', lambda row: row[0])
        self.nlp = spacy.load("en_core_web_md")

    def load_terms(self, filename, extract):
        terms = set()
        with open(filename) as f:
            reader = csv.reader(f)
            for row in reader:
                terms.add(extract(row).lower())
        
        return terms 

    def predict_category(self, text):
        normalised = [clean_text(text)]
        x = self.vectoriser.transform(normalised)
        y = self.model.predict(x)
        if self.match(text, self.env_terms):
            return 4 
        if self.match(text, self.lgbt_terms):
            return 5 
        if self.match(text, self.youth_terms):
            return 6

        return int(y[0])

    def match(self, text, terms):
        words = clean_text(text).split(' ')
        twograms = [words[i] + ' ' + words[i+1] for i in range(len(words)-1)]
        threegrams = [words[i] + ' ' + words[i+1] + ' ' + words[i+2] for i in range(len(words)-2)]
        words.extend(twograms)
        words.extend(threegrams)
    
        for word in words:
            if word in terms:
                return True
        return False 
    
    def get_named_entities(self, text):
        doc = self.nlp(text)
        keywords = set(ent.text.lower() for ent in doc.ents 
            if ent.label_ not in ['DATE','TIME','PERCENT','MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL'])
        if "coronavirus" in text.lower(): 
            keywords.add('coronavirus') 
        return keywords
    
    def get_keywords(self, text):
        text = remove_extra_space(text)
        words = text.split(' ')
        # leave only those that start with a capital letter (presumably the most meaninful)
        words = [w for w in words if w[0] == w[0].upper()]
        return words


def main():
    classifier = Classifier()
    #print(model.predict_category('Apple arcade goes live for iOS 13 beta testers - The Verge'))
    #print(classifier.get_named_entities('Sir Rod  Stewart  charged over Florida hotel \'punch\''))
    print(classifier.get_keywords('Sir Rod  Stewart  charged over Florida hotel \'punch\''))
    return
    
    newsapi = NewsApiClient(api_key=os.environ['NEWSAPI_KEY'])
    response = newsapi.get_top_headlines(language='en', country='gb')

    for article in response['articles']:
        headline = article['title']
        category_id = classifier.predict_category(headline)
        keywords = classifier.get_named_entities(headline)
        
        print('{0:<14} | {1}\n{2}\n'.format(Categories[category_id], headline, keywords))


if __name__ == '__main__':
    main() 