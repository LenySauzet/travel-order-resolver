import random
import json
import pandas as pd
from utils import get_offsets
from preprocessing import preprocess_text

CITIES = pd.read_csv('base/data/raw/communes-france-2025.csv', usecols=['nom_standard'])['nom_standard'].tolist()
STATIONS = pd.read_csv('base/data/raw/liste-des-gares.csv', sep=';')['LIBELLE'].tolist()

TIMES = [
    "demain", "ce soir", "lundi prochain", "à 14h", "vers 10 heures",
    "le 15 mars", "ce week-end", "en fin de journée", "mardi à 8h30",
    "tout de suite", "après-demain", "avant midi", "dans l'après-midi",
    "ce matin", "tôt le matin", "à 17h", "en soirée", "samedi à 15h",
    "vendredi soir", "le 22 avril", "entre 13h et 14h", "ce vendredi",
    "pour ce jeudi", "ce mercredi matin", "le week-end prochain",
    "la semaine prochaine", "après le déjeuner", "dès que possible", "fin de matinée",
    "avant le dîner", "au plus tôt", "dans deux jours"
]

TEMPLATES = [
    "Je voudrais un billet {departure} {destination} pour {time}.",
    "Je souhaite me rendre à {destination} depuis {departure} {time}.",
    "A quelle heure y a-t-il des trains vers {destination} {time} en partance de {departure} ?",
    "Comment me rendre à {destination} depuis {departure} {time} ?",
    "Je veux aller à {destination} en partant de {departure} {time}.",
    "{time}, je cherche un trajet de {departure} à {destination}.",
    "billet de train {departure} {destination} {time}",
    "Quels sont les horaires pour {destination} au départ de {departure} {time} ?",
    "Est-ce qu'il y a un train de {departure} à {destination} {time} ?",
    "Trajet {departure} {destination} {time} le moins cher",
    "{departure} vers {destination} pour {time}",
    "Quels sont les prochains départs de {departure} à destination de {destination} {time} ?",
    "Réserver un billet entre {departure} et {destination} pour {time}",
    "Je cherche à voyager de {departure} à {destination} {time}.",
    "Possibilité d'aller à {destination} depuis {departure} {time} ?",
    "{departure}, destination {destination}, départ {time}.",
    "{time}, existe-t-il un trajet de {departure} à {destination} ?",
    "Quand part le prochain train pour {destination} depuis {departure} {time} ?",
    "Aller simple {departure} - {destination} {time}",
    "Combien coûte un billet de {departure} à {destination} pour {time} ?",
    "Je voudrais partir de {departure} à {destination} {time}.",
    "Quels itinéraires pour aller à {destination} à partir de {departure} {time} ?"
]

def generate_example():
    template = random.choice(TEMPLATES)
     
    departure, destination = random.sample(CITIES + STATIONS, 2)
    time = random.choice(TIMES)

    text = template.format(departure=departure, destination=destination, time=time)

    entities = [
        get_offsets(text, departure, "DEPARTURE"),
        get_offsets(text, destination, "DESTINATION"),
        get_offsets(text, time, "TIME")
    ]

    return (text, {"entities": entities})

def generate_dataset(n=500):
    return [generate_example() for _ in range(n)]

dataset = generate_dataset(10)

with open('base/data/processed/travel-order-dataset.json', 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=4)

print(f"dataset generated with {len(dataset)} examples.")