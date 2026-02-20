
from doctest import Example
import json
from base.src.preprocessing import unified_to_spacy
import spacy
from spacy.scorer import Scorer


def test_model(model, test_data):
    print(f"Test samples: {len(test_data)}\n")

    examples = []
    for text, annotations in test_data:
        doc = model.make_doc(text)
        example = Example.from_dict(doc, annotations)
        example.predicted = model(text)
        examples.append(example)

    scorer = Scorer()
    scores = scorer.score(examples)

    print(f"Precision: {scores['ents_p']:.2%}")
    print(f"Recall: {scores['ents_r']:.2%}")
    print(f"F1-Score: {scores['ents_f']:.2%}")
    print(f"\nPer-entity scores:")
    for entity_type, metrics in scores['ents_per_type'].items():
        print(f"  {entity_type}:")
        print(f"    Precision: {metrics['p']:.2%}")
        print(f"    Recall: {metrics['r']:.2%}")
        print(f"    F1-Score: {metrics['f']:.2%}")

with open('base/data/processed/travel-order-dataset.json', 'r') as f:
    dataset = json.load(f)

dataset = [unified_to_spacy(item) for item in dataset]

train_split = int(len(dataset) * 0.8)
test_data = dataset[train_split:]

print(f"Test samples: {len(test_data)}")

trained_nlp = spacy.load('base/models/travel-order-ner-model')
print("\n=== Evaluating on Test Data ===")
test_model(trained_nlp, test_data)
print("\n=== Evaluating on Validation Data ===")
test_model(trained_nlp, val_data)