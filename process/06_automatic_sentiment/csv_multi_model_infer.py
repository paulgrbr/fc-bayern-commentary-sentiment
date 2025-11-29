import os, re, argparse
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==== Modelle hier eintragen: lokale Fine-Tunes ODER HF-Model-IDs ====
MODELS = [
    "./fine_tuned_german_sentiment",                    # dein bestes lokales Modell
    "./runs_sentiment/xlm-roberta-base",              # dein lokales Fine-Tune (falls trainiert)
    "oliverguhr/german-sentiment-bert",               # HF: fertig feingetunt (3 Klassen)
    "mdraw/german-news-sentiment-bert",               # HF: fertig feingetunt (3 Klassen)
]

USE_TARGET_HINT = True
ADD_CONFIDENCE = True             # optional: zusätzlich <spalte>__conf anhängen
MAX_LEN = 160
BATCH = 64

device = "cuda" if torch.cuda.is_available() else "cpu"


# ---------- Utility ----------
def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)

def resolve_target(gegner: str | None, kontext: str | None) -> str | None:
    k = (kontext or "").strip().lower()
    g = (gegner or "").strip().lower()
    if any(x in k for x in ["fc bayern", "bayern münchen", "bayern m\u00fcnchen", "fcb", "rekordmeister", "bayern"]):
        return "Bayern"
    if g and (g in k or k in g or k == g):
        return "Gegner"
    if any(x in k for x in [
        "werder","bremen","borussia","dortmund","leverkusen","köln","koeln","freiburg","augsburg",
        "stuttgart","gladbach","bochum","leipzig","union","hoffenheim","wolfsburg","mainz",
        "heidenheim","darmstadt"
    ]):
        if "bayern" not in k:
            return "Gegner"
    return None

def apply_hint(text: str, target: str | None) -> str:
    if USE_TARGET_HINT and target:
        return f"[TARGET={target}] {text}"
    return text

def get_label_mapping_from_config(model) -> list[str]:
    """
    Versucht, aus model.config.id2label eine saubere Reihenfolge/Benennung zu bauen.
    Ziel: ['Negativ','Neutral','Positiv'] zurückgeben, passend zu den IDs.
    Fällt bei Unklarheit auf einfache Heuristik zurück.
    """
    cfg = model.config
    if hasattr(cfg, "id2label") and isinstance(cfg.id2label, dict) and len(cfg.id2label) >= 3:
        # sortiere nach ID und mappe nach deutschem Schema
        id2label = [cfg.id2label[i] for i in sorted(cfg.id2label.keys())]
        norm = [str(x).strip().lower() for x in id2label]
        mapped = []
        for n in norm:
            if "neg" in n: mapped.append("Negativ")
            elif "neu" in n: mapped.append("Neutral")
            elif "pos" in n or "posi" in n: mapped.append("Positiv")
            else:
                mapped.append(n.capitalize())
        # Safety: falls keine klaren 3 Klassen → Standard
        if set(mapped) >= {"Negativ","Neutral","Positiv"}:
            return mapped
    # Default (deine Trainingsreihenfolge)
    return ["Negativ","Neutral","Positiv"]


# ---------- Inferenz pro Modell ----------
def predict_with_model(texts: list[str], model_id_or_dir: str):
    tok = AutoTokenizer.from_pretrained(model_id_or_dir)
    mdl = AutoModelForSequenceClassification.from_pretrained(model_id_or_dir).to(device).eval()

    # Sicherstellen, dass das Modell 3 Klassen hat
    num_labels = getattr(mdl.config, "num_labels", None)
    if num_labels is None or num_labels < 3:
        raise ValueError(f"Modell {model_id_or_dir} scheint nicht für 3-Klassen-Sentiment feingetunt zu sein (num_labels={num_labels}).")

    label_order = get_label_mapping_from_config(mdl)  # z. B. ['Negativ','Neutral','Positiv']

    preds, confs = [], []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i+BATCH]
        enc = tok(batch, truncation=True, padding=True, max_length=MAX_LEN, return_tensors="pt")
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            logits = mdl(**enc).logits
        probs = torch.softmax(logits, dim=-1).cpu().numpy()   # [N, num_labels]
        ids = probs.argmax(axis=1)
        preds.extend([label_order[j] for j in ids])
        confs.extend(probs.max(axis=1))
    return preds, confs


# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Anhängen von Sentiment-Spalten (mehrere Modelle) an CSV")
    ap.add_argument("--in_csv", required=True, help="Eingabe-CSV (Komma-separiert)")
    ap.add_argument("--out_csv", default="sentiment_annotated.csv", help="Ausgabe-CSV")
    args = ap.parse_args()

    df = pd.read_csv(args.in_csv)

    # Texte vorbereiten (inkl. Target-Hint)
    prepped = []
    for _, row in df.iterrows():
        text = str(row["text"])
        kontext = row.get("kontext", None)
        gegner = row.get("meta.gegner", None)
        target = resolve_target(gegner, kontext)
        prepped.append(apply_hint(text, target))

    # Für jedes Modell predicten und Spalten anhängen
    for model_dir in MODELS:
        col_base = slug(os.path.basename(model_dir) or model_dir)
        col_pred = f"sentiment__{col_base}"
        col_conf = f"{col_pred}__conf"

        print(f"→ Modell: {model_dir}")
        preds, confs = predict_with_model(prepped, model_dir)
        df[col_pred] = preds
        if ADD_CONFIDENCE:
            df[col_conf] = np.round(confs, 4)

    df.to_csv(args.out_csv, index=False)
    print(f" Fertig. Datei geschrieben: {args.out_csv}")

if __name__ == "__main__":
    main()
