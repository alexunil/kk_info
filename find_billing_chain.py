#!/usr/bin/env python3
"""Find complete billing chain for a health insurance carrier by name"""
import sys
import argparse
from app.database import SessionLocal, Carrier


def find_billing_chain(search_name: str):
    """Find and display the complete billing chain for a carrier"""
    db = SessionLocal()

    try:
        # Suche nach Krankenkasse
        carriers = db.query(Carrier).filter(
            Carrier.name.ilike(f'%{search_name}%')
        ).all()

        if not carriers:
            print(f"❌ Keine Krankenkasse gefunden für: '{search_name}'")
            return

        print(f"🔍 Gefunden: {len(carriers)} Einträge für '{search_name}'\n")
        print("=" * 70)

        for idx, carrier in enumerate(carriers, 1):
            print(f"\n{idx}. {carrier.name}")
            print(f"   IK-Nummer: {carrier.ik_number}")
            print(f"   Stadt: {carrier.city or 'N/A'}")
            if carrier.street:
                print(f"   Adresse: {carrier.street}, {carrier.postal_code} {carrier.city}")

            # Verfolge die Abrechnungskette
            print(f"\n   📊 Abrechnungskette:")
            print(f"   └─> START: {carrier.name} (IK: {carrier.ik_number})")

            current_ik = carrier.acceptance_center_ik
            level = 1
            visited = set([carrier.ik_number])  # Verhindere Endlosschleifen

            while current_ik and current_ik not in visited:
                visited.add(current_ik)

                # Finde die nächste Stufe
                next_center = db.query(Carrier).filter(
                    Carrier.ik_number == current_ik
                ).first()

                indent = "       " + "   " * level

                if next_center:
                    print(f"{indent}└─> {next_center.name} (IK: {current_ik})")
                    print(f"{indent}    Stadt: {next_center.city or 'N/A'}")

                    # Gibt es eine weitere Stufe?
                    if next_center.acceptance_center_ik:
                        current_ik = next_center.acceptance_center_ik
                        level += 1
                    else:
                        print(f"{indent}    ✅ ENDPUNKT: Führt eigene Abrechnung durch")
                        break
                else:
                    # Datenannahmestelle nicht in DB
                    print(f"{indent}└─> Datenannahmestelle IK: {current_ik}")
                    print(f"{indent}    ⚠️  Details nicht in Datenbank")
                    break

            if not carrier.acceptance_center_ik:
                print(f"       └─> ✅ ENDPUNKT: Führt eigene Abrechnung durch")

            print()
            print("-" * 70)

        # Zusammenfassung
        if len(carriers) > 1:
            print(f"\n💡 Tipp: Es gibt {len(carriers)} verschiedene Einträge.")
            print("   Dies können regionale Niederlassungen oder historische")
            print("   Einträge sein. Die Abrechnungskette kann unterschiedlich sein.")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Finde die vollständige Abrechnungskette für eine Krankenkasse',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s "Techniker"
  %(prog)s "DAK"
  %(prog)s "Barmer"
  %(prog)s "AOK Bayern"
        """
    )
    parser.add_argument(
        'name',
        help='Name oder Teil des Namens der Krankenkasse'
    )

    args = parser.parse_args()
    find_billing_chain(args.name)


if __name__ == '__main__':
    main()
