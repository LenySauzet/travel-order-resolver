import spacy

texts = [
    # in french
    # 'Jhone va se promener à Berlin',
    # 'Mike va au magasin',
    # 'Elon Musq est le PDG de Twitter',
    # 'Bob Smith est le gars derrière XYZ-Soft Inc.',
    # 'Florian Dedov est le gars derrière NeuralNine',
    # 'Quel est le prix de 4 bananes ?',
    # 'Combien coûtent 16 chaises ?',
    # 'Donnez-moi la valeur de 5 ordinateurs portables.',
    # 'Donnez-moi la valeur de cinq ordinateurs portables.',

    # in english
    # 'John goes for a walk in Berlin',
    # 'Mike goes to the store',
    # 'Elon Musk is the CEO of Twitter',
    # 'Bob Smith is the guy behind XYZ-Soft Inc.',
    # 'Florian Dedov is the guy behind NeuralNine',
    'What is the price of 4 bananas?',
    'How much are 16 chairs?',
    'Give me the value of 5 laptops.',
    'Give me the value of five laptops.',
]

nlp = spacy.load('en_core_web_md')
# nlp = spacy.load('fr_core_news_md')

# ner_labels = nlp.get_pipe('ner').labels
# print(ner_labels)

# categories = ['ORG', 'PER', 'LOC']

docs = [nlp(text) for text in texts]

for doc in docs:
    entities = []
    for ent in doc.ents:
        # if ent.label_ in categories:
            entities.append((ent.text, ent.label_))
    print(entities)
