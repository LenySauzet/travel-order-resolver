import random
import json
import pandas as pd
from string import Formatter
import sys
sys.path.insert(0, 'base/src')
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

# Synonym replacements applied to templates before entity injection
SYNONYMS = {
    "depuis": ["de", "au depart de", "en partant de", "a partir de"],
    "vers": ["a", "pour", "direction", "destination"],
    "train": ["TGV", "TER", "transport"],
    "billet": ["ticket", "titre de transport"],
    "trajet": ["voyage", "parcours", "itineraire"],
}

TEMPLATES = [
    # --- Standard / formal ---
    "de {departure} vers {destination}",
    "{destination} de {departure}",
    "pour {destination}",
    "je voudrais un billet de {departure} a {destination} pour {time}",
    "je souhaite me rendre a {destination} depuis {departure} {time}",
    "a quelle heure y a t il des trains vers {destination} {time} en partance de {departure}",
    "comment me rendre a {destination} depuis {departure} {time}",
    "je veux aller a {destination} en partant de {departure} {time}",
    "{time} je cherche un trajet de {departure} a {destination}",
    "billet de train de {departure} a {destination} {time}",
    "quels sont les horaires pour {destination} au depart de {departure} {time}",
    "est ce qu il y a un train de {departure} a {destination} {time}",
    "trajet de {departure} a {destination} {time} le moins cher",
    "{departure} vers {destination} pour {time}",
    "quels sont les prochains departs de {departure} a destination de {destination} {time}",
    "reserver un billet entre {departure} et {destination} pour {time}",
    "je cherche a voyager de {departure} a {destination} {time}",
    "possibilite d aller a {destination} depuis {departure} {time}",
    "{departure} destination {destination} depart {time}",
    "{time} existe t il un trajet de {departure} a {destination}",
    "quand part le prochain train pour {destination} depuis {departure} {time}",
    "aller simple de {departure} a {destination} {time}",
    "combien coute un billet de {departure} a {destination} pour {time}",
    "je voudrais partir de {departure} a {destination} {time}",
    "quels itineraires pour aller a {destination} a partir de {departure} {time}",
    "J'aimerais plutôt bien manger sur {departure} ce midi, du coup un train qui part ce matin et j'habite {destination} pour info",
    "je souhaitais me rendre à Marseille mais finalement {destination} c'est mieux de {departure}...",
    "Un pote qui habite Avignon m'a conseillé {destination} donc ce serait d'ici {departure}",
    "Je veux retourner à {departure}, viens on bouge. un billet d'{departure} c'est pas trop chère",
    "Quand j'ai fait le trajet pour {departure} hier, j'ai perdu mon stylo. Demain en rentrant sur {destination} je vais le chercher",
    "On peut faire un {departure} - {destination} {time}?",
    "Rentrons sur {destination} demain, si on  quitte {departure} tôt on peuit le faire",
    "Partons de {departure} vers {destination}",
    "{destination} en provenance de {departure}",
    "Allons de {departure} à destination de {destination}",
    "Partons de {departure}, {destination} nous attend",
    "{departure} à {destination}",
    "Le voyage de {departure} vers {destination}",
    "Je souhaite aller de {departure} à {destination}",
    "Mon trajet {departure} à {destination}",
    "Donne le trajet de {departure} a {destination} stp",
    "Le trajet de {departure} vers {destination} est dispo ?",
    "Avec Luc on part de {departure} pour aller a {destination}",
    "On est à {departure}, on veut décale à {destination}",
    "Je pars de {departure}, je vais aller à {destination} avec un pull orange",
    "Comment je me déplace à {destination} de {departure} ?",
    "à {departure} aujourd'hui, je pars à {destination} demain",
    "Je pars de {departure} et je veux aller au mcdo de {destination}",
    "Moi c'est étienne, je veux aller à {destination} demain avec Malo. Nous partons de {departure}",
    "Je m'échappe à {destination} demain, il y a des billets depuis {departure} ?",
    "Je vais à {destination} pour le boulot, en partant de {departure}",
    "Je suis situé à {departure}, un train pour {destination} est-il disponible ?",
    "Je souhaite aller d'{departure} vers {destination}",
    "Puis-je partir de {departure} et arriver à {destination} ?",
    "Le trajet {departure} - {destination} est-il disponible ?",
    "Je souhaite aller d {departure} vers {destination}",
    "Puis je partir de {departure} et arriver a {destination} ?",
    "Le trajet {departure} - {destination} est il disponible ?",
    "Je vais a {destination} pour le boulot en partant de {departure}",
    "Je suis situe a {departure} un train pour {destination} est il disponible ?",
    "nous voulons aller a {destination} nous partons de {departure}",
    

    # --- Informal / SMS ---
    "ya un train {departure} {destination} {time} ?",
    "besoin daller a {destination} je suis a {departure} {time}",
    "comment jfais pour aller a {destination} de {departure} {time}",
    "faut que jaille a {destination} depuis {departure} {time}",
    "jdois aller a {destination} jepars de {departure} {time}",
    "un truc pour {destination} au depart de {departure} {time}",
    "{departure} {destination} ca marche {time} ?",
    "jvais a {destination} depuis {departure} {time}",
    "jsuis a {departure} jveux aller a {destination} {time}",
    "jveux aller de {departure} a {destination} {time}",
    "on part de {departure} pour aller a {destination} {time}",
    "on est a {departure} on veut decaler a {destination} {time}",
    "train pour {destination} depuis {departure} {time} ?",
    "Avec un pote on part de {departure} pour aller a {destination} {time}",
    "je m echappe a {destination} il y a des billets depuis {departure} {time} ?",

    # --- Questions / interrogative ---
    "Peut on aller de {departure} vers {destination} {time} ?",
    "Y a t il un train de {departure} a {destination} {time} ?",
    "C est possible {departure} {destination} {time} ?",
    "Comment faire pour aller de {departure} a {destination} {time} ?",
    "Quel train prendre de {departure} pour {destination} {time} ?",
    "On peut partir de {departure} et arriver a {destination} {time} ?",
    "Il existe un trajet {departure} {destination} {time} ?",

    # --- Reversed / varied word order ---
    "{destination} svp je pars de {departure} {time}",
    "Pour aller a {destination} je suis a {departure} {time}",
    "Direction {destination} depart de {departure} {time}",
    "Arrivee {destination} depart {departure} {time}",
    "{destination} en partant de {departure} c est possible {time} ?",
    "Vers {destination} au depart de {departure} {time}",
    "partir a {destination} depuis {departure} {time}",
    "Comment je me deplace a {destination} de {departure} {time} ?",

    # --- Typos / common mistakes ---
    "je voudrai aller a {destination} depuis {departure} {time}",
    "aler a {destination} depuis {departure} {time}",
    "un bilet {departure} {destination} {time}",
    "trajet de {departure} ver {destination} {time}",
    "je veu aller de {departure} a {destination} {time}",

    # --- Arrow / shorthand ---
    "{departure} => {destination}",
    "{departure} > {destination}",
    "{departure} - {destination}",
    "trajet: {departure} -> {destination} {time}",
    "{departure} -> {destination} pour moi svp",
    "billet {departure} {destination} svp",
    "Je cherche un {departure} - {destination} {time}",
    "On peut faire un {departure} - {destination} {time} ?",

    # --- Contextual / natural ---
    "je dois me rendre a {destination} je suis actuellement a {departure} {time}",
    "comment rejoindre {destination} en partant de {departure} {time}",
    "je me trouve a {departure} et je veux rejoindre {destination} {time}",
    "besoin de voyager de {departure} a {destination} {time}",
    "faut que je parte de {departure} pour aller a {destination} {time}",
    "je cherche a me deplacer de {departure} vers {destination} {time}",
    "je voudrais rejoindre {destination} depuis {departure} {time}",
    "a {departure} aujourd hui je pars a {destination} {time}",
    "je pars de {departure} je vais aller a {destination} {time}",
    "Moi c est paul je veux aller a {destination} avec un ami nous partons de {departure} {time}",

    "Je pars de {departure} je vais aller a {destination} avec un pull orange",
    "Je pars de {departure} et je veux aller au mcdo de {destination}",
]

