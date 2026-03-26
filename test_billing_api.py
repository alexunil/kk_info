#!/usr/bin/env python3
"""Test script for the new billing center API endpoint"""
from app.main import app
from fastapi.testclient import TestClient

# Create test client
client = TestClient(app)


def test_billing_center(krankenkasse: str):
    """Test the billing center endpoint"""
    print(f"\n{'='*70}")
    print(f"🔍 Suche Abrechnungsstelle für: {krankenkasse}")
    print('='*70)

    # Make API call
    response = client.post(
        "/find-billing-center",
        json={"krankenkasse": krankenkasse}
    )

    if response.status_code == 404:
        print(f"❌ Nicht gefunden: {response.json()['detail']}")
        return

    if response.status_code != 200:
        print(f"❌ Fehler: {response.status_code}")
        print(response.text)
        return

    # Parse response
    data = response.json()

    print(f"\n✅ Gefunden: {data['krankenkasse']}")
    print(f"📊 Anzahl IK-Nummern: {data['anzahl_ik_nummern']}")
    print(f"🎯 Eindeutig: {'Ja' if data['eindeutig'] else 'Nein'}")

    if data['hinweis']:
        print(f"\n⚠️  {data['hinweis']}")

    print("\n📍 Abrechnungsstelle(n):")
    for center in data['abrechnungsstellen']:
        print(f"\n  • {center['name']}")
        print(f"    IK: {center['ik']}")
        if center['stadt']:
            print(f"    Stadt: {center['stadt']}")
        if center['adresse']:
            print(f"    Adresse: {center['adresse']}")
        print(f"    Anzahl Niederlassungen: {center['anzahl_niederlassungen']}")

    print("\n📋 IK-Nummern (erste 10):")
    for ik in data['ik_nummern'][:10]:
        print(f"  - {ik}")
    if len(data['ik_nummern']) > 10:
        print(f"  ... und {len(data['ik_nummern']) - 10} weitere")


def main():
    """Run tests"""
    print("\n" + "="*70)
    print("🏥 Test: Abrechnungsstellen-API")
    print("="*70)

    # Test verschiedene Krankenkassen
    test_cases = [
        "Techniker",
        "DAK",
        "Barmer",
        "AOK Bayern",
        "Handelskrankenkasse",
        "Mercedes",
        "Deutsche Betriebskrankenkasse"  # Hat mehrere Abrechnungsstellen!
    ]

    for kasse in test_cases:
        test_billing_center(kasse)

    print("\n" + "="*70)
    print("✅ Tests abgeschlossen")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
