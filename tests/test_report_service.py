"""
Unit tests for report generation and retrieval.
Tests ReportService functionality and reporting API endpoints.
"""

import pytest
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.schemas.report_schemas import ExecutionReport, ReportStep, ReportSummary
from app.services.report_service import ReportService
from app.utils.logging_config import logger


@pytest.fixture
def sample_report():
    """Create a sample ExecutionReport for testing."""
    steps = [
        ReportStep(
            step_text="Navigate to home page",
            action="click",
            selector="button.home",
            value=None,
            status="passed",
            message="Successfully clicked home button",
            duration=0.5,
            screenshot_path="reports/screenshots/step_001.png",
            metadata={"retry_count": 0}
        ),
        ReportStep(
            step_text="Fill login form",
            action="fill",
            selector="input#username",
            value="testuser",
            status="passed",
            message="Form filled successfully",
            duration=0.3,
            screenshot_path="reports/screenshots/step_002.png",
            metadata={"field_type": "text"}
        ),
        ReportStep(
            step_text="Submit form",
            action="click",
            selector="button.submit",
            value=None,
            status="failed",
            message="Timeout waiting for success page",
            duration=5.0,
            screenshot_path="reports/screenshots/step_003.png",
            metadata={"error_type": "TimeoutError"}
        )
    ]
    
    summary = ReportSummary(
        total_steps=3,
        passed_steps=2,
        failed_steps=1,
        duration=5.8
    )
    
    now = datetime.now()
    report = ExecutionReport(
        execution_id="test_exec_001",
        feature_name="User Login",
        scenario_name="Valid user login",
        status="failed",
        started_at=now,
        finished_at=datetime.now(),
        duration=5.8,
        steps=steps,
        summary=summary,
        screenshots=["reports/screenshots/step_001.png", "reports/screenshots/step_002.png"],
        metadata={"browser": "chromium", "headless": True}
    )
    
    return report


@pytest.fixture
def report_service_with_temp_dir(tmp_path):
    """Create ReportService with temporary directory."""
    service = ReportService(reports_dir=str(tmp_path))
    return service


class TestReportServiceJSON:
    """Test JSON report generation and persistence."""
    
    def test_generate_json_report(self, report_service_with_temp_dir, sample_report):
        """Test JSON report generation."""
        service = report_service_with_temp_dir
        json_str = service.generate_json_report(sample_report)
        
        # Verify it's valid JSON
        report_dict = json.loads(json_str)
        assert report_dict["execution_id"] == "test_exec_001"
        assert report_dict["status"] == "failed"
        assert report_dict["feature_name"] == "User Login"
        assert len(report_dict["steps"]) == 3
        assert report_dict["summary"]["passed_steps"] == 2
        assert report_dict["summary"]["failed_steps"] == 1
    
    def test_save_json_report(self, report_service_with_temp_dir, sample_report):
        """Test saving JSON report to disk."""
        service = report_service_with_temp_dir
        filepath = service.save_json_report(sample_report)
        
        # Verify file exists
        assert os.path.exists(filepath)
        assert filepath.endswith(".json")
        assert "test_exec_001" in filepath
        
        # Verify content
        with open(filepath, 'r') as f:
            content = json.load(f)
        assert content["execution_id"] == "test_exec_001"
        assert len(content["steps"]) == 3
    
    def test_load_json_report(self, report_service_with_temp_dir, sample_report):
        """Test loading JSON report from disk."""
        service = report_service_with_temp_dir
        
        # Save and reload
        filepath = service.save_json_report(sample_report)
        loaded_report = service.load_json_report(filepath)
        
        # Verify loaded report
        assert loaded_report is not None
        assert loaded_report.execution_id == sample_report.execution_id
        assert loaded_report.status == sample_report.status
        assert len(loaded_report.steps) == len(sample_report.steps)
        assert loaded_report.summary.passed_steps == 2
        assert loaded_report.summary.failed_steps == 1
    
    def test_load_nonexistent_report(self, report_service_with_temp_dir):
        """Test loading non-existent report returns None."""
        service = report_service_with_temp_dir
        loaded = service.load_json_report("/nonexistent/path.json")
        assert loaded is None


class TestReportServiceHTML:
    """Test HTML report generation."""
    
    def test_generate_html_report(self, report_service_with_temp_dir, sample_report):
        """Test HTML report generation."""
        service = report_service_with_temp_dir
        html_str = service.generate_html_report(sample_report)
        
        # Verify HTML structure
        assert isinstance(html_str, str)
        assert "test_exec_001" in html_str  # execution_id
        assert "User Login" in html_str  # feature_name
        assert "Valid user login" in html_str  # scenario_name
        assert "passed" in html_str or "failed" in html_str  # status
        assert "3" in html_str  # total_steps (as string)
    
    def test_save_html_report(self, report_service_with_temp_dir, sample_report):
        """Test saving HTML report to disk."""
        service = report_service_with_temp_dir
        filepath = service.save_html_report(sample_report)
        
        # Verify file exists
        assert os.path.exists(filepath)
        assert filepath.endswith(".html")
        assert "test_exec_001" in filepath
        
        # Verify content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "test_exec_001" in content
        assert "User Login" in content
    
    def test_html_report_contains_steps(self, report_service_with_temp_dir, sample_report):
        """Test HTML report contains all steps."""
        service = report_service_with_temp_dir
        html_str = service.generate_html_report(sample_report)
        
        # Verify steps are in HTML
        assert "Navigate to home page" in html_str
        assert "Fill login form" in html_str
        assert "Submit form" in html_str


