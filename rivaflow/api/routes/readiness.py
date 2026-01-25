"""Readiness check-in endpoints."""
from fastapi import APIRouter, HTTPException
from datetime import date

from rivaflow.core.services.readiness_service import ReadinessService
from rivaflow.core.models import ReadinessCreate

router = APIRouter()
service = ReadinessService()


@router.post("/")
async def log_readiness(readiness: ReadinessCreate):
    """Log daily readiness check-in."""
    try:
        readiness_id = service.log_readiness(
            check_date=readiness.check_date,
            sleep=readiness.sleep,
            stress=readiness.stress,
            soreness=readiness.soreness,
            energy=readiness.energy,
            hotspot_note=readiness.hotspot_note,
            weight_kg=readiness.weight_kg,
        )
        entry = service.get_readiness(readiness.check_date)
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_readiness():
    """Get the most recent readiness entry."""
    entry = service.get_latest_readiness()
    if not entry:
        return None
    return entry


@router.get("/{check_date}")
async def get_readiness(check_date: date):
    """Get readiness for a specific date."""
    entry = service.get_readiness(check_date)
    if not entry:
        raise HTTPException(status_code=404, detail="Readiness entry not found")
    return entry


@router.get("/range/{start_date}/{end_date}")
async def get_readiness_range(start_date: date, end_date: date):
    """Get readiness entries within a date range."""
    return service.get_readiness_range(start_date, end_date)


@router.post("/weight")
async def log_weight_only(data: dict):
    """Log weight only for a date (quick logging for rest days)."""
    try:
        check_date = date.fromisoformat(data.get("check_date", date.today().isoformat()))
        weight_kg = float(data["weight_kg"])

        if weight_kg < 30 or weight_kg > 300:
            raise HTTPException(status_code=400, detail="Weight must be between 30 and 300 kg")

        readiness_id = service.log_weight_only(check_date, weight_kg)
        entry = service.get_readiness(check_date)
        return entry
    except KeyError:
        raise HTTPException(status_code=400, detail="weight_kg is required")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
