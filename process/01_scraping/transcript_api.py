import pandas as pd
import requests

# Excel laden
datei = "raw_data.xlsx"
df = pd.read_excel(datei)

for index, row in df.iterrows():
    url = row["URL"]

    api = "https://transcriptapi.com/api/v2/youtube/transcript"
    params = {
        "video_url": url,
        "send_metadata": "true",
        "format": "json",
        "include_timestamp": "false"
    }
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer sk_KMVXVjGKnSY049EvgW0aJ5wd_62h2gifNX77wFeDm-c"
    }

    r = requests.get(api, params=params, headers=headers)

    if r.status_code != 200:
        df.at[index, "ZDF Transkript"] = "Fehler"
        continue

    data = r.json()
    text = " ".join(i["text"] for i in data["transcript"])
    df.at[index, "ZDF Transkript"] = text

# zurück in Originaldatei speichern
df.to_excel(datei, index=False)

print("Fertig aktualisiert!")
