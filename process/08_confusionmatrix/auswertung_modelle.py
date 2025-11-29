#!/usr/bin/env python3
"""
Vergleicht manuelle Sentiment-Labels mit den Vorhersagen mehrerer Modelle.

Nutzung:
    python auswertung_modelle.py kommentare_annotiert.csv

Voraussetzungen:
- In der CSV gibt es eine Spalte mit manuellen Labels (Standard: 'sentiment__manual'),
  z.B. 'p' (positiv), 'o' (neutral), 'n' (negativ).
- Es gibt Modell-Spalten wie:
    - sentiment__fine_tuned_german_sentiment
    - sentiment__xlm-roberta-base
    - sentiment__german-sentiment-bert
    - sentiment__german-news-sentiment-bert
  (Namen kannst du unten in `model_cols` anpassen.)
"""

import argparse
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Vergleicht manuelle Sentiment-Labels mit Modellvorhersagen."
    )
    parser.add_argument(
        "input_csv",
        help="Pfad zur CSV-Datei mit manuellen und Modell-Sentiments"
    )
    parser.add_argument(
        "--manual_col",
        default="sentiment__manual",
        help="Spaltenname für das manuelle Label (Standard: 'sentiment__manual')"
    )
    return parser.parse_args()


def normalize_label(label: str):
    """
    Normalisiert ein Label (manuell ODER Modell) auf eines von:
    'pos' (positiv), 'neu' (neutral), 'neg' (negativ).

    Versucht dabei robust auf verschiedene Schreibweisen zu reagieren:
    - p / positiv / positive
    - o / neutral / neu
    - n / negativ / negative
    - 1 / 0 / -1 usw.

    Gibt None zurück, wenn nichts erkannt wird.
    """
    if label is None:
        return None

    s = str(label).strip().lower()

    # direkt Kürzel
    if s in {"p", "pos", "positiv", "positive", "1"}:
        return "pos"
    if s in {"o", "neu", "neutral", "0"}:
        return "neu"
    if s in {"n", "neg", "negativ", "negative", "-1"}:
        return "neg"

    # heuristisch über enthaltene Wörter
    if "pos" in s:
        return "pos"
    if "neu" in s or "neutral" in s:
        return "neu"
    if "neg" in s:
        return "neg"

    return None


def main():
    args = parse_args()

    # CSV laden
    df = pd.read_csv(args.input_csv)

    if args.manual_col not in df.columns:
        raise ValueError(f"Manuelle Spalte '{args.manual_col}' nicht in CSV gefunden.")

    # Nur Zeilen mit manueller Annotation verwenden
    df = df[df[args.manual_col].notna()].copy()
    n_manual = len(df)
    print(f"Anzahl Zeilen mit manuellem Label: {n_manual}")

    if n_manual == 0:
        print("Keine Zeilen mit manuellem Label vorhanden – Abbruch.")
        return

    # Manuelle Labels normalisieren
    df["manual_norm"] = df[args.manual_col].apply(normalize_label)
    df = df[df["manual_norm"].notna()].copy()
    n_manual_norm = len(df)
    print(f"Nach Normalisierung der manuellen Labels verbleiben {n_manual_norm} Zeilen.\n")

    # Modell-Spalten, die wir vergleichen wollen
    model_cols = [
        "sentiment__fine_tuned_german_sentiment",
        "sentiment__xlm-roberta-base",
        "sentiment__german-sentiment-bert",
        "sentiment__german-news-sentiment-bert",
    ]
    # nur Spalten verwenden, die es wirklich gibt
    model_cols = [c for c in model_cols if c in df.columns]

    if not model_cols:
        print("Keine der erwarteten Modell-Spalten gefunden – nichts zu vergleichen.")
        return

    results = []

    for col in model_cols:
        # Modell-Labels normalisieren
        norm_col = f"{col}__norm"
        df[norm_col] = df[col].apply(normalize_label)

        # Nur Zeilen, wo sowohl manuell als auch Modell ein gültiges Label haben
        mask_valid = df[norm_col].notna() & df["manual_norm"].notna()
        df_valid = df[mask_valid].copy()
        n_valid = len(df_valid)

        if n_valid == 0:
            print(f"Modell '{col}': Keine vergleichbaren Zeilen (alle Labels None).")
            continue

        # Korrektklassifizierung
        correct = (df_valid[norm_col] == df_valid["manual_norm"]).sum()
        accuracy = correct / n_valid

        results.append({
            "model": col,
            "n_valid": n_valid,
            "correct": correct,
            "accuracy": accuracy,
        })

        print(f"Modell: {col}")
        print(f"  Vergleichbare Zeilen: {n_valid}")
        print(f"  Korrekt:               {correct}")
        print(f"  Accuracy:              {accuracy:.3f}")

        # einfache "Konfusionsmatrix" ausgeben
        print("  Konfusionsmatrix (manuell -> Modell):")
        crosstab = pd.crosstab(df_valid["manual_norm"], df_valid[norm_col])
        print(crosstab, "\n")

    if not results:
        print("Es konnten keine sinnvollen Vergleiche berechnet werden.")
        return

    # Modelle nach Accuracy sortiert anzeigen
    print("\n=== Zusammenfassung (nach Accuracy sortiert) ===")
    results_sorted = sorted(results, key=lambda x: x["accuracy"], reverse=True)
    for r in results_sorted:
        print(
            f"{r['model']}: Accuracy {r['accuracy']:.3f} "
            f"({r['correct']}/{r['n_valid']} korrekt)"
        )

    best = results_sorted[0]
    print(
        f"\nBestes Modell auf diesen Daten: {best['model']} "
        f"mit Accuracy {best['accuracy']:.3f}"
    )


if __name__ == "__main__":
    main()
