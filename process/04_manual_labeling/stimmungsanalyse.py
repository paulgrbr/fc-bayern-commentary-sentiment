import json

# Datei mit den Sätzen laden
with open("saetze3.json", "r", encoding="utf-8") as f:
    saetze = json.load(f)

print("Bitte gib zu jedem Satz eine Stimmung ein:")
print("O = Neutral, P = Positiv, N = Negativ\n")

# Zuordnung von Eingabe zu ausgeschriebenem Wert
stimmungs_map = {
    "O": "Neutral",
    "P": "Positiv",
    "N": "Negativ"
}

for satz in saetze:
    print(f"Satz {satz['index']}: {satz['text']}")
    
    # Stimmung abfragen
    while True:
        eingabe = input("Stimmung (O/P/N): ").strip().upper()
        if eingabe in ["O", "P", "N"]:
            stimmung = stimmungs_map[eingabe]
            break
        else:
            print("Ungültige Eingabe. Bitte O, P oder N eingeben.")
    
    satz["sentiment"] = stimmung

    # Wenn Positiv oder Negativ → nach Bezug fragen
    if eingabe in ["P", "N"]:
        while True:
            bezug = input("Bezug (B = Bayern, G = Gegner): ").strip().upper()
            if bezug in ["B", "G"]:
                satz["target"] = "Bayern" if bezug == "B" else "Gegner"
                break
            else:
                print("Ungültige Eingabe. Bitte B oder G eingeben.")
    else:
        satz["target"] = None

    print()  # Leerzeile für bessere Übersicht

# Ergebnis speichern
with open("saetze_mit_stimmung3.json", "w", encoding="utf-8") as f:
    json.dump(saetze, f, ensure_ascii=False, indent=2)

print("\nFertig! Die Datei 'saetze_mit_stimmung3.json' wurde erstellt.")
print("Vorschau der ersten Einträge:")
print(json.dumps(saetze[:5], ensure_ascii=False, indent=2))
