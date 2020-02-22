import os
import pickle
import csv
import re
import json
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

        nlp = spacy.load('en_core_web_sm')

    def remove_and(self, word_list):
        for word in word_list:
            if word.text.lower() == 'and':
                word_list.remove(word)
        return word_list

    def remove_adjectives(self, word_list):
        toDelete = []
        for i, word in enumerate(word_list):
            if word.pos_ == "ADJ" and (i+1)<len(word_list):
                if word_list[i+1].pos_ == "NOUN":
                    toDelete.append(i)
                elif word_list[i+1].pos_ == "CCONJ":
                    toDelete.append(i)
                    toDelete.append(i+1)

        for i in reversed(toDelete):
            word_list.remove(word_list[i])
                    
        return word_list

    # removing description between 'who' and a comma 
    def remove_subdescription(self, word_list): 
        new_wordlist = []
        i = 0
        while (i < len(word_list)):
            if word_list[i].text == 'who' or word_list[i].text == 'which':
                while word_list[i].text != "," and word_list[i].text != "." and i < len(word_list):
                    i += 1 
            new_wordlist.append(word_list[i])
            i += 1
        return new_wordlist

    def parse(self, body):
        nlp_body = self.nlp(body)
        word_list = []
        for word in nlp_body:
            word_list.append(word)

        return word_list

    def make_summary(self, body):
        word_list = self.parse(body)
        new_list = self.remove_adjectives(self.remove_subdescription(word_list))
        key_word_dict = self.key_words(self.freq_dict(word_list))
        summary_list = self.remove_less_freq(key_word_dict, new_list)
        print("Initial word count:", len(word_list), "Summary word count:", len(summary_list))
        return " ".join(str(token) for token in summary_list)

    def freq_dict(self, word_list):
        freq_dict = {}
        for word in word_list:
            if word.pos_ == "NOUN" or word.pos_ == "VERB" or word.pos_ == "PROPN":
                if word.text in freq_dict:
                    freq_dict[word.text] += 1 
                else:
                    freq_dict[word.text] = 1 

        return freq_dict
            
    def key_words(self, freq_dict):
        key_word_dict = {}
        for key, value in freq_dict.items():
            if value > 1:
                key_word_dict[key] = value
        return key_word_dict


    def remove_less_freq(self, key_word_dict, word_list):
        toDelete = []
        i = 0 
        while i < len(word_list):
            contains_freq = False
            startIndex = i
            while i < len(word_list) and word_list[i].text != '.':
                if word_list[i].text in key_word_dict:
                    contains_freq = True
                i+=1
            if not contains_freq:
                toDelete.append((startIndex, i))
            i+=1
        for startIndex, endIndex in reversed(toDelete):
            for i in range(startIndex, endIndex):
                if (i < len(word_list)):
                    word_list.remove(word_list[i])

        return word_list

def main():

    all_bodies = []
    with open('tests/data/event_registry_org3.json') as json_file:
        data = json.load(json_file)
        for article in data:
            all_bodies.append(article['body'])

    classifier = Classifier()

    chosen = 3
    summary = classifier.make_summary(all_bodies[chosen])    
    # print(summary)
    return

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