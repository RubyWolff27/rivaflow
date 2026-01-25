"""Report and analytics endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import date
import io
import csv

from rivaflow.core.services.report_service import ReportService

router = APIRouter()
service = ReportService()


@router.get("/week")
async def get_week_report(target_date: date = None):
    """Get current week report."""
    start_date, end_date = service.get_week_dates(target_date)
    report = service.generate_report(start_date, end_date)
    return report


@router.get("/month")
async def get_month_report(target_date: date = None):
    """Get current month report."""
    start_date, end_date = service.get_month_dates(target_date)
    report = service.generate_report(start_date, end_date)
    return report


@router.get("/range/{start_date}/{end_date}")
async def get_range_report(start_date: date, end_date: date):
    """Get report for custom date range."""
    report = service.generate_report(start_date, end_date)
    return report


@router.get("/week/csv")
async def export_week_csv(target_date: date = None):
    """Export week report as CSV."""
    start_date, end_date = service.get_week_dates(target_date)
    report = service.generate_report(start_date, end_date)

    # Create CSV in memory
    output = io.StringIO()
    if report["sessions"]:
        fieldnames = ["date", "class_type", "gym_name", "location", "duration_mins",
                     "intensity", "rolls", "submissions_for", "submissions_against"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for session in report["sessions"]:
            writer.writerow({
                "date": session["session_date"],
                "class_type": session["class_type"],
                "gym_name": session["gym_name"],
                "location": session.get("location", ""),
                "duration_mins": session["duration_mins"],
                "intensity": session["intensity"],
                "rolls": session["rolls"],
                "submissions_for": session["submissions_for"],
                "submissions_against": session["submissions_against"],
            })

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=week_report.csv"}
    )
