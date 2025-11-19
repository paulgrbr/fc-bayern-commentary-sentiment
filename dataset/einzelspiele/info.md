# README – Kurzbeschreibung der Variablen

## meta → Allgemeine Spieldaten

- **saison** → Saison (z. B. „23/24“)
- **spieltag** → Spieltagnummer
- **heim_auswaerts** → Perspektive des FC Bayern („Heim“ / „Auswärts“)
- **gegner** → Name des Gegners
- **tabelle** → Tabellenplatz des FC Bayern

## ergebnis → Endstand

- **bayern** → Tore FC Bayern
- **gegner** → Tore des Gegners

## offizielle → Offizielle Personen

- **schiedsrichter** → Spielleiter
- **kommentator** → TV-Kommentator ZDF

## content.transkript[] → Einzelne Sätze des Spielberichts

- **index** → Laufende Nummer
- **text** → Originalsatz (Aussage)
- **kontext** → Betroffenes Team („FC Bayern München“, Gegner oder „Neutral“)
- **klassifikation** → Zusatzinfos
  - **tore_bayern** → Tore Bayern bis hierhin
  - **tore_gegner** → Tore Gegner bis hierhin
  - **phase** → Spielabschnitt
    - `0` = Vorbericht
    - `1` = 1. Halbzeit
    - `2` = 2. Halbzeit
    - `3` = Nachbericht

https://fbref.com/en/squads/054efa67/2023-2024/matchlogs/c20/possession/Bayern-Munich-Match-Logs-Bundesliga
