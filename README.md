# Sentimentanalyse der ZDF-Sportstudio Spielzusammenfassungen des FC Bayern München

Projekt der Vorlesung **Natural Language Processing** an der **DHBW Ravensburg**.

Dieses Projekt untersucht, ob Spielzusammenfassungen des ZDF-„sportstudio fußball“ eine messbare Parteilichkeit zugunsten oder zulasten des FC Bayern München aufweisen. Grundlage ist ein selbst erstellter Datensatz aus rund **70 YouTube-Videos** der Spielzeiten **2023/24** und **2024/25**.

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

## ℹ️ Lizenz
Dieses Projekt entstand im Rahmen einer Studienleistung. Nutzung der bereitgestellten Daten nur zu Forschungs- und Lehrzwecken.