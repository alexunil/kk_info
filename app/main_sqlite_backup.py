"""FastAPI application for health insurance carrier data"""
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db, Carrier, create_tables

# Create database tables on startup
create_tables()

app = FastAPI(
    title="Krankenkassen Info API",
    description="API für deutsche Krankenkassendaten aus EDIFACT-Dateien",
    version="1.0.0"
)


# Pydantic models for API responses
class CarrierResponse(BaseModel):
    """Response model for a single carrier"""
    id: int
    ik_number: str
    name: str
    carrier_type: Optional[str] = None
    bkk_code: Optional[str] = None
    valid_from: Optional[datetime] = None
    function_code: Optional[str] = None
    acceptance_center_ik: Optional[str] = None
    processing_code: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None

    class Config:
        from_attributes = True


class CarrierListResponse(BaseModel):
    """Response model for carrier list"""
    total: int
    carriers: List[CarrierResponse]


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


def get_final_billing_center(carrier: Carrier, db: Session) -> Optional[str]:
    """
    Verfolge die Abrechnungskette bis zur finalen Stelle.
    Returns the IK of the final billing center.
    """
    visited = set([carrier.ik_number])
    current_ik = carrier.acceptance_center_ik

    while current_ik and current_ik not in visited:
        visited.add(current_ik)
        next_center = db.query(Carrier).filter(Carrier.ik_number == current_ik).first()

        if next_center and next_center.acceptance_center_ik:
            current_ik = next_center.acceptance_center_ik
        else:
            # Finale Stelle gefunden
            return current_ik

    return current_ik


@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "Krankenkassen Info API",
        "version": "1.0.0",
        "endpoints": {
            "/carriers": "List all carriers",
            "/carriers/{ik_number}": "Get carrier by IK number",
            "/carriers/search": "Search carriers by name or city",
            "/acceptance-centers": "List acceptance centers with stats",
            "/acceptance-centers/{ik}": "Get carriers by acceptance center",
            "/find-billing-center": "Find billing center for a health insurance (POST)"
        }
    }


