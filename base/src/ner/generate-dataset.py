import random
import json
import pandas as pd
from string import Formatter
import sys
sys.path.append('base/src')
from preprocessing import normalize_text

ENTRIES = pd.read_csv('base/data/processed/entries.csv', usecols=['entries'])['entries'].tolist()

TIMES = [
    normalize_text(t) for t in [
        "demain", "ce soir", "lundi prochain", "à 14h", "vers 10 heures",
        "le 15 mars", "ce week-end", "en fin de journée", "mardi à 8h30",
        "tout de suite", "après-demain", "avant midi", "dans l'après-midi",
        "ce matin", "tôt le matin", "à 17h", "en soirée", "samedi à 15h",
        "vendredi soir", "le 22 avril", "entre 13h et 14h", "ce vendredi",
        "pour ce jeudi", "ce mercredi matin", "le week-end prochain",
        "la semaine prochaine", "après le déjeuner", "dès que possible", "fin de matinée",
        "avant le dîner", "au plus tôt", "dans deux jours"
    ]
]

TEMPLATES = [
    "je voudrais un billet {departure} {destination} pour {time}",
    "je souhaite me rendre a {destination} depuis {departure} {time}",
    "a quelle heure y a t il des trains vers {destination} {time} en partance de {departure}",
    "comment me rendre a {destination} depuis {departure} {time}",
    "je veux aller a {destination} en partant de {departure} {time}",
    "{time} je cherche un trajet de {departure} a {destination}",
    "billet de train {departure} {destination} {time}",
    "quels sont les horaires pour {destination} au depart de {departure} {time}",
    "est ce qu il y a un train de {departure} a {destination} {time}",
    "trajet {departure} {destination} {time} le moins cher",
    "{departure} vers {destination} pour {time}",
    "quels sont les prochains departs de {departure} a destination de {destination} {time}",
    "reserver un billet entre {departure} et {destination} pour {time}",
    "je cherche a voyager de {departure} a {destination} {time}",
    "possibilite d aller a {destination} depuis {departure} {time}",
    "{departure} destination {destination} depart {time}",
    "{time} existe t il un trajet de {departure} a {destination}",
    "quand part le prochain train pour {destination} depuis {departure} {time}",
    "aller simple {departure} {destination} {time}",
    "combien coute un billet de {departure} a {destination} pour {time}",
    "je voudrais partir de {departure} a {destination} {time}",
    "quels itineraires pour aller a {destination} a partir de {departure} {time}"
]

LABELS = {"departure": "DEPARTURE", "destination": "DESTINATION", "time": "TIME"}

def generate_example():
    template = random.choice(TEMPLATES)
    departure, destination = random.sample(ENTRIES, 2)
    time = random.choice(TIMES)

    values = {"departure": departure, "destination": destination, "time": time}

    entities = []
    parts = []
    pos = 0

    for literal, field_name, _, _ in Formatter().parse(template):
        parts.append(literal)
        pos += len(literal)

        if field_name:
            value = values[field_name]
            entities.append((pos, pos + len(value), LABELS[field_name]))
            parts.append(value)
            pos += len(value)

    return ("".join(parts), {"entities": entities})

def generate_dataset(n=500):
    return [generate_example() for _ in range(n)]

dataset = generate_dataset(500)

with open('base/data/processed/travel-order-dataset.json', 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=4)

print(f"dataset generated with {len(dataset)} examples.")