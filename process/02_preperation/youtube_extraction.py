import os
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATEI = "raw_data.xlsx"
TEAM = "FC Bayern München"
MODEL = "gpt-4o-mini"

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY fehlt in .env")

client = OpenAI(api_key=API_KEY)


def extract_from_text(text: str, team: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {
            "heim_auswaerts": "Unbekannt",
            "gegner": "Unbekannt",
            "schiedsrichter": None,
            "kommentator": None,
            "tore_bayern": "Unbekannt",
            "tore_gegner": "Unbekannt",
        }

    system = (
        "Du extrahierst ausschließlich aus dem gegebenen Beschreibungstext "
        "Informationen zum Fußballspiel. "
        "Antwortformat: reines JSON ohne Erklärtexte. "
        "Wenn unbekannt: 'Unbekannt' oder null. "
        "Heim/Auswärts immer relativ zum Bezugs-Team bestimmen. "
        "Zähle die Tore final (Endergebnis), nicht die Reihenfolge."
    )

    user = f"""
            Bezugs-Team: {team}

            Beschreibung:
            \"\"\"{text}\"\"\" 

            Gib genau folgende Felder als JSON zurück:
            {{
            "heim_auswaerts": "Heim" | "Auswärts" | "Unbekannt",
            "gegner": "STRING",
            "schiedsrichter": "STRING oder null",
            "kommentator": "STRING oder null",
            "tore_bayern": "ZAHL oder Unbekannt",
            "tore_gegner": "ZAHL oder Unbekannt"
            }}
            """

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
    )

    content = resp.choices[0].message.content

    try:
        return json.loads(content)
    except Exception:
        try:
            json_str = content[content.index("{"): content.rindex("}") + 1]
            return json.loads(json_str)
        except Exception:
            return {
                "heim_auswaerts": "Unbekannt",
                "gegner": "Unbekannt",
                "schiedsrichter": None,
                "kommentator": None,
                "tore_bayern": "Unbekannt",
                "tore_gegner": "Unbekannt",
            }


df = pd.read_excel(DATEI)

for col in [
    "Heim/Auswärts",
    "Gegner",
    "Schiedsrichter",
    "Kommentator",
    "Tore Bayern",
    "Tore Gegner",
]:
    if col not in df.columns:
        df[col] = None

for idx, row in df.iterrows():
    beschr = str(row.get("Beschreibung", "") or "")
    result = extract_from_text(beschr, TEAM)

    df.at[idx, "Heim/Auswärts"] = result.get("heim_auswaerts")
    df.at[idx, "Gegner"] = result.get("gegner")
    df.at[idx, "Schiedsrichter"] = result.get("schiedsrichter")
    df.at[idx, "Kommentator"] = result.get("kommentator")
    df.at[idx, "Tore Bayern"] = result.get("tore_bayern")
    df.at[idx, "Tore Gegner"] = result.get("tore_gegner")

df.to_excel(DATEI, index=False)
print("Fertig aktualisiert.")