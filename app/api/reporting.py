"""
API endpoints for test execution reports.
Provides endpoints to retrieve, list, and manage test execution reports.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from app.services.report_service import report_service
from app.utils.logging_config import logger


router = APIRouter(prefix="/api/ia", tags=["reports"])


@router.get("/reports/{execution_id}")
async def get_report(execution_id: str, format: Optional[str] = "json") -> Dict[str, Any]:
    try:
        reports = report_service.list_json_reports()
        report_path = next((filepath for filename, filepath in reports if execution_id in filename), None)
        if not report_path:
            raise HTTPException(status_code=404, detail=f"Report not found for execution {execution_id}")

        report = report_service.load_json_report(report_path)
        if not report:
            raise HTTPException(status_code=500, detail="Failed to load report")

        if format == "html":
            return {
                "execution_id": report.execution_id,
                "format": "html",
                "content": report_service.generate_html_report(report),
                "status": "success",
            }

        return {
            "execution_id": report.execution_id,
            "format": "json",
            "status": report.status,
            "feature_name": report.feature_name,
            "scenario_name": report.scenario_name,
            "started_at": report.started_at.isoformat(),
            "finished_at": report.finished_at.isoformat(),
            "duration": report.duration,
            "summary": {
                "total_steps": report.summary.total_steps,
                "passed_steps": report.summary.passed_steps,
                "failed_steps": report.summary.failed_steps,
                "plan_a_steps": report.summary.plan_a_steps,
                "plan_b_steps": report.summary.plan_b_steps,
                "duration": report.summary.duration,
            },
            "steps_count": len(report.steps),
            "report": report_service.get_report_summary(report),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ReportingAPI: Failed to get report: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/reports")
async def list_reports() -> Dict[str, Any]:
    try:
        reports = report_service.list_json_reports()
        report_summaries = []
        for filename, filepath in reports:
            report = report_service.load_json_report(filepath)
            if report:
                report_summaries.append(
                    {
                        "filename": filename,
                        "execution_id": report.execution_id,
                        "feature_name": report.feature_name,
                        "scenario_name": report.scenario_name,
                        "status": report.status,
                        "started_at": report.started_at.isoformat(),
                        "total_steps": report.summary.total_steps,
                        "passed_steps": report.summary.passed_steps,
                        "failed_steps": report.summary.failed_steps,
                        "plan_a_steps": report.summary.plan_a_steps,
                        "plan_b_steps": report.summary.plan_b_steps,
                    }
                )

        return {"total_reports": len(report_summaries), "reports": report_summaries, "status": "success"}
    except Exception as exc:
        logger.error("ReportingAPI: Failed to list reports: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/reports/{execution_id}/summary")
async def get_report_summary(execution_id: str) -> Dict[str, Any]:
    try:
        reports = report_service.list_json_reports()
        report_path = next((filepath for filename, filepath in reports if execution_id in filename), None)
        if not report_path:
            raise HTTPException(status_code=404, detail=f"Report not found for execution {execution_id}")

        report = report_service.load_json_report(report_path)
        if not report:
            raise HTTPException(status_code=500, detail="Failed to load report")

        return {"execution_id": execution_id, "summary": report_service.get_report_summary(report), "status": "success"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ReportingAPI: Failed to get report summary: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
