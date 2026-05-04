import asyncio
import os
import sys

from app.utils.gherkin_parser import parse_gherkin_text
from app.services.executor_service import ExecutorService
from app.services.report_service import report_service


async def run_feature(feature_path: str):
    if not os.path.exists(feature_path):
        print(f"Feature file not found: {feature_path}")
        return 1

    with open(feature_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_gherkin_text(content)
    if not parsed or not parsed.get("scenarios"):
        print("No scenarios found in feature")
        return 1

    scenario = parsed["scenarios"][0]
    steps = scenario.get("steps", [])

    # Find a navigation step to get base URL
    url = None
    for s in steps:
        if s["keyword"].lower().startswith("given") and "navigate to" in s["text"].lower():
            # extract URL between quotes
            import re
            m = re.search(r'"([^"]+)"', s["text"])
            if m:
                url = m.group(1)
                break

    if not url:
        print("No navigation URL found in feature. Please include a Given step with a URL.")
        return 1

    executor = ExecutorService()
    executor.feature_name = parsed.get("feature_name") or os.path.splitext(os.path.basename(feature_path))[0]
    executor.scenario_name = scenario.get("name") or "Unnamed scenario"
    try:
        await executor.start_session(url)

        # execute steps (skip the Given navigation we already did)
        for step in steps:
            text = step.get("text")
            kw = step.get("keyword", "").strip().lower()
            if kw.startswith("given") and "navigate to" in text.lower():
                continue
            print(f"Executing: {text}")
            try:
                await executor.execute_gherkin_step(text)
            except Exception as exc:
                print(f"Step failed: {text} -> {exc}")
                # continue executing remaining steps to capture failures

        report = executor.get_execution_report()
        saved = report_service.save_both_reports(report)
        print("Reports saved:")
        print(saved)
        return 0
    finally:
        await executor.stop_session()


def main():
    feature = sys.argv[1] if len(sys.argv) > 1 else "tests/feature/demo_pfe.feature"
    code = asyncio.run(run_feature(feature))
    sys.exit(code)


if __name__ == "__main__":
    main()
