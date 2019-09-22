import pickle
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

    def predict(self, headline):
        normalised = [normalize_text(headline)]
        x = self.vectoriser.transform(normalised)
        y = self.model.predict(x)

        return y[0]
