import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY fehlt in .env")

client = OpenAI(api_key=API_KEY)

INPUT_DIR = Path("einzelne_spiele")
OUTPUT_DIR = Path("mit_zuordnung")

with open("scraping/kader_23.txt", "r", encoding="utf-8") as f:
    KADER = f.read()


def sorted_json_files_by_mtime(folder: Path):
    files = [p for p in folder.glob("23-24*.json") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def build_system_prompt(opponent: str) -> str:
    return (
        "Du bist ein Experte für deutsche Fußball-Kommentare.\n\n"
        "Aufgabe: Bestimme für jeden Satz aus einem Spielbericht, welches Team er betrifft.\n\n"
        "Erlaubte Antworten (exakt diese Schreibweise):\n"
        f"- FC Bayern München\n- {opponent}\n- Neutral\n\n"
        "Wenn Pronomen oder beschreibende Folgesätze vorkommen, übernimm das Team des vorherigen Satzes.\n"
        "Beispiele:\n"
        "  - 'Sané, 4. Minute, 1:0 Bayern.' → FC Bayern München\n"
        "  - 'Ein perfekt herausgespielter Treffer.' → FC Bayern München\n\n"
        "Kriterien:\n"
        "- Aktionen, Chancen, Tore → entsprechendes Team\n"
        "- Beschreibungen oder Kommentare direkt danach → selbes Team\n"
        "- Beide Teams erwähnt oder neutral → Neutral\n\n"
        "Bekannte Spielernamen zur Zuordnung:\n"
        f"{KADER}\n\n"
        "Antwortformat:\n"
        '[{"index": <Nummer>, "kontext": <Antwort>}]\n\n'
        "Nur das JSON-Array, keine Erklärungen oder Texte außerhalb davon."
    )


def get_model_response(messages):
    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            wait = 2 ** attempt
            print(f"API-Fehler (Versuch {attempt + 1}): {e} → warte {wait}s")
            time.sleep(wait)
    raise RuntimeError("Zu viele API-Fehler in Folge.")


def parse_and_validate_response(content, valid_labels):
    start, end = content.find("["), content.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"Antwort enthält kein JSON-Array:\n{content[:300]}")

    try:
        results = json.loads(content[start : end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"Fehler beim JSON-Parsing: {e}\nAntwort:\n{content[:400]}")

    invalid_entries = []
    for r in results:
        kontext = str(r.get("kontext", "")).strip()
        if kontext not in valid_labels:
            invalid_entries.append(r)

    return results, invalid_entries


def classify_file(in_path: Path, out_path: Path):
    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    transkript = data["content"]["transkript"]
    opponent = data["meta"]["gegner"]
    valid_labels = {"FC Bayern München", opponent, "Neutral"}

    print(f"\nDatei: {in_path.name} | Gegner: {opponent} | Sätze: {len(transkript)}")

    system_prompt = build_system_prompt(opponent)
    sentences_json = json.dumps(
        [{"index": t["index"], "text": t["text"]} for t in transkript],
        ensure_ascii=False,
    )

    user_prompt = (
        f"Hier sind alle Sätze aus dem Spielbericht gegen {opponent}. "
        "Analysiere sie und gib nur das JSON-Array zurück:\n\n"
        f"{sentences_json}"
    )

    attempt_counter = 1
    while True:
        print(f"Durchlauf {attempt_counter} ...")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = get_model_response(messages)
        results, invalid_entries = parse_and_validate_response(content, valid_labels)

        if invalid_entries:
            print(f"{len(invalid_entries)} ungültige Labels, wiederhole ...")
            for bad in invalid_entries:
                print(f"  Index {bad.get('index')}: '{bad.get('kontext')}'")
            attempt_counter += 1
            time.sleep(2)
        else:
            print("Alle Labels gültig.")
            break

    for r in results:
        idx = r["index"]
        team = str(r["kontext"]).strip()
        for t in transkript:
            if t["index"] == idx:
                t["kontext"] = team
                break
        print(f"{idx:>3}: {team}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Gespeichert: {out_path} (nach {attempt_counter} Durchläufen)")


def main():
    files = sorted_json_files_by_mtime(INPUT_DIR)
    if not files:
        print(f"Keine 23-24*.json in {INPUT_DIR.resolve()}")
        return

    print(f"Gefundene Dateien: {len(files)}")
    for path in files:
        classify_file(path, OUTPUT_DIR / path.name)


if __name__ == "__main__":
    main()