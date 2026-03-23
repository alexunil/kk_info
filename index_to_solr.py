#!/usr/bin/env python3
"""Index all carrier data from SQLite to Solr"""
import sys
import os
import argparse
from datetime import datetime
import pysolr

from app.database import SessionLocal, Carrier


def get_final_billing_center(carrier, db, cache={}):
    """
    Get final billing center name (cached for performance).
    Returns tuple of (ik, name)
    """
    if carrier.ik_number in cache:
        return cache[carrier.ik_number]

    visited = set([carrier.ik_number])
    current_ik = carrier.acceptance_center_ik

    while current_ik and current_ik not in visited:
        visited.add(current_ik)
        next_center = db.query(Carrier).filter(Carrier.ik_number == current_ik).first()

        if next_center and next_center.acceptance_center_ik:
            current_ik = next_center.acceptance_center_ik
        else:
            # Final center found
            result = (current_ik, next_center.name if next_center else None)
            cache[carrier.ik_number] = result
            return result

    result = (current_ik, None)
    cache[carrier.ik_number] = result
    return result


def index_carriers_to_solr(solr_url: str, clear_index: bool = False, batch_size: int = 100):
    """Index all carriers from SQLite to Solr"""

    # Connect to Solr
    solr = pysolr.Solr(solr_url, always_commit=True, timeout=10)

    # Test connection
    try:
        solr.ping()
        print(f"✅ Connected to Solr at {solr_url}")
    except Exception as e:
        print(f"❌ Failed to connect to Solr: {e}")
        return False

    # Clear index if requested
    if clear_index:
        print("Clearing Solr index...")
        solr.delete(q='*:*')
        print("✅ Index cleared")

    # Get carriers from SQLite
    db = SessionLocal()
    try:
        carriers = db.query(Carrier).all()
        total = len(carriers)
        print(f"\n📊 Found {total} carriers in SQLite database")

        # Prepare documents for Solr
        documents = []
        billing_cache = {}

        for i, carrier in enumerate(carriers, 1):
            # Get final billing center
            final_ik, final_name = get_final_billing_center(carrier, db, billing_cache)

            # Create Solr document
            doc = {
                'id': carrier.ik_number,  # Use IK as unique ID
                'ik_number': carrier.ik_number,
                'name': carrier.name,
                'name_exact': carrier.name,
                'carrier_type': carrier.carrier_type or '',
                'bkk_code': carrier.bkk_code or '',
                'function_code': carrier.function_code or '',
                'acceptance_center_ik': carrier.acceptance_center_ik or '',
                'acceptance_center_name': final_name or '',
                'processing_code': carrier.processing_code or '',
                'postal_code': carrier.postal_code or '',
                'city': carrier.city or '',
                'street': carrier.street or '',
                'address_type': carrier.address_type or '',
                'message_number': carrier.message_number or '',
                'popularity': 1,  # Can be adjusted based on usage
            }

            # Add dates if available
            if carrier.valid_from:
                doc['valid_from'] = carrier.valid_from.isoformat() + 'Z'
            if carrier.created_at:
                doc['created_at'] = carrier.created_at.isoformat() + 'Z'
            if carrier.updated_at:
                doc['updated_at'] = carrier.updated_at.isoformat() + 'Z'

            documents.append(doc)

            # Batch index
            if len(documents) >= batch_size:
                solr.add(documents)
                print(f"  Indexed {i}/{total} carriers...")
                documents = []

        # Index remaining documents
        if documents:
            solr.add(documents)

        print(f"\n✅ Successfully indexed {total} carriers to Solr")

        # Build suggestions
        print("\n🔨 Building suggestion dictionary...")
        try:
            solr._send_request('get', 'suggest?suggest.build=true')
            print("✅ Suggestion dictionary built")
        except Exception as e:
            print(f"⚠️  Warning: Could not build suggestions: {e}")

        return True

    except Exception as e:
        print(f"\n❌ Error indexing to Solr: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Index carrier data from SQLite to Solr'
    )
    parser.add_argument(
        '--solr-url',
        default=os.getenv('SOLR_URL', 'http://localhost:8983/solr/kk-info'),
        help='Solr URL (default: http://localhost:8983/solr/kk-info)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear Solr index before indexing'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for indexing (default: 100)'
    )

    args = parser.parse_args()

    print("="*70)
    print("📇 Krankenkassen Data Indexer - SQLite → Solr")
    print("="*70)

    success = index_carriers_to_solr(
        solr_url=args.solr_url,
        clear_index=args.clear,
        batch_size=args.batch_size
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
