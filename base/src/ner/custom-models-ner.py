import random
import json
import spacy
from spacy.util import minibatch
from spacy.training.example import Example

with open('base/data/processed/travel-order-dataset.json', 'r') as f:
    train_data = json.load(f)

nlp = spacy.load('fr_core_news_md')

if 'ner' not in nlp.pipe_names:
    ner = nlp.add_pipe('ner')
else:
    ner = nlp.get_pipe('ner')

for _, annotations in train_data:
    for ent in annotations['entities']:
        if ent[2] not in ner.labels:
            ner.add_label(ent[2])

other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
with nlp.disable_pipes(*other_pipes):
    optimizer = nlp.resume_training()

    epochs = 50
    for epoch in range(epochs):
        random.shuffle(train_data)
        losses = {}
        batches = minibatch(train_data, size=2)
        for batch in batches:
            exemples = []
            for text, annotations in batch:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                exemples.append(example)
            nlp.update(exemples, drop=0.5, losses=losses)
        print(f'Epoch: {epoch}, Losses: {losses}')

nlp.to_disk('base/models/travel-order-ner-model')

trained_nlp = spacy.load('base/models/travel-order-ner-model')

test_texts = [
    'Je voudrais un billet Paris Toulouse demain à 14h.',
    'Je souhaite me rendre à Lyon depuis Paris ce soir.',
    'A quelle heure y a-t-il des trains vers Toulouse mardi à 8h30 en partance de Paris ?',
    'Comment me rendre à Toulouse depuis Paris lundi prochain ?',
    'Je veux aller à Toulouse en partant de Paris ce week-end.',
    'Trajet de Paris vers Toulouse en fin de journée.',
    'Je cherche un train allant de Paris à Toulouse après-demain.',
    'billet de train Paris Toulouse demain',
    'Quels sont les horaires pour Toulouse au départ de Paris le 15 mars ?',
]

for text in test_texts:
    doc = trained_nlp(text)
    print(f'Text: {text}')
    print(f'Entities: {[(ent.text, ent.label_) for ent in doc.ents]}')
    print('-' * 100)