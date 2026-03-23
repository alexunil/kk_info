# API Beispiele - Abrechnungsstellen finden

## Endpoint: POST /find-billing-center

Finde die finale Abrechnungsstelle für eine Krankenkasse anhand des Namens.

## Request Format

```json
{
  "krankenkasse": "Techniker"
}
```

## Response Format

```json
{
  "success": true,
  "krankenkasse": "TECHNIKER KRANKENKASSE",
  "eindeutig": true,
  "anzahl_ik_nummern": 28,
  "ik_nummern": ["100177504", "100577508", ...],
  "abrechnungsstellen": [
    {
      "name": "DAVASO GmbH zuvor INTER-FORUM",
      "ik": "661430035",
      "stadt": "Leipzig",
      "adresse": "Gärtnerweg 12",
      "anzahl_niederlassungen": 27
    }
  ],
  "hinweis": null
}
```

## Verwendung mit curl

### Beispiel 1: Techniker Krankenkasse

```bash
curl -X POST http://localhost:8000/find-billing-center \
  -H "Content-Type: application/json" \
  -d '{"krankenkasse": "Techniker"}' | python3 -m json.tool
```

**Ergebnis:**
- Abrechnungsstelle: DAVASO GmbH (Leipzig)
- 28 IK-Nummern
- Eindeutig: ✅ Ja

### Beispiel 2: DAK

```bash
curl -X POST http://localhost:8000/find-billing-center \
  -H "Content-Type: application/json" \
  -d '{"krankenkasse": "DAK"}' | python3 -m json.tool
```

**Ergebnis:**
- Abrechnungsstelle: DAVASO GmbH (Leipzig)
- 36 IK-Nummern
- Eindeutig: ✅ Ja

### Beispiel 3: BARMER

```bash
curl -X POST http://localhost:8000/find-billing-center \
  -H "Content-Type: application/json" \
  -d '{"krankenkasse": "Barmer"}' | python3 -m json.tool
```

**Ergebnis:**
- Abrechnungsstelle: BARMER Abr. häusl. Krankenpflege (Schwäbisch Gmünd)
- 31 IK-Nummern
- Eindeutig: ✅ Ja

### Beispiel 4: AOK Bayern

```bash
curl -X POST http://localhost:8000/find-billing-center \
  -H "Content-Type: application/json" \
  -d '{"krankenkasse": "AOK Bayern"}' | python3 -m json.tool
```

**Ergebnis:**
- Abrechnungsstelle: DAV AOK Bayern - kubus IT (Bayreuth)
- 5 IK-Nummern
- Eindeutig: ✅ Ja

### Beispiel 5: Mercedes BKK

```bash
curl -X POST http://localhost:8000/find-billing-center \
  -H "Content-Type: application/json" \
  -d '{"krankenkasse": "Mercedes"}' | python3 -m json.tool
```

**Ergebnis:**
- Abrechnungsstelle: Abrechnungszentrum Emmendingen
- 2 IK-Nummern
- Eindeutig: ✅ Ja

## Spezialfall: Mehrdeutige Zuordnung

### Deutsche Betriebskrankenkasse (2 Abrechnungsstellen)

```bash
curl -X POST http://localhost:8000/find-billing-center \
  -H "Content-Type: application/json" \
  -d '{"krankenkasse": "Deutsche Betriebskrankenkasse"}' | python3 -m json.tool
```

**Ergebnis:**
- Abrechnungsstellen:
  1. BARMER Abr. (Schwäbisch Gmünd) - 10 Niederlassungen
  2. Abrechnungszentrum Emmendingen - 2 Niederlassungen
- 12 IK-Nummern
- Eindeutig: ❌ **Nein** (mit Warnhinweis!)

## Verwendung mit Python

```python
import requests

response = requests.post(
    'http://localhost:8000/find-billing-center',
    json={'krankenkasse': 'Techniker'}
)

data = response.json()

if data['success']:
    print(f"Krankenkasse: {data['krankenkasse']}")
    print(f"Anzahl IK-Nummern: {data['anzahl_ik_nummern']}")

    for center in data['abrechnungsstellen']:
        print(f"\nAbrechnungsstelle: {center['name']}")
        print(f"  IK: {center['ik']}")
        print(f"  Ort: {center['stadt']}")
        print(f"  Niederlassungen: {center['anzahl_niederlassungen']}")
```

## Fehlerbehandlung

### Krankenkasse nicht gefunden

```bash
curl -X POST http://localhost:8000/find-billing-center \
  -H "Content-Type: application/json" \
  -d '{"krankenkasse": "XYZ"}'
```

**Response:**
```json
{
  "detail": "Keine Krankenkasse gefunden für: 'XYZ'"
}
```

Status Code: **404**

## API starten

```bash
# Development Server
./run_dev.sh

# Oder manuell:
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Interaktive Dokumentation

Nach dem Start der API:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Dort kannst du die API interaktiv testen!
