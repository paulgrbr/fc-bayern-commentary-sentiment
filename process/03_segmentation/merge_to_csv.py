import json
from pathlib import Path
import pandas as pd
from pandas import json_normalize

DATA_DIR = Path("mit_zuordnung")
OUTPUT_CSV = "alle_saetze_23-25.csv"


def load_one_json(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    transkript = (data.get("content") or {}).get("transkript", [])
    df = json_normalize(transkript)

    meta = {f"meta.{k}": v for k, v in (data.get("meta") or {}).items()}
    ergebnis = {f"ergebnis.{k}": v for k, v in (data.get("ergebnis") or {}).items()}
    offizielle = {f"offizielle.{k}": v for k, v in (data.get("offizielle") or {}).items()}
    all_meta = {**meta, **ergebnis, **offizielle}

    for k, v in all_meta.items():
        df[k] = v

    df["source_file"] = path.name
    return df


files = sorted(DATA_DIR.glob("*.json"))
if not files:
    raise FileNotFoundError(f"Keine JSON-Dateien in {DATA_DIR} gefunden.")

frames = []
for p in files:
    try:
        frames.append(load_one_json(p))
    except Exception as e:
        print(f"Übersprungen: {p.name} ({e})")

big = pd.concat(frames, ignore_index=True)

meta_prefixes = ("meta.", "ergebnis.", "offizielle.")
cols_transkript = [
    c for c in big.columns if not c.startswith(meta_prefixes) and c != "source_file"
]
cols_meta = [c for c in big.columns if c.startswith(meta_prefixes)]
big = big[cols_transkript + cols_meta + ["source_file"]]

if "meta.ballbesitz_bayern" in big.columns:
    big["meta.ballbesitz_bayern"] = pd.to_numeric(
        big["meta.ballbesitz_bayern"], errors="coerce"
    )

print(big.head())
print(f"Zeilen gesamt: {len(big):,}")

big.to_csv(OUTPUT_CSV, index=False)