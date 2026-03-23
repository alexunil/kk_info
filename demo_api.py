#!/usr/bin/env python3
"""Demo script to show API functionality"""
import sys
import time
import urllib.request
import json


def api_call(endpoint):
    """Make API call and return JSON"""
    url = f"http://127.0.0.1:9000{endpoint}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error calling {endpoint}: {e}")
        return None


def main():
    """Run API demonstrations"""
    print("=" * 60)
    print("🏥 Krankenkassen Info API - Demo")
    print("=" * 60)

    # 1. Health Check
    print("\n1️⃣  Health Check")
    print("-" * 60)
    data = api_call("/health")
    if data:
        print(f"✅ Status: {data['status']}")
        print(f"📊 Datenbankverbindung: {data['database']}")
        print(f"🏥 Anzahl Krankenkassen: {data['carrier_count']}")

    # 2. First carriers
    print("\n2️⃣  Erste 5 Krankenkassen")
    print("-" * 60)
    data = api_call("/carriers?limit=5")
    if data:
        print(f"Total: {data['total']} Krankenkassen in der Datenbank\n")
        for c in data['carriers']:
            print(f"  • {c['name']}")
            print(f"    IK: {c['ik_number']}, Stadt: {c['city']}")
            print(f"    Datenannahmestelle-IK: {c['acceptance_center_ik']}\n")

    # 3. Search by name
    print("\n3️⃣  Suche nach 'Techniker'")
    print("-" * 60)
    data = api_call("/carriers/search/?name=Techniker")
    if data:
        print(f"Gefunden: {data['total']} Ergebnis(se)\n")
        for c in data['carriers']:
            print(f"  • {c['name']}")
            print(f"    IK: {c['ik_number']}, {c['city']}\n")

    # 4. Search by city
    print("\n4️⃣  Krankenkassen in Hamburg")
    print("-" * 60)
    data = api_call("/carriers/search/?city=Hamburg")
    if data:
        print(f"Gefunden: {data['total']} Krankenkassen\n")
        for c in data['carriers'][:5]:
            print(f"  • {c['name']}")
        if data['total'] > 5:
            print(f"  ... und {data['total']-5} weitere")

    # 5. Acceptance centers
    print("\n5️⃣  Datenannahmestellen")
    print("-" * 60)
    data = api_call("/acceptance-centers")
    if data:
        print(f"Total: {len(data)} Datenannahmestellen\n")
        # Sort by carrier count
        sorted_centers = sorted(data, key=lambda x: -x['carrier_count'])
        for center in sorted_centers[:5]:
            print(f"  • IK {center['acceptance_center_ik']}: {center['carrier_count']} Krankenkassen")
            examples = ', '.join(center['carrier_names'][:3])
            print(f"    Beispiele: {examples}\n")

    # 6. Specific acceptance center
    print("\n6️⃣  Krankenkassen für Datenannahmestelle 105830016")
    print("-" * 60)
    data = api_call("/acceptance-centers/105830016")
    if data:
        print(f"Total: {data['total']} Krankenkassen nutzen diese Stelle\n")
        for c in data['carriers'][:5]:
            print(f"  • {c['name']} ({c['city']})")
        if data['total'] > 5:
            print(f"  ... und {data['total']-5} weitere")

    # 7. Specific carrier
    print("\n7️⃣  Spezifische Krankenkasse (IK: 100177504)")
    print("-" * 60)
    data = api_call("/carriers/100177504")
    if data:
        print(f"Name: {data['name']}")
        print(f"IK: {data['ik_number']}")
        print(f"Stadt: {data['city']}, PLZ: {data['postal_code']}")
        if data['street']:
            print(f"Straße: {data['street']}")
        print(f"Datenannahmestelle-IK: {data['acceptance_center_ik']}")

    print("\n" + "=" * 60)
    print("✅ Demo abgeschlossen!")
    print("=" * 60)
    print("\n📚 Weitere Informationen:")
    print("  - Swagger UI: http://127.0.0.1:9000/docs")
    print("  - ReDoc: http://127.0.0.1:9000/redoc")
    print()


if __name__ == '__main__':
    main()
