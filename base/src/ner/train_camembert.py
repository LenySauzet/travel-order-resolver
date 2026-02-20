"""
Training CamemBERT NER Model for Travel Orders
Fine-tuning Jean-Baptiste/camembert-ner for DEPARTURE, DESTINATION and TIME entities.

Run from project root:
    uv run python base/src/ner/train_camembert.py
"""

import json
import numpy as np
import torch
from collections import Counter
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
    EarlyStoppingCallback,
)
from sklearn.model_selection import train_test_split
from seqeval.metrics import f1_score

LABEL_LIST = [
    "O",
    "B-DEPARTURE",
    "I-DEPARTURE",
    "B-DESTINATION",
    "I-DESTINATION",
    "B-TIME",
    "I-TIME",
]

label2id = {label: i for i, label in enumerate(LABEL_LIST)}
id2label = {i: label for i, label in enumerate(LABEL_LIST)}


class NERDataset(Dataset):
    def __init__(self, data, tokenizer, max_length=64):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item["text"]
        entities = item["entities"]

        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_offsets_mapping=True,
            return_tensors="pt",
        )

        labels = self._align_labels(text, entities, encoding)

        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(labels),
        }

    def _align_labels(self, text, entities, encoding):
        offset_mapping = encoding["offset_mapping"].squeeze().tolist()
        labels = []
        entity_first_token = {}

        for i, (start, end) in enumerate(offset_mapping):
            if start == 0 and end == 0:
                labels.append(-100)
                continue

            token_label = "O"
            for ent_idx, entity in enumerate(entities):
                e_start, e_end = entity["start"], entity["end"]
                e_label = entity["label"]
                token_mid = (start + end) // 2

                if e_start <= token_mid < e_end:
                    if ent_idx not in entity_first_token:
                        token_label = f"B-{e_label}"
                        entity_first_token[ent_idx] = i
                    else:
                        token_label = f"I-{e_label}"
                    break

            labels.append(label2id[token_label])

        return labels


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)

    true_labels = []
    pred_labels = []

    for pred_seq, label_seq in zip(predictions, labels):
        true_seq = []
        pred_seq_labels = []
        for pred, label in zip(pred_seq, label_seq):
            if label != -100:
                true_seq.append(id2label[label])
                pred_seq_labels.append(id2label[pred])
        true_labels.append(true_seq)
        pred_labels.append(pred_seq_labels)

    return {"f1": f1_score(true_labels, pred_labels)}


def main():
    print("Label mappings:")
    for label, idx in label2id.items():
        print(f"  {label}: {idx}")

    # Load dataset
    with open("base/data/processed/travel-order-dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"\nSample: {json.dumps(dataset[0], indent=2, ensure_ascii=False)}")

    train_data, test_data = train_test_split(dataset, test_size=0.2, random_state=42)
    print(f"\nTraining samples: {len(train_data)}")
    print(f"Test samples: {len(test_data)}")

    label_counts = Counter()
    for sample in train_data:
        for ent in sample["entities"]:
            label_counts[ent["label"]] += 1
    print(f"\nLabel distribution:")
    for label, count in label_counts.items():
        print(f"  {label}: {count}")

    # Load model
    model_name = "Jean-Baptiste/camembert-ner"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL_LIST),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    )

    train_dataset = NERDataset(train_data, tokenizer)
    test_dataset = NERDataset(test_data, tokenizer)
    data_collator = DataCollatorForTokenClassification(tokenizer)

    training_args = TrainingArguments(
        output_dir="base/models/BERT/camembert-ner-travel-checkpoints",
        num_train_epochs=3,
        per_device_train_batch_size=64,
        per_device_eval_batch_size=64,
        learning_rate=5e-5,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir="./logs",
        logging_steps=50,
        warmup_ratio=0.1,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
    )

    print(f"\nTraining with {model_name}:")
    print(f"  Epochs: {training_args.num_train_epochs}")
    print(f"  Batch size: {training_args.per_device_train_batch_size}")
    print(f"  Learning rate: {training_args.learning_rate}")

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    # Train
    print("\nStarting training...\n")
    trainer.train()

    # Save
    model_save_path = "base/models/BERT/camembert-ner-travel"
    trainer.save_model(model_save_path)
    tokenizer.save_pretrained(model_save_path)
    print(f"\nModel saved to: {model_save_path}")

    # Evaluate
    test_results = trainer.evaluate(test_dataset)
    print("\nTest Results:")
    for key, value in test_results.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