@app.get("/carriers", response_model=CarrierListResponse)
def get_carriers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get list of all carriers with pagination"""
    total = db.query(Carrier).count()
    carriers = db.query(Carrier).offset(skip).limit(limit).all()

    return CarrierListResponse(
        total=total,
        carriers=carriers
    )


@app.get("/carriers/{ik_number}", response_model=CarrierResponse)
def get_carrier(ik_number: str, db: Session = Depends(get_db)):
    """Get a specific carrier by IK number"""
    carrier = db.query(Carrier).filter(Carrier.ik_number == ik_number).first()

    if not carrier:
        raise HTTPException(status_code=404, detail=f"Carrier with IK {ik_number} not found")

    return carrier


@app.get("/carriers/search/", response_model=CarrierListResponse)
def search_carriers(
    name: Optional[str] = Query(None, min_length=2),
    city: Optional[str] = Query(None, min_length=2),
    ik: Optional[str] = Query(None, min_length=3),
    db: Session = Depends(get_db)
):
    """Search carriers by name, city, or IK number"""
    query = db.query(Carrier)

    if name:
        query = query.filter(Carrier.name.ilike(f"%{name}%"))

    if city:
        query = query.filter(Carrier.city.ilike(f"%{city}%"))

    if ik:
        query = query.filter(Carrier.ik_number.like(f"%{ik}%"))

    carriers = query.all()

    return CarrierListResponse(
        total=len(carriers),
        carriers=carriers
    )


@app.get("/acceptance-centers", response_model=List[AcceptanceCenterStats])
def get_acceptance_centers(db: Session = Depends(get_db)):
    """Get list of all acceptance centers with statistics"""
    # Group by acceptance center IK
    carriers = db.query(Carrier).filter(Carrier.acceptance_center_ik.isnot(None)).all()

    centers = {}
    for carrier in carriers:
        ik = carrier.acceptance_center_ik
        if ik not in centers:
            centers[ik] = {
                'acceptance_center_ik': ik,
                'carrier_count': 0,
                'carrier_names': []
            }
        centers[ik]['carrier_count'] += 1
        if len(centers[ik]['carrier_names']) < 10:
            centers[ik]['carrier_names'].append(carrier.name)

    return list(centers.values())


@app.get("/acceptance-centers/{ik}", response_model=CarrierListResponse)
def get_carriers_by_acceptance_center(ik: str, db: Session = Depends(get_db)):
    """Get all carriers that use a specific acceptance center"""
    carriers = db.query(Carrier).filter(Carrier.acceptance_center_ik == ik).all()

    if not carriers:
        raise HTTPException(
            status_code=404,
            detail=f"No carriers found for acceptance center IK {ik}"
        )

    return CarrierListResponse(
        total=len(carriers),
        carriers=carriers
    )


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    carrier_count = db.query(Carrier).count()

    return {
        "status": "healthy",
        "database": "connected",
        "carrier_count": carrier_count
    }


def _find_billing_center_logic(krankenkasse: str, db: Session) -> BillingCenterResponse:
    """
    Interne Logik zum Finden der Abrechnungsstelle.
    Wird von GET und POST Endpunkten verwendet.
    """
    # Suche alle Einträge der Krankenkasse
    carriers = db.query(Carrier).filter(
        Carrier.name.ilike(f'%{krankenkasse}%')
    ).all()

    if not carriers:
        raise HTTPException(
            status_code=404,
            detail=f"Keine Krankenkasse gefunden für: '{krankenkasse}'"
        )

    # Sammle alle IK-Nummern
    all_ik_numbers = [c.ik_number for c in carriers]

    # Finde finale Abrechnungsstellen
    billing_centers = {}  # IK -> Liste von Carrier-IKs

    for carrier in carriers:
        final_ik = get_final_billing_center(carrier, db)
        if final_ik:
            if final_ik not in billing_centers:
                billing_centers[final_ik] = []
            billing_centers[final_ik].append(carrier.ik_number)

    # Erstelle Response-Objekte für Abrechnungsstellen
    billing_center_infos = []
    for final_ik, carrier_iks in billing_centers.items():
        # Hole Details der Abrechnungsstelle
        center = db.query(Carrier).filter(Carrier.ik_number == final_ik).first()

        if center:
            billing_center_infos.append(BillingCenterInfo(
                name=center.name,
                ik=center.ik_number,
                stadt=center.city,
                adresse=center.street,
                anzahl_niederlassungen=len(carrier_iks)
            ))
        else:
            # Abrechnungsstelle nicht in DB
            billing_center_infos.append(BillingCenterInfo(
                name="Unbekannt",
                ik=final_ik,
                stadt=None,
                adresse=None,
                anzahl_niederlassungen=len(carrier_iks)
            ))

    # Ist die Zuordnung eindeutig?
    eindeutig = len(billing_centers) == 1
    hinweis = None

    if not eindeutig:
        hinweis = (
            f"Achtung: Diese Krankenkasse hat {len(billing_centers)} verschiedene "
            f"Abrechnungsstellen. Dies kann auf regionale Unterschiede oder "
            f"historische Fusionen hindeuten."
        )

    # Nutze den ersten gefundenen Carrier-Namen als Standard
    krankenkasse_name = carriers[0].name

    return BillingCenterResponse(
        success=True,
        krankenkasse=krankenkasse_name,
        eindeutig=eindeutig,
        anzahl_ik_nummern=len(all_ik_numbers),
        ik_nummern=sorted(all_ik_numbers),
        abrechnungsstellen=billing_center_infos,
        hinweis=hinweis
    )


@app.get("/find-billing-center", response_model=BillingCenterResponse)
def find_billing_center_get(
    krankenkasse: str = Query(..., min_length=2, description="Name der Krankenkasse"),
    db: Session = Depends(get_db)
):
    """
    Finde die finale Abrechnungsstelle für eine Krankenkasse (GET).

    Beispiel: /find-billing-center?krankenkasse=Techniker
    """
    return _find_billing_center_logic(krankenkasse, db)


@app.post("/find-billing-center", response_model=BillingCenterResponse)
def find_billing_center_post(request: BillingCenterRequest, db: Session = Depends(get_db)):
    """
    Finde die finale Abrechnungsstelle für eine Krankenkasse (POST).

    Gibt zurück:
    - Name der finalen Abrechnungsstelle(n)
    - Alle IK-Nummern der Krankenkasse
    - Flag ob eindeutig (eine Stelle) oder mehrdeutig (mehrere Stellen)
    """
    return _find_billing_center_logic(request.krankenkasse, db)
