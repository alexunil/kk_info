"""Solr client for carrier data search"""
import os
from typing import List, Dict, Optional, Tuple
import pysolr
from collections import defaultdict


class SolrCarrierClient:
    """Client for searching carrier data in Solr"""

    def __init__(self, solr_url: str = None):
        self.solr_url = solr_url or os.getenv('SOLR_URL', 'http://localhost:8983/solr/kk-info')
        self.solr = pysolr.Solr(self.solr_url, always_commit=True, timeout=10)

    def ping(self) -> bool:
        """Check if Solr is available"""
        try:
            self.solr.ping()
            return True
        except:
            return False

    def get_total_count(self) -> int:
        """Get total number of carriers in index"""
        try:
            results = self.solr.search('*:*', rows=0)
            return results.hits
        except:
            return 0

    def search_carriers(self, query: str = '*:*', filters: Dict[str, str] = None,
                       start: int = 0, rows: int = 100) -> Tuple[int, List[Dict]]:
        """
        Search carriers with optional filters.
        Returns (total, results)
        """
        fq = []
        if filters:
            for field, value in filters.items():
                if value:
                    fq.append(f'{field}:"{value}"')

        try:
            results = self.solr.search(query, start=start, rows=rows, fq=fq)
            return results.hits, list(results)
        except Exception as e:
            print(f"Solr search error: {e}")
            return 0, []

    def search_by_name(self, name: str, start: int = 0, rows: int = 100) -> Tuple[int, List[Dict]]:
        """Search carriers by name"""
        query = f'name:*{name}* OR name_exact:"{name}"'
        return self.search_carriers(query, start=start, rows=rows)

    def search_by_city(self, city: str, start: int = 0, rows: int = 100) -> Tuple[int, List[Dict]]:
        """Search carriers by city"""
        return self.search_carriers(f'city:*{city}*', start=start, rows=rows)

    def search_by_ik(self, ik: str, start: int = 0, rows: int = 100) -> Tuple[int, List[Dict]]:
        """Search carriers by IK number (partial match)"""
        return self.search_carriers(f'ik_number:*{ik}*', start=start, rows=rows)

    def get_by_ik(self, ik_number: str) -> Optional[Dict]:
        """Get a specific carrier by exact IK number"""
        try:
            results = self.solr.search(f'ik_number:"{ik_number}"', rows=1)
            if results:
                return list(results)[0]
            return None
        except:
            return None

    def search_multi(self, name: str = None, city: str = None, ik: str = None,
                    start: int = 0, rows: int = 100) -> Tuple[int, List[Dict]]:
        """Search with multiple criteria"""
        queries = []
        if name:
            queries.append(f'name:*{name}*')
        if city:
            queries.append(f'city:*{city}*')
        if ik:
            queries.append(f'ik_number:*{ik}*')

        if not queries:
            return self.search_carriers('*:*', start=start, rows=rows)

        query = ' AND '.join(queries)
        return self.search_carriers(query, start=start, rows=rows)

    def get_acceptance_centers_stats(self) -> List[Dict]:
        """Get statistics for acceptance centers"""
        try:
            # Use faceting to get stats
            results = self.solr.search('*:*', rows=0, facet='on',
                                      **{'facet.field': 'acceptance_center_ik',
                                         'facet.limit': -1,
                                         'facet.mincount': 1})

            facets = results.facets.get('facet_fields', {}).get('acceptance_center_ik', [])

            # Parse facets (they come as [value1, count1, value2, count2, ...])
            centers = []
            for i in range(0, len(facets), 2):
                ik = facets[i]
                count = facets[i + 1]

                if not ik:
                    continue

                # Get example carrier names
                center_carriers = self.solr.search(f'acceptance_center_ik:"{ik}"', rows=10)
                carrier_names = [c.get('name', '') for c in center_carriers]

                centers.append({
                    'acceptance_center_ik': ik,
                    'carrier_count': count,
                    'carrier_names': carrier_names[:10]
                })

            return centers
        except Exception as e:
            print(f"Error getting acceptance center stats: {e}")
            return []

    def suggest(self, query: str, count: int = 10) -> List[str]:
        """Get autocomplete suggestions for carrier names"""
        try:
            # Use Solr's suggest component
            params = {
                'suggest': 'true',
                'suggest.q': query,
                'suggest.count': count,
                'suggest.dictionary': 'carrier_suggest'
            }

            response = self.solr._send_request('get', 'suggest', params=params)

            suggestions = []
            suggest_data = response.get('suggest', {}).get('carrier_suggest', {}).get(query, {})

            if 'suggestions' in suggest_data:
                for item in suggest_data['suggestions']:
                    suggestions.append(item.get('term', ''))

            return suggestions
        except Exception as e:
            print(f"Suggest error: {e}")
            # Fallback: simple wildcard search
            try:
                results = self.solr.search(f'name:{query}*', rows=count, fl='name')
                return list(set([r.get('name', '') for r in results if r.get('name')]))
            except:
                return []


# Global client instance
_solr_client = None


def get_solr_client() -> SolrCarrierClient:
    """Get or create Solr client instance"""
    global _solr_client
    if _solr_client is None:
        _solr_client = SolrCarrierClient()
    return _solr_client
