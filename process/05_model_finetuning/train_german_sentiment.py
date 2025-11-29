import os, json, glob, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import evaluate
import torch.nn.functional as F
from torch import nn
from datasets import Dataset, DatasetDict
import torch
from torch import nn
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    Trainer, TrainingArguments, EarlyStoppingCallback
)

# ===== Config =====
INPUT_DIR   = "./Selbst_belabelt"      # <- dein Ordner mit den 3 JSONs
OUTPUT_DIR  = "./fine_tuned_german_sentiment"
BASE_MODEL  = "oliverguhr/german-sentiment-bert"
USE_TARGET_HINT = True                  # 'target' als Zusatzsignal nutzen
VAL_SIZE    = 0.2
SEED        = 42

labels    = ["negative", "neutral", "positive"]
label2id  = {l:i for i,l in enumerate(labels)}
id2label  = {i:l for l,i in label2id.items()}

def normalize_label(s: str) -> str:
    s = s.strip().lower()
    if s.startswith("pos"): return "positive"
    if s.startswith("neu"): return "neutral"
    if s.startswith("neg"): return "negative"
    raise ValueError(f"Unbekanntes Label: {s}")

# ===== Daten laden =====
files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json")))
assert files, f"Keine JSON-Dateien in {INPUT_DIR} gefunden."

texts, y, metas = [], [], []
for fp in files:
    with open(fp, "r", encoding="utf-8") as f:
        items = json.load(f)
    for it in items:
    # robust: Eintrag ohne sentiment wird übersprungen
        if "sentiment" not in it:
            print(f" WARNUNG: Eintrag ohne 'sentiment' übersprungen -> {it}")
            continue

        text = it["text"].strip()
        lab  = normalize_label(it["sentiment"])
        tgt  = it.get("target")

        if USE_TARGET_HINT and tgt:
            text = f"[TARGET={tgt}] {text}"

        texts.append(text)
        y.append(label2id[lab])

        metas.append({"index": it.get("index"), "target": tgt, "src": os.path.basename(fp)})

X_tr, X_va, y_tr, y_va = train_test_split(
    texts, y, test_size=VAL_SIZE, stratify=y, random_state=SEED
)

train_ds = Dataset.from_dict({"text": X_tr, "label": y_tr})
val_ds   = Dataset.from_dict({"text": X_va, "label": y_va})
ds = DatasetDict({"train": train_ds, "validation": val_ds})

# ===== Tokenizer =====
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
def tok(batch): return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=160)
ds = ds.map(tok, batched=True)
ds = ds.remove_columns([c for c in ds["train"].column_names if c not in ["input_ids","attention_mask","label"]])
ds.set_format("torch")

# ===== Modell + gewichtete Loss =====
model = AutoModelForSequenceClassification.from_pretrained(
    BASE_MODEL, num_labels=len(labels), id2label=id2label, label2id=label2id
)

class_weights = compute_class_weight("balanced", classes=np.arange(len(labels)), y=np.array(y_tr))
class_weights = torch.tensor(class_weights, dtype=torch.float)

class WeightedCELoss(nn.Module):
    def __init__(self, weight: torch.Tensor):
        super().__init__()
        # als Buffer registrieren, damit es Teil des Moduls ist
        self.register_buffer("w", weight)

    def forward(self, logits, labels):
        # Gewicht + Labels auf dasselbe Device wie logits bringen
        return F.cross_entropy(
            logits,
            labels.to(logits.device),
            weight=self.w.to(logits.device)
        )

weighted_loss = WeightedCELoss(class_weights)

class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        model_inputs = {k: v for k, v in inputs.items() if k != "labels"}
        outputs = model(**model_inputs)
        logits = outputs.get("logits")
        loss = weighted_loss(logits, labels)   # labels-Device wird im Loss gefixt
        return (loss, outputs) if return_outputs else loss



# ===== Metriken =====
metric_acc = evaluate.load("accuracy")
metric_f1  = evaluate.load("f1")
def compute_metrics(eval_pred):
    logits, labels_np = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": metric_acc.compute(predictions=preds, references=labels_np)["accuracy"],
        "f1_macro": metric_f1.compute(predictions=preds, references=labels_np, average="macro")["f1"]
    }

# ===== Trainings-Args (auf 2070 Super abgestimmt) =====
args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="steps",
    eval_steps=50,
    save_steps=50,
    save_total_limit=2,
    logging_steps=25,
    learning_rate=2e-5,
    per_device_train_batch_size=16,   # 2070S: passt mit FP16
    per_device_eval_batch_size=32,
    gradient_accumulation_steps=1,
    num_train_epochs=10,
    weight_decay=0.01,
    warmup_ratio=0.06,
    lr_scheduler_type="linear",
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    fp16=torch.cuda.is_available(),
    seed=SEED,
    report_to="none"
)

trainer = WeightedTrainer(
    model=model,
    args=args,
    train_dataset=ds["train"],
    eval_dataset=ds["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3, early_stopping_threshold=5e-4)]
)

trainer.train()
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(" Fertig. Bestes Modell gespeichert unter:", OUTPUT_DIR)
