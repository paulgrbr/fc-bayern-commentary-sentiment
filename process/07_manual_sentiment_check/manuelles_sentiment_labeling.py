#!/usr/bin/env python3
"""
Manuelle Sentiment-Überprüfung für zufällig ausgewählte Sätze aus einer CSV.

Nutzung:
    python manuelles_sentiment_labeling.py kommentare_annotiert.csv kommentare_annotiert.csv \
        --exclude_json Selbst_belabelt/saetze_mit_stimmung.json \
        Selbst_belabelt/saetze_mit_stimmung2.json Selbst_belabelt/saetze_mit_stimmung3.json

Wichtige Eigenschaften:
- Sätze aus den JSON-Dateien (Trainingsdaten) werden ausgeschlossen.
- Bereits manuell gelabelte Zeilen (Spalte `sentiment__manual`) werden komplett
  übersprungen.
- Du definierst ein Ziel (`--target_total`, z.B. 700). Das Skript zieht pro Lauf
  nur noch so viele neue Sätze, wie fehlen.
- Du gibst 'p' (positiv), 'o' (neutral), 'n' (negativ) ein.
- Nach jeder Annotation wird automatisch in die Output-CSV gespeichert.
"""

import argparse
import sys
import json
import pandas as pd
from pathlib import Path


def parse_args():
    """Kommandozeilenargumente parsen."""
    parser = argparse.ArgumentParser(
        description="Manuelle Sentiment-Überprüfung für zufällige Sätze in einer CSV."
    )
    parser.add_argument(
        "input_csv",
        help="Pfad zur Eingabedatei (CSV)"
    )
    parser.add_argument(
        "output_csv",
        help="Pfad zur Ausgabedatei (CSV) mit zusätzlicher Spalte für manuelles Sentiment"
    )
    parser.add_argument(
        "--target_total",
        type=int,
        default=700,
        help="Ziel-Gesamtanzahl manuell gelabelter Sätze (Standard: 700)"
    )
    parser.add_argument(
        "--max_per_run",
        type=int,
        default=700,
        help="Maximale Anzahl neu zu labelnder Sätze pro Lauf (Standard: 700)"
    )
    parser.add_argument(
        "--random_state",
        type=int,
        default=42,
        help="Zufalls-Seed für Reproduzierbarkeit (Standard: 42)"
    )
    parser.add_argument(
        "--manual_col",
        type=str,
        default="sentiment__manual",
        help="Name der Spalte für das manuelle Sentiment (Standard: 'sentiment__manual')"
    )
    parser.add_argument(
        "--exclude_json",
        nargs="*",
        default=[],
        help=(
            "Liste von JSON-Dateien mit Sätzen, die NICHT in der Stichprobe "
            "vorkommen dürfen (z.B. Trainingsdaten)."
        )
    )
    return parser.parse_args()


def load_excluded_texts(json_paths):
    """
    Lädt aus einer Liste von JSON-Dateien alle 'text'-Felder in ein Set.

    Erwartetes JSON-Format: Liste von Objekten mit mindestens dem Schlüssel 'text', z.B.:

    [
      {"index": 1, "text": "Satz ...", "sentiment": "Positiv", "target": "Bayern"},
      ...
    ]
    """
    excluded = set()

    for path in json_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warnung: Konnte JSON-Datei '{path}' nicht laden: {e}")
            continue

        if not isinstance(data, list):
            print(f"Warnung: JSON-Datei '{path}' hat kein Listenformat, überspringe.")
            continue

        for entry in data:
            if isinstance(entry, dict) and "text" in entry:
                txt = entry["text"]
                if isinstance(txt, str):
                    excluded.add(txt)

    print(f"Insgesamt {len(excluded)} unterschiedliche Texte zum Ausschließen geladen.")
    return excluded


