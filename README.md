# Sentimentanalyse der ZDF-Sportstudio Spielzusammenfassungen des FC Bayern München

Projekt der Vorlesung **Natural Language Processing** an der **DHBW Ravensburg**.

Dieses Projekt untersucht, ob Spielzusammenfassungen des ZDF-„sportstudio fußball“ eine messbare Parteilichkeit zugunsten oder zulasten des FC Bayern München aufweisen. Grundlage ist ein selbst erstellter Datensatz aus rund **70 YouTube-Videos** (ausschließlich Bundesliga) der Spielzeiten **2023/24** und **2024/25**.

---

## ⚽️ Inhalt

### Datenerhebung
- Extraktion automatischer YouTube-Untertitel  
- Anreicherung der Metadaten (Gegner, Kommentator, Spielort, Ergebnis)

### Datenaufbereitung
- LLM-basierte Korrektur der Transkripte  
- Strukturierte Extraktion von Spielinformationen  
- Segmentierung in inhaltlich geschlossene Kommentar-Einheiten

### Modellierung
- Klassifikation der Segmente (Bayern / Gegner / Neutral)  
- Anreicherung mit Spielphase und Spielstand  
- Sentimentanalyse inklusive Fine-Tuning

### Datensatz
- Ca. **7 800** final segmentierte und annotierte Aussagen  
- JSON-Strukturen pro Spiel  
- Zusammengeführte tabellarische Form für die Analyse

---

## 🥅 Ziel

Untersuchung möglicher positiver, neutraler oder negativer Kommentierung des FC Bayern in ZDF-Spielzusammenfassungen.  
Zusätzlich Analyse potenzieller Muster über Spiele, Gegner oder Kommentatoren.

---

## 📄 Datensatzstruktur
- Bereinigte und normalisierte Transkripte  
- Segmentierte JSON-Dateien  
- Analyse-Notebook und Skripte  
- Dokumentation aller Verarbeitungsschritte

---

## Lizenz

Dieses Projekt entstand im Rahmen einer Studienleistung.  
Die Verwendung der bereitgestellten Daten ist ausschließlich zu Forschungs- und Lehrzwecken gestattet.

### Datenquellen
Bei der Nutzung und Weiterverarbeitung sind die folgenden externen Quellen zu beachten:

- **FBref (Bayern-Statistiken)**  
    https://fbref.com/en/squads/054efa67/2023-2024/Bayern-Munich-Stats

    https://fbref.com/en/squads/054efa67/2024-2025/Bayern-Munich-Stats
  

- **Wikipedia: Kader der Bundesliga**  
  https://de.wikipedia.org/wiki/Kader_der_deutschen_Fußball-Bundesliga_2023/24

  https://de.wikipedia.org/wiki/Kader_der_deutschen_Fußball-Bundesliga_2024/25

- **YouTube – ZDF sportstudio fußball**  
  https://www.youtube.com/@sportstudiofussball  
  (Quelle der automatisch generierten Videotranskripte)

Alle Rechte an den oben genannten Inhalten verbleiben bei den jeweiligen Urhebern.