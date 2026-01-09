import random
import json
from faker import Faker

fake = Faker()

TEMPLATES = [
    "What is the price of {quantity} {product}?",
    "How much do {quantity} {product} cost?",
    "Can you tell me the price of {quantity} {product}?",
    "What's the cost for {quantity} {product}?",
    "How expensive are {quantity} {product}?",
    "Give me the price of {quantity} {product}.",
    "Do you know the price for {quantity} {product}?",
    "What would {quantity} {product} cost?",
    "Tell me how much {quantity} {product} are.",
    "What is the cost of {quantity} {product}?",
    "How much money for {quantity} {product}?",
    "Price check: {quantity} {product}.",
    "How much are {quantity} {product} today?",
    "What's the price on {quantity} {product}?",
    "Can I get the cost of {quantity} {product}?",
    "How much would {quantity} {product} be?",
    "Tell me the cost for {quantity} {product}.",
    "What do {quantity} {product} cost?",
    "Check the price of {quantity} {product}.",
    "What's the total price of {quantity} {product}?",
]

PRODUCTS = [
    "bananas", "apples", "oranges", "eggs", "pineapples",
    "tomatoes", "potatoes", "cucumbers", "carrots", "onions",
    "lemons", "peaches", "pears", "strawberries", "kiwis",
    "mangoes", "avocados", "cherries", "watermelons", "blueberries"
]

def generate_example():
    template = random.choice(TEMPLATES)
    quantity = str(random.randint(1, 25))
    product = random.choice(PRODUCTS)

    text = template.format(quantity=quantity, product=product)

    q_start = text.find(quantity)
    q_end = q_start + len(quantity)

    p_start = text.find(product)
    p_end = p_start + len(product)

    entities = [
        (q_start, q_end, "QUANTITY"),
        (p_start, p_end, "PRODUCT")
    ]

    return (text, {"entities": entities})


def generate_dataset(n=20):
    return [generate_example() for _ in range(n)]

with open('base/src/ner/train_data.json', 'w') as f:
    train_data = generate_dataset(30)
    json.dump(train_data, f)
