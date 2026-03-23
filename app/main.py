"""FastAPI application for health insurance carrier data with Solr"""
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.solr_client import get_solr_client
from app.database import get_db, Carrier

# Create database tables on startup (still needed for imports)
from app.database import create_tables
create_tables()

app = FastAPI(
    title="Krankenkassen Info API (Solr)",
    description="API für deutsche Krankenkassendaten - powered by Apache Solr",
    version="2.0.0"
)


# Pydantic models
class CarrierSolrResponse(BaseModel):
    """Response model for a single carrier from Solr"""
    ik_number: str
    name: str
    carrier_type: Optional[str] = ""
    bkk_code: Optional[str] = ""
    function_code: Optional[str] = ""
    acceptance_center_ik: Optional[str] = ""
    acceptance_center_name: Optional[str] = ""
    processing_code: Optional[str] = ""
    postal_code: Optional[str] = ""
    city: Optional[str] = ""
    street: Optional[str] = ""


class CarrierListResponse(BaseModel):
    """Response model for carrier list"""
    total: int
    carriers: List[CarrierSolrResponse]


class AcceptanceCenterStats(BaseModel):
    """Statistics for an acceptance center"""
    acceptance_center_ik: str
    carrier_count: int
    carrier_names: List[str] = Field(max_length=10)


class BillingCenterRequest(BaseModel):
    """Request model for finding billing center"""
    krankenkasse: str = Field(..., min_length=2, description="Name der Krankenkasse")


class BillingCenterInfo(BaseModel):
    """Information about a billing center"""
    name: str
    ik: str
    stadt: Optional[str] = None
    adresse: Optional[str] = None
    anzahl_niederlassungen: int


class BillingCenterResponse(BaseModel):
    """Response model for billing center lookup"""
    success: bool
    krankenkasse: str
    eindeutig: bool
    anzahl_ik_nummern: int
    ik_nummern: List[str]
    abrechnungsstellen: List[BillingCenterInfo]
    hinweis: Optional[str] = None


class SuggestResponse(BaseModel):
    """Response for autocomplete suggestions"""
    query: str
    suggestions: List[str]


# Helper functions
def solr_doc_to_carrier(doc: dict) -> CarrierSolrResponse:
    """Convert Solr document to CarrierResponse"""
    return CarrierSolrResponse(
        ik_number=doc.get('ik_number', ''),
        name=doc.get('name', ''),
        carrier_type=doc.get('carrier_type', ''),
        bkk_code=doc.get('bkk_code', ''),
        function_code=doc.get('function_code', ''),
        acceptance_center_ik=doc.get('acceptance_center_ik', ''),
        acceptance_center_name=doc.get('acceptance_center_name', ''),
        processing_code=doc.get('processing_code', ''),
        postal_code=doc.get('postal_code', ''),
        city=doc.get('city', ''),
        street=doc.get('street', '')
    )


