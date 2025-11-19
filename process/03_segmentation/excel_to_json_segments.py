import os
import re
import json
import time
import hashlib
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# Konfiguration
EXCEL_DATEI = "data/23-25_working.xlsx"
AUSGABE_ORDNER = "einzelne_spiele"
MODEL = "gpt-4o"

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY fehlt in .env")

client = OpenAI(api_key=API_KEY)

os.makedirs(AUSGABE_ORDNER, exist_ok=True)

df = pd.read_excel(EXCEL_DATEI, sheet_name=0)


def normalize_text(text: str) -> str:
    text = re.sub(r'["\[\],]', "", text)
    text = re.sub(r"\s+", "", text)
    return text


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ask_openai_as_sentences(content: str, max_retries: int = 5) -> list[str]:
    system_prompt = (
        "Du teilst einen deutschen Kommentartext in inhaltlich zusammenhängende Aussagen "
        "für eine Sentimentanalyse auf.\n\n"
        "Regeln:\n"
        "- Maximal 3 Sätze pro Aussage, wenn die Sätze direkt zusammengehören (z.B. Aktion + Auflösung).\n"
        "- Trennen bei neuem Fokus (anderes Team/Spieler/Schiedsrichter/Publikum), neuer Aktion, "
        "neuer Bewertung oder historischem Einschub.\n"
        "- Nicht trennen, wenn ein Satz die direkte Auflösung/Klarstellung zur vorherigen Aktion ist.\n"
        "- Keine Inhalte entfernen oder umformulieren. Der rekonstruierte Text muss exakt der Eingabe entsprechen.\n"
        "- Punkte, Zeilenumbrüche oder Ordinalzahlen markieren nicht automatisch einen Schnitt.\n\n"
        "Format: Gib ausschließlich ein gültiges JSON-Array von Strings zurück, ohne weitere Texte."
    )

    user_prompt = f'Text:\n"""{content}"""'

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            answer = (resp.choices[0].message.content or "").strip()
            answer = answer.replace("```json", "").replace("```", "")

            try:
                parsed = json.loads(answer)
            except Exception:
                m = re.search(r"\[.*\]", answer, re.DOTALL)
                if not m:
                    raise ValueError("Keine JSON-Array-Struktur gefunden.")
                parsed = json.loads(m.group(0))

            if not isinstance(parsed, list):
                raise ValueError("Antwort ist kein JSON-Array.")

            original_norm = normalize_text(content)
            reconstructed_norm = normalize_text("".join(parsed))

            if len(original_norm) != len(reconstructed_norm):
                raise ValueError("Textverlust (Längenunterschied).")

            if hash_text(original_norm) != hash_text(reconstructed_norm):
                raise ValueError("Text wurde verändert (Hash-Mismatch).")

            print("Check OK")
            return parsed

        except Exception as e:
            print(f"Fehler bei Versuch {attempt}/{max_retries}: {e}")
            time.sleep(attempt * 2)

    raise RuntimeError("ask_openai_as_sentences() nach allen Versuchen fehlgeschlagen.")


for _, row in df.iterrows():
    raw_transkript = str(row.get("Transkript", "") or "").strip()
    if not raw_transkript:
        continue

    saetze = ask_openai_as_sentences(raw_transkript)

    sentences_struct = [{"index": i, "text": s} for i, s in enumerate(saetze)]

    daten = {
        "meta": {
            "saison": row.get("Saison"),
            "spieltag": row.get("Spieltag"),
            "heim_auswaerts": row.get("Heim/Auswärts"),
            "gegner": row.get("Gegner"),
            "tabelle": row.get("Tabelle"),
        },
        "ergebnis": {
            "bayern": row.get("Tore Bayern"),
            "gegner": row.get("Tore Gegner"),
        },
        "offizielle": {
            "schiedsrichter": row.get("Schiedsrichter"),
            "kommentator": row.get("Kommentator"),
        },
        "content": {
            "transkript": sentences_struct,
        },
    }

    saison_str = str(row.get("Saison", "")).replace("/", "-")
    spieltag_str = str(row.get("Spieltag", ""))
    gegner_str = str(row.get("Gegner", "")).lower().replace(" ", "_")

    dateiname = f"{saison_str}_S{spieltag_str}_{gegner_str}.json"

    pfad = os.path.join(AUSGABE_ORDNER, dateiname)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)