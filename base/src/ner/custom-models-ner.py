import random
import json
import spacy
from spacy.util import minibatch
from spacy.training.example import Example

# train_data = [
#     ("What is the price of 10 bananas?", {"entities": [(21, 23, "QUANTITY"), (24, 31, "PRODUCT")]}),
# ]

# use the train_data.json file
with open('base/src/ner/train_data.json', 'r') as f:
    train_data = json.load(f)

nlp = spacy.load('en_core_web_md')

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

nlp.to_disk('base/models/ner/custom-ner-model')

trained_nlp = spacy.load('base/models/ner/custom-ner-model')

test_texts = [
    'How much money for 16 pineapples?',
    'Can you tell me the price of 7 strawberries?',
    'Can I get the cost of 14 oranges?',
    'Price check: 14 tomatoes.',
]

for text in test_texts:
    doc = trained_nlp(text)
    print(f'Text: {text}')
    print(f'Entities: {[(ent.text, ent.label_) for ent in doc.ents]}')
    print('-' * 100)