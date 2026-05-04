import argparse
import asyncio
import json
import os
from typing import Any

from app.services.nlp_service import NLPService
from app.services.vision_service import VisionService
from app.services.executor_service import ExecutorService


def serialize_report(report: Any) -> dict:
    # ExecutionReport is a pydantic model; use JSON mode so datetimes serialize cleanly.
    if hasattr(report, "model_dump"):
        return report.model_dump(mode="json")
    if hasattr(report, "dict"):
        return report.dict()
    if hasattr(report, "__dict__"):
        return report.__dict__
    return dict(report)


async def run_pipeline(url: str, gherkin_step: str, headless: bool, report_path: str):
    nlp = NLPService()
    vision = VisionService()
    executor = ExecutorService(nlp, vision)

    try:
        await executor.start_session(url)
        print(f"Running pipeline for: {gherkin_step} on {url}")

        result = await executor.execute_gherkin_step(gherkin_step)

        report = executor.get_execution_report()
        report_data = serialize_report(report)

        # Include the last step result for convenience.
        output = {"step_result": result, "report": report_data}

        if report_path:
            os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"Report saved to: {report_path}")
        else:
            print(json.dumps(output, indent=2, ensure_ascii=False))
    finally:
        await executor.stop_session()


def main():
    parser = argparse.ArgumentParser(description="Run full pipeline for one Gherkin step against a URL")
    parser.add_argument("--url", required=True, help="Target website URL to test (e.g. https://example.com)")
    parser.add_argument("--gherkin", required=True, help='Gherkin step text, e.g. "When I click the submit button"')
    parser.add_argument("--report-path", default="reports/last_run_report.json", help="Where to save the JSON report")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (not implemented override)")

    args = parser.parse_args()

    # Note: headless handling can be added to ExecutorService.start_session if needed.
    asyncio.run(run_pipeline(args.url, args.gherkin, args.headless, args.report_path))


if __name__ == "__main__":
    main()