class TestReportServiceSummary:
    """Test report summary generation."""
    
    def test_get_report_summary(self, report_service_with_temp_dir, sample_report):
        """Test report summary extraction."""
        service = report_service_with_temp_dir
        summary = service.get_report_summary(sample_report)
        
        assert summary["execution_id"] == "test_exec_001"
        assert summary["status"] == "failed"
        assert summary["feature"] == "User Login"
        assert summary["scenario"] == "Valid user login"
        assert summary["total_steps"] == 3
        assert summary["passed_steps"] == 2
        assert summary["failed_steps"] == 1
        assert "started_at" in summary
        assert "finished_at" in summary


class TestReportServiceListingAndManagement:
    """Test report listing and batch operations."""
    
    def test_list_json_reports_empty(self, report_service_with_temp_dir):
        """Test listing reports when directory is empty."""
        service = report_service_with_temp_dir
        reports = service.list_json_reports()
        assert reports == []
    
    def test_list_json_reports_multiple(self, report_service_with_temp_dir, sample_report):
        """Test listing multiple reports."""
        service = report_service_with_temp_dir
        
        # Save multiple reports
        service.save_json_report(sample_report)
        
        sample_report.execution_id = "test_exec_002"
        service.save_json_report(sample_report)
        
        sample_report.execution_id = "test_exec_003"
        service.save_json_report(sample_report)
        
        # List reports
        reports = service.list_json_reports()
        assert len(reports) == 3
        
        # Verify format
        for filename, filepath in reports:
            assert filename.endswith(".json")
            assert os.path.exists(filepath)
    
    def test_save_both_reports(self, report_service_with_temp_dir, sample_report):
        """Test saving both JSON and HTML reports."""
        service = report_service_with_temp_dir
        result = service.save_both_reports(sample_report)
        
        # Verify both files exist
        assert os.path.exists(result["json"])
        assert os.path.exists(result["html"])
        assert result["json"].endswith(".json")
        assert result["html"].endswith(".html")


class TestReportServiceEdgeCases:
    """Test edge cases and error handling."""
    
    def test_generate_report_with_empty_steps(self, report_service_with_temp_dir):
        """Test generating report with no steps."""
        service = report_service_with_temp_dir
        
        summary = ReportSummary(total_steps=0, passed_steps=0, failed_steps=0, duration=0)
        report = ExecutionReport(
            execution_id="empty_exec",
            feature_name="Empty Feature",
            scenario_name="Empty Scenario",
            status="skipped",
            started_at=datetime.now(),
            finished_at=datetime.now(),
            duration=0,
            steps=[],
            summary=summary,
            screenshots=[],
            metadata={}
        )
        
        json_str = service.generate_json_report(report)
        html_str = service.generate_html_report(report)
        
        assert "empty_exec" in json_str
        assert "empty_exec" in html_str
    
    def test_report_with_special_characters(self, report_service_with_temp_dir):
        """Test report with special characters in text."""
        service = report_service_with_temp_dir
        
        summary = ReportSummary(total_steps=1, passed_steps=1, failed_steps=0, duration=1.0)
        steps = [
            ReportStep(
                step_text="Test with <special> & \"quotes\" and 'apostrophes'",
                action="type",
                selector="input",
                value="<special>",
                status="passed",
                message="Handled special characters correctly",
                duration=0.5,
                screenshot_path="reports/screenshots/special.png",
                metadata={}
            )
        ]
        
        report = ExecutionReport(
            execution_id="special_chars",
            feature_name="Special < Characters & More",
            scenario_name="Test's Scenario",
            status="passed",
            started_at=datetime.now(),
            finished_at=datetime.now(),
            duration=1.0,
            steps=steps,
            summary=summary,
            screenshots=[],
            metadata={}
        )
        
        # Should not raise errors
        json_str = service.generate_json_report(report)
        html_str = service.generate_html_report(report)
        
        assert len(json_str) > 0
        assert len(html_str) > 0
    
    def test_report_directories_created(self, tmp_path):
        """Test that directories are created if missing."""
        reports_dir = str(tmp_path / "new_reports_dir")
        service = ReportService(reports_dir=reports_dir)
        
        # Verify directories exist
        assert os.path.exists(os.path.join(reports_dir, "json"))
        assert os.path.exists(os.path.join(reports_dir, "html"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