LABELS = {"departure": "DEPARTURE", "destination": "DESTINATION", "time": "TIME"}


def apply_synonyms(template):
    """Randomly replace words with synonyms in the template (before entity injection)."""
    if random.random() < 0.15:
        for word, syns in SYNONYMS.items():
            if word in template and random.random() < 0.5:
                template = template.replace(word, random.choice(syns), 1)
    return template


def add_random_variations(text):
    """Add natural text variations while keeping entity offsets aligned."""
    # 15% chance: remove some accents (length-preserving replacements)
    if random.random() < 0.15:
        text = text.replace("à", "a").replace("é", "e").replace("è", "e").replace("ê", "e")

    # 10% chance: replace punctuation with spaces (length-preserving)
    if random.random() < 0.10:
        text = text.replace("?", " ").replace("!", " ").replace(",", " ").replace("-", " ")
    

    return text


def generate_example():
    template = random.choice(TEMPLATES)
    departure, destination = random.sample(ENTRIES, 2)
    time = random.choice(TIMES)


    # Randomly downcase some entries to add variability
    if random.random() < 0.3:
        departure = departure.lower()
    if random.random() < 0.3:
        destination = destination.lower()

    values = {"departure": departure, "destination": destination, "time": time}

    entities = []
    parts = []
    pos = 0

    for literal, field_name, _, _ in Formatter().parse(template):
        parts.append(literal)
        pos += len(literal)

        if field_name:
            value = values[field_name]
            entities.append({"start": pos, "end": pos + len(value), "label": LABELS[field_name]})
            parts.append(value)
            pos += len(value)

    final_text = "".join(parts)

    # Apply random post-processing variations
    final_text = add_random_variations(final_text)

    return {"text": final_text, "entities": entities}


def generate_dataset(n=500):
    return [generate_example() for _ in range(n)]


dataset = generate_dataset(20000)

with open('base/data/processed/travel-order-dataset.json', 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=4)

print(f"dataset generated with {len(dataset)} examples.")
print(f"templates: {len(TEMPLATES)}, stations: {len(ENTRIES)}, time expressions: {len(TIMES)}")
print("\nSample:")
for i in range(5):
    print(f"  {dataset[i][0]}")