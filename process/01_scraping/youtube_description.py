from pytubefix import YouTube
from urllib.parse import urlparse, parse_qs
import pandas as pd

def clean_youtube_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("Leere URL")

    parsed = urlparse(url)

    # youtu.be/VIDEOID
    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.lstrip("/")
    else:
        qs = parse_qs(parsed.query)
        video_id = qs.get("v", [None])[0]

    if not video_id:
        raise ValueError(f"Keine Video-ID gefunden in URL: {url}")

    return f"https://www.youtube.com/watch?v={video_id}"


df = pd.read_excel("raw_data.xlsx")

for idx, row in df.iterrows():
    raw_url = str(row.get("URL", "") or "").strip()
    if not raw_url:
        continue

    try:
        url = clean_youtube_url(raw_url)
        yt = YouTube(url)
        df.at[idx, "Beschreibung"] = f"Titel: {yt.title} Beschreibung: {yt.description}"
    except Exception as e:
        df.at[idx, "Beschreibung"] = f"Fehler: {e}"

df.to_excel("raw_data.xlsx", index=False)
print("Fertig.")