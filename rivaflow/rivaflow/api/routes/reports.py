"""Report and analytics endpoints."""

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.report_service import ReportService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
service = ReportService()


@router.get("/week")
@limiter.limit("60/minute")
def get_week_report(
    request: Request,
    target_date: date = None,
    current_user: dict = Depends(get_current_user),
):
    """Get current week report."""
    start_date, end_date = service.get_week_dates(target_date)
    report = service.generate_report(
        user_id=current_user["id"], start_date=start_date, end_date=end_date
    )
    return report


@router.get("/month")
@limiter.limit("60/minute")
def get_month_report(
    request: Request,
    target_date: date = None,
    current_user: dict = Depends(get_current_user),
):
    """Get current month report."""
    start_date, end_date = service.get_month_dates(target_date)
    report = service.generate_report(
        user_id=current_user["id"], start_date=start_date, end_date=end_date
    )
    return report


@router.get("/range/{start_date}/{end_date}")
@limiter.limit("60/minute")
def get_range_report(
    request: Request,
    start_date: date,
    end_date: date,
    current_user: dict = Depends(get_current_user),
):
    """Get report for custom date range."""
    report = service.generate_report(
        user_id=current_user["id"], start_date=start_date, end_date=end_date
    )
    return report


@router.get("/week/csv")
@limiter.limit("60/minute")
def export_week_csv(
    request: Request,
    target_date: date = None,
    current_user: dict = Depends(get_current_user),
):
    """Export week report as CSV."""
    start_date, end_date = service.get_week_dates(target_date)
    report = service.generate_report(
        user_id=current_user["id"], start_date=start_date, end_date=end_date
    )

    # Create CSV in memory
    output = io.StringIO()
    if report["sessions"]:
        fieldnames = [
            "date",
            "class_type",
            "gym_name",
            "location",
            "duration_mins",
            "intensity",
            "rolls",
            "submissions_for",
            "submissions_against",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for session in report["sessions"]:
            writer.writerow(
                {
                    "date": session["session_date"],
                    "class_type": session["class_type"],
                    "gym_name": session["gym_name"],
                    "location": session.get("location", ""),
                    "duration_mins": session["duration_mins"],
                    "intensity": session["intensity"],
                    "rolls": session["rolls"],
                    "submissions_for": session["submissions_for"],
                    "submissions_against": session["submissions_against"],
                }
            )

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=week_report.csv"},
    )
