"""Readiness check-in endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import date

from rivaflow.core.services.readiness_service import ReadinessService
from rivaflow.core.models import ReadinessCreate
from rivaflow.core.dependencies import get_current_user

router = APIRouter()
service = ReadinessService()


@router.post("/")
async def log_readiness(readiness: ReadinessCreate, current_user: dict = Depends(get_current_user)):
    """Log daily readiness check-in."""
    try:
        readiness_id = service.log_readiness(
            user_id=current_user["id"],
            check_date=readiness.check_date,
            sleep=readiness.sleep,
            stress=readiness.stress,
            soreness=readiness.soreness,
            energy=readiness.energy,
            hotspot_note=readiness.hotspot_note,
            weight_kg=readiness.weight_kg,
        )
        entry = service.get_readiness(user_id=current_user["id"], check_date=readiness.check_date)
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_readiness(current_user: dict = Depends(get_current_user)):
    """Get the most recent readiness entry."""
    entry = service.get_latest_readiness(user_id=current_user["id"])
    if not entry:
        return None
    return entry


@router.get("/{check_date}")
async def get_readiness(check_date: date, current_user: dict = Depends(get_current_user)):
    """Get readiness for a specific date."""
    entry = service.get_readiness(user_id=current_user["id"], check_date=check_date)
    if not entry:
        raise HTTPException(status_code=404, detail="Readiness entry not found")
    return entry


@router.get("/range/{start_date}/{end_date}")
async def get_readiness_range(start_date: date, end_date: date, current_user: dict = Depends(get_current_user)):
    """Get readiness entries within a date range."""
    return service.get_readiness_range(user_id=current_user["id"], start_date=start_date, end_date=end_date)


@router.post("/weight")
async def log_weight_only(data: dict, current_user: dict = Depends(get_current_user)):
    """Log weight only for a date (quick logging for rest days)."""
    try:
        check_date = date.fromisoformat(data.get("check_date", date.today().isoformat()))
        weight_kg = float(data["weight_kg"])

        if weight_kg < 30 or weight_kg > 300:
            raise HTTPException(status_code=400, detail="Weight must be between 30 and 300 kg")

        readiness_id = service.log_weight_only(user_id=current_user["id"], check_date=check_date, weight_kg=weight_kg)
        entry = service.get_readiness(user_id=current_user["id"], check_date=check_date)
        return entry
    except KeyError:
        raise HTTPException(status_code=400, detail="weight_kg is required")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
