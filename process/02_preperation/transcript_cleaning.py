import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATEI = "raw_data.xlsx"
MODEL = "gpt-4o"
TRANSCRIPT_COL = "ZDF Transkript"
OUTPUT_COL = "Clean Transcript"

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY fehlt in .env")

client = OpenAI(api_key=API_KEY)

with open("kader_23.txt", "r", encoding="utf-8") as f:
    kader = f.read()

SYSTEM_PROMPT = (
    "Du bekommst ein auto-generiertes YouTube-Transkript einer Bundesliga-Zusammenfassung. "
    "Bereinige es (Lesbarkeit, Rechtschreibung, Format), aber ändere den Inhalt nicht. "
    "Nutze zur Korrektur fehlerhafter Spielernamen folgende Kaderliste:\n\n"
    f"{kader}\n\n"
    "Gib ausschließlich das bereinigte Transkript zurück. Keine Überschrift, kein Kommentar.\n\n"
    "Hier ist außerdem die Roh-Videobeschreibung:\n"
)


def analyze(transcript: str, beschreibung: str) -> str:
    transcript = (transcript or "").strip()
    beschreibung = (beschreibung or "").strip()

    if not transcript:
        return "Kein Transkript vorhanden."

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript + "\n\n" + beschreibung}
        ],
        temperature=0.1
    )

    return resp.choices[0].message.content.strip()


df = pd.read_excel(DATEI)

if OUTPUT_COL not in df.columns:
    df[OUTPUT_COL] = None

for idx, row in df.iterrows():
    transcript = row.get(TRANSCRIPT_COL, "")
    beschreibung = row.get("Beschreibung", "")

    try:
        result = analyze(transcript, beschreibung)
    except Exception as e:
        result = f"Fehler: {e}"

    df.at[idx, OUTPUT_COL] = result

df.to_excel(DATEI, index=False)
print("Fertig.")