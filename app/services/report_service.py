import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.schemas.report_schemas import ExecutionReport
from app.utils.logging_config import logger


class ReportService:
    """Service for generating, saving, and retrieving execution reports."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        self.json_dir = os.path.join(reports_dir, "json")
        self.html_dir = os.path.join(reports_dir, "html")
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)

        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.jinja_env.filters["strftime"] = lambda dt, fmt: dt.strftime(fmt) if hasattr(dt, "strftime") else dt
        self.jinja_env.filters["isoformat"] = lambda dt: dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
        self.jinja_env.filters["basename"] = lambda path: os.path.basename(path) if path else path

    def generate_json_report(self, report: ExecutionReport) -> str:
        report_dict = report.model_dump(mode="json")
        json_str = json.dumps(report_dict, indent=2, default=str)
        logger.info("ReportService: JSON report generated for execution %s", report.execution_id)
        return json_str

    def save_json_report(self, report: ExecutionReport) -> str:
        json_content = self.generate_json_report(report)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.execution_id}_{timestamp}.json"
        filepath = os.path.join(self.json_dir, filename)
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(json_content)
        logger.info("ReportService: JSON report saved to %s", filepath)
        return filepath

    def load_json_report(self, filepath: str) -> Optional[ExecutionReport]:
        try:
            if not os.path.exists(filepath):
                logger.warning("ReportService: Report file not found: %s", filepath)
                return None
            with open(filepath, "r", encoding="utf-8") as file:
                report_dict = json.load(file)
            return ExecutionReport(**report_dict)
        except Exception as exc:
            logger.error("ReportService: Failed to load JSON report: %s", exc)
            return None

    def get_report_summary(self, report: ExecutionReport) -> Dict[str, Any]:
        return {
            "execution_id": report.execution_id,
            "status": report.status,
            "feature": report.feature_name,
            "scenario": report.scenario_name,
            "total_steps": report.summary.total_steps,
            "passed_steps": report.summary.passed_steps,
            "failed_steps": report.summary.failed_steps,
            "plan_a_steps": report.summary.plan_a_steps,
            "plan_b_steps": report.summary.plan_b_steps,
            "duration": report.summary.duration,
            "started_at": report.started_at.isoformat(),
            "finished_at": report.finished_at.isoformat(),
        }

    def generate_html_report(self, report: ExecutionReport) -> str:
        context = {
            "execution_id": report.execution_id,
            "status": report.status,
            "feature_name": report.feature_name,
            "scenario_name": report.scenario_name,
            "started_at": report.started_at,
            "finished_at": report.finished_at,
            "duration": report.duration,
            "total_steps": report.summary.total_steps,
            "passed_steps": report.summary.passed_steps,
            "failed_steps": report.summary.failed_steps,
            "plan_a_steps": report.summary.plan_a_steps,
            "plan_b_steps": report.summary.plan_b_steps,
            "steps": report.steps,
        }
        template = self.jinja_env.get_template("report.html.j2")
        html_str = template.render(context)
        logger.info("ReportService: HTML report generated for execution %s", report.execution_id)
        return html_str

    def save_html_report(self, report: ExecutionReport) -> str:
        html_content = self.generate_html_report(report)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.execution_id}_{timestamp}.html"
        filepath = os.path.join(self.html_dir, filename)
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(html_content)
        logger.info("ReportService: HTML report saved to %s", filepath)
        return filepath

    def save_both_reports(self, report: ExecutionReport) -> Dict[str, str]:
        return {"json": self.save_json_report(report), "html": self.save_html_report(report)}

    def list_json_reports(self) -> list:
        reports = []
        try:
            if os.path.exists(self.json_dir):
                for filename in sorted(os.listdir(self.json_dir), reverse=True):
                    if filename.endswith(".json"):
                        reports.append((filename, os.path.join(self.json_dir, filename)))
            return reports
        except Exception as exc:
            logger.error("ReportService: Failed to list JSON reports: %s", exc)
            return []


report_service = ReportService()
