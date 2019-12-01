import pickle
import csv
import re

def normalize_text(s):
    s = s.lower()
    s = re.sub(r'\s\W',' ',s)
    s = re.sub(r'\W\s',' ',s)
    s = re.sub(r'\s+',' ',s)
    
    return s

class Classifier:
    def __init__(self, model_filename='model/nb.model', vectoriser_filename='model/nb.vectorizer'):
        self.model = pickle.load(open(model_filename, 'rb'))
        self.vectoriser = pickle.load(open(vectoriser_filename, 'rb'))
        self.env_terms = self.load_terms('model/env_terms.csv', lambda row: row[1])
        self.lgbt_terms = self.load_terms('model/lgbt_terms.csv', lambda row: row[0])
        self.youth_terms = self.load_terms('model/youth_terms.csv', lambda row: row[0])

    def load_terms(self, filename, extract):
        terms = set()
        with open(filename) as f:
            reader = csv.reader(f)
            for row in reader:
                terms.add(extract(row).lower())
        
        return terms 

    def predict(self, headline):
        normalised = [normalize_text(headline)]
        x = self.vectoriser.transform(normalised)
        y = self.model.predict(x)
        if self.match(headline, self.env_terms):
            return 4 
        if self.match(headline, self.lgbt_terms):
            return 5 
        if self.match(headline, self.youth_terms):
            return 6

        return y[0]

    def match(self, headline, terms):
        words = normalize_text(headline).split(' ')
        twograms = [words[i] + " " + words[i+1] for i in range(len(words)-1)]
        threegrams = [words[i] + " " + words[i+1] + " " + words[i+2] for i in range(len(words)-2)]
        words.extend(twograms)
        words.extend(threegrams)
    
        for word in words:
            if word in terms:
                return True
        return False 
            

