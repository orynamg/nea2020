import spacy

nlp = spacy.load("en_core_web_sm")

s = "Apple is looking at buying U.K. startup for $1 billion"
s = "breaking president trump’s 200 billion in sanctions on iran has wiped Obama’s 150 billion gift to the country"
# s = s.lower()

doc = nlp(s)
for ent in doc.ents:
    print(ent.text, ent.start_char, ent.end_char, ent.label_)