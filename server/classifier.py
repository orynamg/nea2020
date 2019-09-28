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
        self.env_terms = self.load_env_terms()

    def load_env_terms(self):
        terms = set()
        with open('model/env_terms.csv') as f:
            reader = csv.reader(f)
            for row in reader:
                terms.add(row[1])
        
        return terms 

    def predict(self, headline):
        normalised = [normalize_text(headline)]
        x = self.vectoriser.transform(normalised)
        y = self.model.predict(x)
        if self.is_env(headline):
            return 4 #environment

        return y[0]

    def is_env(self, headline):
        words = headline.split(" ")
        twograms = [words[i] + " " + words[i+1] for i in range(len(words)-1)]
        threegrams = [words[i] + " " + words[i+1] + " " + words[i+2] for i in range(len(words)-2)]
        words.extend(twograms)
        words.extend(threegrams)
    
        for word in words:
            if word in self.env_terms:
                return True
        return False 
            