def main():
    args = parse_args()

    input_path = Path(args.input_csv)

    # CSV einlesen
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"Fehler beim Einlesen der CSV-Datei: {e}")
        sys.exit(1)

    # Prüfen, ob die wichtigsten Spalten existieren
    required_cols = ["text", "kontext"]
    for col in required_cols:
        if col not in df.columns:
            print(f"Fehlende Spalte in der CSV: '{col}'")
            sys.exit(1)

    # JSON-Dateien mit zu exkludierenden Sätzen laden
    excluded_texts = set()
    if args.exclude_json:
        excluded_texts = load_excluded_texts(args.exclude_json)

        if excluded_texts:
            original_len = len(df)
            df = df[~df["text"].isin(excluded_texts)].copy()
            filtered_len = len(df)
            removed = original_len - filtered_len
            print(
                f"{removed} Zeilen aufgrund von Ausschluss-Texten entfernt "
                f"({filtered_len} Zeilen verbleiben)."
            )
        else:
            print("Hinweis: Keine gültigen Ausschluss-Texte geladen, es wurde nichts gefiltert.")

    # Liste der Sentiment-Spalten, die angezeigt werden sollen
    sentiment_cols = [
        "sentiment__fine_tuned_german_sentiment",
        "sentiment__xlm-roberta-base",
        "sentiment__german-sentiment-bert",
        "sentiment__german-news-sentiment-bert",
    ]
    sentiment_cols = [c for c in sentiment_cols if c in df.columns]

    if not sentiment_cols:
        print("Warnung: Keine der erwarteten Sentiment-Spalten wurde gefunden.")
        print("Das Skript läuft weiter, zeigt dann aber nur Text & Kontext an.")

    # Spalte für manuelles Sentiment initialisieren (falls noch nicht vorhanden)
    if args.manual_col not in df.columns:
        df[args.manual_col] = pd.NA

    # *** WICHTIG: Fortschritt über sentiment__manual verfolgen ***

    # Anzahl bereits manuell gelabelter Zeilen
    current_labeled = df[args.manual_col].notna().sum()
    print(f"Aktuell bereits manuell gelabelte Sätze: {current_labeled}")

    # Noch fehlende Anzahl bis zum Ziel
    remaining_to_label = max(0, args.target_total - current_labeled)

    if remaining_to_label == 0:
        print(f"Ziel von {args.target_total} gelabelten Sätzen ist bereits erreicht 🎉")
        sys.exit(0)

    print(f"Noch zu labeln bis zum Ziel: {remaining_to_label}")

    # Nur ungelabelte Zeilen werden überhaupt in Betracht gezogen
    unlabeled_mask = df[args.manual_col].isna()
    unlabeled_df = df[unlabeled_mask].copy()

    n_unlabeled = len(unlabeled_df)
    if n_unlabeled == 0:
        print("Es gibt keine ungelabelten Zeilen mehr. Nichts zu tun.")
        sys.exit(0)

    # Wie viele sollen wir in diesem Lauf wirklich ziehen?
    # 1. Nicht mehr als noch bis zum Ziel fehlt
    # 2. Nicht mehr als `max_per_run`
    # 3. Nicht mehr als tatsächlich ungelabelt vorhanden
    n_samples = min(remaining_to_label, args.max_per_run, n_unlabeled)
    print(f"In diesem Lauf werden {n_samples} neue Sätze zur Annotation gezogen.")

    sampled_df = unlabeled_df.sample(n=n_samples, random_state=args.random_state)

    print("\nStarte manuelle Sentiment-Überprüfung.")
    print("Gib ein: p = positiv, o = neutral, n = negativ, q = abbrechen.\n")

    newly_labeled = 0

    # Über alle zufällig ausgewählten, ungelabelten Zeilen iterieren
    for i, (idx, row) in enumerate(sampled_df.iterrows(), start=1):
        print("=" * 80)
        print(f"Satz {i} von {n_samples} (Original-Index: {idx})")
        print("-" * 80)
        print(f"TEXT:\n{row['text']}\n")
        print(f"KONTEXT:\n{row.get('kontext', '')}\n")

        # Automatische Sentiments anzeigen (falls vorhanden)
        if sentiment_cols:
            print("Automatische Sentiments:")
            for col in sentiment_cols:
                print(f"  {col}: {row.get(col, '')}")
            print()

        # Eingabe-Schleife, bis eine gültige Eingabe vorliegt
        while True:
            user_input = input("Deine Bewertung (p/o/n, q = abbrechen): ").strip().lower()

            if user_input in ("p", "o", "n"):
                manual_label = user_input  # alternativ Mapping auf 'positiv', 'neutral', 'negativ'
                df.at[idx, args.manual_col] = manual_label
                newly_labeled += 1
                break
            elif user_input == "q":
                print("Abbruch durch Benutzer. Bisherige Annotationen werden gespeichert.")
                try:
                    df.to_csv(args.output_csv, index=False)
                    print(f"Zwischenergebnis gespeichert in: {args.output_csv}")
                except Exception as e:
                    print(f"Fehler beim Speichern der CSV-Datei: {e}")
                sys.exit(0)
            else:
                print("Ungültige Eingabe. Bitte 'p', 'o', 'n' oder 'q' eingeben.")

        # Nach jeder Annotation automatisch speichern
        try:
            df.to_csv(args.output_csv, index=False)
        except Exception as e:
            print(f"Warnung: Konnte nach Satz {i} nicht speichern: {e}")

    print("\nLauf beendet.")
    print(f"In diesem Lauf neu gelabelt: {newly_labeled}")
    total_now = current_labeled + newly_labeled
    print(f"Insgesamt jetzt manuell gelabelt: {total_now} von Ziel {args.target_total}.")
    print(f"Aktuelle Datei gespeichert in: {args.output_csv}")


if __name__ == "__main__":
    main()
