#!/usr/bin/env python3
"""Import EDIFACT .ke0 files into the database"""
import sys
import argparse
from pathlib import Path

from app.edifact_parser import EdifactParser
from app.database import SessionLocal, create_tables, Carrier


def import_file(filepath: str, clear_existing: bool = False):
    """Import an EDIFACT .ke0 file into the database"""

    # Check if file exists
    file_path = Path(filepath)
    if not file_path.exists():
        print(f"Error: File {filepath} not found")
        return False

    # Create database tables if they don't exist
    create_tables()

    # Parse the EDIFACT file
    print(f"Parsing {filepath}...")
    parser = EdifactParser()
    carriers = parser.parse_file(filepath)
    print(f"Found {len(carriers)} carriers in file")

    # Import into database
    db = SessionLocal()
    try:
        # Clear existing data if requested
        if clear_existing:
            print("Clearing existing carriers from database...")
            db.query(Carrier).delete()
            db.commit()

        # Insert carriers
        print("Importing carriers into database...")
        imported = 0
        for carrier_data in carriers:
            carrier = Carrier(
                ik_number=carrier_data.ik_number,
                carrier_type=carrier_data.carrier_type,
                name=carrier_data.name,
                bkk_code=carrier_data.bkk_code,
                valid_from=carrier_data.valid_from,
                function_code=carrier_data.function_code,
                acceptance_center_ik=carrier_data.acceptance_center_ik,
                processing_code=carrier_data.processing_code,
                address_type=carrier_data.address_type,
                postal_code=carrier_data.postal_code,
                city=carrier_data.city,
                street=carrier_data.street,
                message_number=carrier_data.message_number
            )
            db.add(carrier)
            imported += 1

            if imported % 100 == 0:
                print(f"  Imported {imported} carriers...")

        db.commit()
        print(f"✓ Successfully imported {imported} carriers")

        # Show some statistics
        print("\nStatistics:")
        total = db.query(Carrier).count()
        print(f"  Total carriers in database: {total}")

        centers = db.query(Carrier.acceptance_center_ik)\
            .filter(Carrier.acceptance_center_ik.isnot(None))\
            .distinct()\
            .count()
        print(f"  Unique acceptance centers: {centers}")

        return True

    except Exception as e:
        print(f"Error importing data: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Import EDIFACT .ke0 files into the database"
    )
    parser.add_argument(
        'file',
        help='Path to the .ke0 EDIFACT file'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing data before import'
    )

    args = parser.parse_args()

    success = import_file(args.file, clear_existing=args.clear)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
