"""
Test a trained CamemBERT NER model on example sentences.

Run from project root:
    uv run python base/src/ner/test_camembert.py
"""

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification


MODEL_PATH = "base/models/BERT/camembert-ner-travel"


def predict(text, model, tokenizer):
    model.eval()
    device = next(model.parameters()).device
    model_id2label = model.config.id2label

    inputs = tokenizer(
        text,
        return_tensors="pt",
        return_offsets_mapping=True,
        padding=True,
        truncation=True,
        max_length=128,
    )

    offset_mapping = inputs.pop("offset_mapping").squeeze().tolist()
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=2).squeeze().tolist()

    if not isinstance(predictions, list):
        predictions = [predictions]

    entities = {"DEPARTURE": [], "DESTINATION": [], "TIME": []}
    current_entity = None
    current_tokens = []

    for i, (pred, (start, end)) in enumerate(zip(predictions, offset_mapping)):
        if start == 0 and end == 0:
            continue

        label = model_id2label.get(pred, "O")

        if label.startswith("B-"):
            if current_entity and current_tokens:
                entity_text = text[current_tokens[0][0]:current_tokens[-1][1]].strip()
                entities[current_entity].append(entity_text)
            current_entity = label[2:]
            current_tokens = [(start, end)]
        elif label.startswith("I-") and current_entity == label[2:]:
            current_tokens.append((start, end))
        else:
            if current_entity and current_tokens:
                entity_text = text[current_tokens[0][0]:current_tokens[-1][1]].strip()
                entities[current_entity].append(entity_text)
            current_entity = None
            current_tokens = []

    if current_entity and current_tokens:
        entity_text = text[current_tokens[0][0]:current_tokens[-1][1]].strip()
        entities[current_entity].append(entity_text)

    return entities


def main():
    print(f"Loading model from {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    print(f"  id2label: {model.config.id2label}")
    print(f"  Device: {device}")

    test_sentences = [
        "Je veux aller de Paris a Marseille",
        "Un billet de Lyon pour Bordeaux s'il vous plait",
        "Je dois partir de Toulouse vers Nice demain",
        "Trajet entre Nantes et Strasbourg lundi prochain",
        "Je cherche un train de Montpellier a Lille a 14h",
        "Horaires des TGV de Rennes a La Rochelle ce vendredi",
        "Je pars de Clermont-Ferrand direction Aix-en-Provence dans l'apres-midi",
        "Y a-t-il un train de Grenoble a Geneve ce soir ?",
    ]

    print("\n" + "=" * 70)
    print("Testing model on real examples:")
    print("=" * 70)

    for sentence in test_sentences:
        entities = predict(sentence, model, tokenizer)
        departure = entities["DEPARTURE"][0] if entities["DEPARTURE"] else "Not found"
        destination = entities["DESTINATION"][0] if entities["DESTINATION"] else "Not found"
        time_ent = entities["TIME"][0] if entities["TIME"] else "Not found"

        print(f"\n{sentence}")
        print(f"  Departure:    {departure}")
        print(f"  Destination:  {destination}")
        print(f"  Time:         {time_ent}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
