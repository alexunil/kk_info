# Krankenkassen Info API

FastAPI-Anwendung zum Parsen von EDIFACT-Dateien (.ke0) mit deutschen Krankenkassendaten und Bereitstellung über eine REST-API.

## Features

- ✅ Import von EDIFACT .ke0-Dateien mit der `pydifact`-Bibliothek
- ✅ SQLite-Datenbank zur Speicherung der Krankenkassendaten
- ✅ REST-API mit FastAPI
- ✅ Suche nach Krankenkassen (Name, Stadt, IK-Nummer)
- ✅ Abfrage von Datenannahmestellen und zugeordneten Krankenkassen
- ✅ Automatische API-Dokumentation (OpenAPI/Swagger)

## Installation

```bash
# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

## Verwendung

### 1. EDIFACT-Datei importieren

```bash
# Erste Import (mit --clear um bestehende Daten zu löschen)
python import_edifact.py EK05Q126.ke0 --clear

# Weitere Importe (ohne --clear zum Hinzufügen)
python import_edifact.py weitere_datei.ke0
```

### 2. API starten

```bash
# Development-Server mit Auto-Reload
./run_dev.sh

# Oder manuell:
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Die API ist dann verfügbar unter:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. API-Endpunkte

- `GET /` - API-Übersicht
- `GET /health` - Health Check mit Statistiken
- `GET /carriers` - Liste aller Krankenkassen (mit Pagination)
- `GET /carriers/{ik_number}` - Krankenkasse nach IK-Nummer
- `GET /carriers/search/?name=...&city=...&ik=...` - Krankenkassen suchen
- `GET /acceptance-centers` - Übersicht Datenannahmestellen
- `GET /acceptance-centers/{ik}` - Krankenkassen einer Datenannahmestelle
- **`POST /find-billing-center`** - 🆕 Finde Abrechnungsstelle für Krankenkasse (siehe API_BEISPIELE.md)

### Beispiele

```bash
# Alle Krankenkassen (erste 10)
curl "http://localhost:8000/carriers?limit=10"

# Nach Name suchen
curl "http://localhost:8000/carriers/search/?name=Techniker"

# Krankenkassen in Hamburg
curl "http://localhost:8000/carriers/search/?city=Hamburg"

# Spezifische Krankenkasse
curl "http://localhost:8000/carriers/100177504"

# Alle Datenannahmestellen
curl "http://localhost:8000/acceptance-centers"

# 🆕 NEU: Finde Abrechnungsstelle für Krankenkasse
curl -X POST http://localhost:8000/find-billing-center \
  -H "Content-Type: application/json" \
  -d '{"krankenkasse": "Techniker"}'

# Ergebnis: DAVASO GmbH (Leipzig) + alle 28 IK-Nummern
```

**Siehe API_BEISPIELE.md für weitere Beispiele!**

## Projektstruktur

```
kk_info/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI-Anwendung
│   ├── database.py          # SQLAlchemy Modelle
│   └── edifact_parser.py    # EDIFACT-Parser mit pydifact
├── venv/                    # Virtual Environment
├── import_edifact.py        # Import-Script
├── run_dev.sh               # Development-Server starten
├── test_api.sh              # API-Tests
├── requirements.txt         # Python Dependencies
├── kk_info.db              # SQLite-Datenbank (nach Import)
├── EK05Q126.ke0            # Beispiel-Datei
└── README.md
```

---

## EDIFACT-Dateiformat (.ke0)

1. Die Dateistruktur (Segmente)
Eine EDIFACT-Datei besteht aus Segmenten, die durch ein Apostroph (') getrennt sind. Die Felder innerhalb eines Segments werden durch ein Pluszeichen (+) getrennt.

Ein typischer Datensatz für eine Krankenkasse in einer .KE0-Datei sieht etwa so aus (stark vereinfacht): UNB+UNOC:3+123456789+... (Nutzdaten-Header) UNH+1+KOTG:04:000:00' (Beginn der Nachricht "Kostenträgerdaten") ... NAD+SENDER... IDE+1+... (Identifikation der Kasse) VKG+... (Verknüpfung zur Abrechnungsstelle)

2. Die wichtigsten Segmente für deine Suche
Wenn du wissen willst, wer (z. B. Davaso) für wen (z. B. TK) abrechnet, musst du auf folgende Segmente achten:

NAD (Name and Address): Enthält das IK (Institutionskennzeichen) der Krankenkasse, den Namen und die Anschrift.

IDE (Identification): Hier wird spezifiziert, um welche Art von Stelle es sich handelt (z. B. "01" für Krankenkasse).

VKG (Verknüpfungssegment): Das ist das entscheidende Segment für dich. Es verknüpft die Krankenkasse mit ihrer Datenannahmestelle.

In diesem Segment steht ein Code für den Verarbeitungszweck (z. B. Abrechnung von Heilmitteln).

Dahinter folgt das IK der Datenannahmestelle. Wenn dort das IK von Davaso steht (z. B. 261401064), weißt du, dass dorthin die Daten geschickt werden müssen.

FKT (Funktion): Gibt an, ob der Datensatz neu ist, geändert wurde oder gelöscht werden soll.

3. Wo findet man die offizielle Dokumentation?
Die genauen Feldbelegungen ändern sich manchmal leicht. Die "Bibel" dafür ist das Dokument: "Technischer Leitfaden zum Datenaustausch mit sonstigen Leistungserbringern" (Anlage 1 zum Vertrag über den Datenaustausch).

Dort ist in Kapitel "Struktur der Kostenträgerdatei" exakt definiert:

Welches Feld an welcher Stelle steht (z. B. Stelle 1-3: Segmentkennung).

Welche Codelisten gelten (z. B. 01 = Kasse, 02 = Pflegekasse).

Die logische Verknüpfung der IKs.

4. Technischer Tipp für die Verarbeitung
Da EDIFACT für Menschen schwer lesbar ist, nutzen Entwickler meistens:

EDI-Parser: Es gibt Bibliotheken (für Python, Java, C#), die EDI-Dateien in JSON oder XML umwandeln.

IK-Suche: Wenn du nicht selbst programmieren willst, kannst du die IKs auch manuell in der IK-Datenbank der ARGE IK prüfen, um herauszufinden, welcher Firmenname hinter der Nummer im VKG-Segment steckt.
