from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ReportStep(BaseModel):
    step_text: str
    action: Optional[str] = None
    selector: Optional[str] = None
    plan_used: Optional[str] = None
    value: Optional[str] = None
    status: str
    message: Optional[str] = None
    duration: Optional[float] = None
    screenshot_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ReportSummary(BaseModel):
    total_steps: int
    passed_steps: int
    failed_steps: int
    duration: float
    plan_a_steps: int = 0
    plan_b_steps: int = 0


class ExecutionReport(BaseModel):
    execution_id: str
    feature_name: Optional[str] = None
    scenario_name: Optional[str] = None
    status: str
    started_at: datetime
    finished_at: datetime
    duration: float
    steps: List[ReportStep]
    summary: ReportSummary
    screenshots: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