# Endpoints
@app.get("/")
def root():
    """API root endpoint"""
    solr = get_solr_client()
    solr_status = "connected" if solr.ping() else "disconnected"

    return {
        "message": "Krankenkassen Info API (Solr-powered)",
        "version": "2.0.0",
        "search_engine": "Apache Solr",
        "solr_status": solr_status,
        "endpoints": {
            "/carriers": "List all carriers",
            "/carriers/{ik_number}": "Get carrier by IK number",
            "/carriers/search": "Search carriers by name, city or IK",
            "/acceptance-centers": "List acceptance centers with stats",
            "/acceptance-centers/{ik}": "Get carriers by acceptance center",
            "/find-billing-center": "Find billing center (GET/POST)",
            "/suggest": "Autocomplete suggestions (NEW!)",
            "/health": "Health check"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    solr = get_solr_client()

    try:
        solr_available = solr.ping()
        carrier_count = solr.get_total_count() if solr_available else 0
    except:
        solr_available = False
        carrier_count = 0

    return {
        "status": "healthy" if solr_available else "degraded",
        "search_engine": "solr",
        "solr": "connected" if solr_available else "disconnected",
        "carrier_count": carrier_count
    }


@app.get("/carriers", response_model=CarrierListResponse)
def get_carriers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get list of all carriers with pagination (from Solr)"""
    solr = get_solr_client()
    total, results = solr.search_carriers('*:*', start=skip, rows=limit)

    carriers = [solr_doc_to_carrier(doc) for doc in results]

    return CarrierListResponse(
        total=total,
        carriers=carriers
    )


@app.get("/carriers/{ik_number}", response_model=CarrierSolrResponse)
def get_carrier(ik_number: str):
    """Get a specific carrier by IK number (from Solr)"""
    solr = get_solr_client()
    doc = solr.get_by_ik(ik_number)

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Carrier with IK {ik_number} not found"
        )

    return solr_doc_to_carrier(doc)


@app.get("/carriers/search/", response_model=CarrierListResponse)
def search_carriers(
    name: Optional[str] = Query(None, min_length=2),
    city: Optional[str] = Query(None, min_length=2),
    ik: Optional[str] = Query(None, min_length=3),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Search carriers by name, city, or IK number (from Solr)"""
    solr = get_solr_client()

    total, results = solr.search_multi(
        name=name,
        city=city,
        ik=ik,
        start=skip,
        rows=limit
    )

    carriers = [solr_doc_to_carrier(doc) for doc in results]

    return CarrierListResponse(
        total=total,
        carriers=carriers
    )


@app.get("/acceptance-centers", response_model=List[AcceptanceCenterStats])
def get_acceptance_centers():
    """Get list of all acceptance centers with statistics (from Solr)"""
    solr = get_solr_client()
    return solr.get_acceptance_centers_stats()


@app.get("/acceptance-centers/{ik}", response_model=CarrierListResponse)
def get_carriers_by_acceptance_center(ik: str):
    """Get all carriers that use a specific acceptance center (from Solr)"""
    solr = get_solr_client()

    total, results = solr.search_carriers(
        query='*:*',
        filters={'acceptance_center_ik': ik}
    )

    if total == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No carriers found for acceptance center IK {ik}"
        )

    carriers = [solr_doc_to_carrier(doc) for doc in results]

    return CarrierListResponse(
        total=total,
        carriers=carriers
    )


@app.get("/suggest", response_model=SuggestResponse)
def suggest_carriers(
    q: str = Query(..., min_length=1, description="Query string for autocomplete"),
    count: int = Query(10, ge=1, le=50, description="Number of suggestions")
):
    """
    Get autocomplete suggestions for carrier names.
    NEW endpoint for fast typeahead/autocomplete.
    """
    solr = get_solr_client()
    suggestions = solr.suggest(q, count=count)

    return SuggestResponse(
        query=q,
        suggestions=suggestions
    )


@app.get("/find-billing-center", response_model=BillingCenterResponse)
def find_billing_center_get(
    krankenkasse: str = Query(..., min_length=2, description="Name der Krankenkasse")
):
    """Find billing center for a health insurance (GET) - uses Solr"""
    return _find_billing_center_logic_solr(krankenkasse)


@app.post("/find-billing-center", response_model=BillingCenterResponse)
def find_billing_center_post(request: BillingCenterRequest):
    """Find billing center for a health insurance (POST) - uses Solr"""
    return _find_billing_center_logic_solr(request.krankenkasse)


def _find_billing_center_logic_solr(krankenkasse: str) -> BillingCenterResponse:
    """Find billing center using Solr (much faster than SQLite)"""
    solr = get_solr_client()

    # Search for carriers
    total, results = solr.search_by_name(krankenkasse, rows=1000)

    if total == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Keine Krankenkasse gefunden für: '{krankenkasse}'"
        )

    # Collect IK numbers
    all_ik_numbers = [doc.get('ik_number', '') for doc in results]

    # Group by acceptance center
    billing_centers = {}
    for doc in results:
        final_ik = doc.get('acceptance_center_ik', '')
        if final_ik and final_ik not in billing_centers:
            billing_centers[final_ik] = {
                'name': doc.get('acceptance_center_name', final_ik),
                'ik': final_ik,
                'stadt': '',  # Could be enhanced
                'adresse': '',
                'carrier_iks': []
            }
        if final_ik:
            billing_centers[final_ik]['carrier_iks'].append(doc.get('ik_number', ''))

    # Create response
    billing_center_infos = []
    for center_data in billing_centers.values():
        billing_center_infos.append(BillingCenterInfo(
            name=center_data['name'],
            ik=center_data['ik'],
            stadt=center_data.get('stadt'),
            adresse=center_data.get('adresse'),
            anzahl_niederlassungen=len(center_data['carrier_iks'])
        ))

    eindeutig = len(billing_centers) == 1
    hinweis = None

    if not eindeutig:
        hinweis = (
            f"Achtung: Diese Krankenkasse hat {len(billing_centers)} verschiedene "
            f"Abrechnungsstellen. Dies kann auf regionale Unterschiede oder "
            f"historische Fusionen hindeuten."
        )

    krankenkasse_name = results[0].get('name', krankenkasse) if results else krankenkasse

    return BillingCenterResponse(
        success=True,
        krankenkasse=krankenkasse_name,
        eindeutig=eindeutig,
        anzahl_ik_nummern=len(all_ik_numbers),
        ik_nummern=sorted(all_ik_numbers),
        abrechnungsstellen=billing_center_infos,
        hinweis=hinweis
    )
