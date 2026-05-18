import base64
import asyncio
import json
import os
import re
import subprocess
import sys
from typing import Any

import httpx
import streamlit as st

os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/tmp/ms-playwright")


st.set_page_config(
    page_title="Data-AI Test Studio",
    page_icon="DA",
    layout="wide",
)


SAMPLE_GHERKIN = """Feature: Google search pipeline smoke

Scenario: Search for OpenAI on Google
  Given I navigate to "https://www.google.com/search?q=OpenAI"
  Then I should see "OpenAI"
"""


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "generated-gherkin-test"


def get_backend_url() -> str:
    backend_url = os.getenv("BACKEND_URL", "")
    if not backend_url:
        try:
            backend_url = st.secrets.get("BACKEND_URL", "")
        except Exception:
            backend_url = ""
    return str(backend_url).rstrip("/")


@st.cache_resource(show_spinner="Loading NLP and vision models...")
def get_local_client() -> Any:
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


@st.cache_resource(show_spinner="Installing Playwright Chromium...")
def ensure_playwright_browser() -> None:
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
        text=True,
    )


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    backend_url = get_backend_url()
    if backend_url:
        url = f"{backend_url}{path}"
        with httpx.Client(timeout=180.0, follow_redirects=True) as client:
            if method == "GET":
                response = client.get(url)
            else:
                response = client.post(url, json=payload or {})
    else:
        client = get_local_client()
        if method == "GET":
            response = client.get(path)
        else:
            response = client.post(path, json=payload or {})

    data = response.json() if response.content else {}
    if response.status_code >= 400:
        detail = data.get("detail", data)
        raise RuntimeError(detail if isinstance(detail, str) else json.dumps(detail, indent=2))
    return data


def show_json(data: Any) -> None:
    st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def render_report_files(report_paths: dict[str, str]) -> None:
    html_path = report_paths.get("html")
    json_path = report_paths.get("json")

    if not html_path and not json_path:
        st.warning("No report files were returned by the pipeline.")
        return

    html_tab, json_tab, files_tab = st.tabs(["HTML report", "JSON file", "File paths"])

    with html_tab:
        if html_path and os.path.exists(html_path):
            st.components.v1.html(read_text_file(html_path), height=700, scrolling=True)
        else:
            st.warning("HTML report file was not found.")

    with json_tab:
        if json_path and os.path.exists(json_path):
            show_json(json.loads(read_text_file(json_path)))
        else:
            st.warning("JSON report file was not found.")

    with files_tab:
        show_json(report_paths)


def render_api_report(execution_id: str) -> None:
    html_tab, json_tab = st.tabs(["HTML report", "JSON file"])

    with html_tab:
        html_report = request_json("GET", f"/api/ia/reports/{execution_id}?format=html")
        st.components.v1.html(html_report["content"], height=700, scrolling=True)

    with json_tab:
        show_json(request_json("GET", f"/api/ia/reports/{execution_id}"))


def load_json_file(path: str) -> Any:
    return json.loads(read_text_file(path))


def list_local_reports() -> list[dict[str, Any]]:
    json_dir = os.path.join("reports", "json")
    if not os.path.exists(json_dir):
        return []

    reports = []
    for filename in sorted(os.listdir(json_dir), reverse=True):
        if not filename.endswith(".json"):
            continue

        path = os.path.join(json_dir, filename)
        try:
            report = load_json_file(path)
        except Exception:
            continue

        summary = report.get("summary", {})
        reports.append(
            {
                "filename": filename,
                "path": path,
                "execution_id": report.get("execution_id", ""),
                "feature_name": report.get("feature_name", ""),
                "scenario_name": report.get("scenario_name", ""),
                "status": report.get("status", ""),
                "started_at": report.get("started_at", ""),
                "total_steps": summary.get("total_steps", 0),
                "passed_steps": summary.get("passed_steps", 0),
                "failed_steps": summary.get("failed_steps", 0),
                "plan_a_steps": summary.get("plan_a_steps", 0),
                "plan_b_steps": summary.get("plan_b_steps", 0),
            }
        )
    return reports


def find_html_report(execution_id: str) -> str | None:
    html_dir = os.path.join("reports", "html")
    if not execution_id or not os.path.exists(html_dir):
        return None

    matches = [
        os.path.join(html_dir, filename)
        for filename in sorted(os.listdir(html_dir), reverse=True)
        if filename.endswith(".html") and execution_id in filename
    ]
    return matches[0] if matches else None


def get_target_url_from_gherkin(gherkin_text: str) -> str | None:
    match = re.search(r'Given\s+I\s+navigate\s+to\s+"([^"]+)"', gherkin_text, re.IGNORECASE)
    return match.group(1) if match else None


async def execute_live_feature(
    *,
    url: str,
    gherkin_text: str,
    feature_name: str,
    scenario_name: str,
    status_slot: Any,
    progress_slot: Any,
) -> dict[str, Any]:
    from app.services.executor_service import ExecutorService
    from app.services.report_service import report_service
    from app.utils.gherkin_parser import parse_gherkin_text

    parsed = parse_gherkin_text(gherkin_text)
    if not parsed or not parsed.get("scenarios"):
        raise RuntimeError("No scenarios found in the provided Gherkin text")

    scenario = parsed["scenarios"][0]
    steps = scenario.get("steps", [])
    target_url = url or get_target_url_from_gherkin(gherkin_text)
    if not target_url:
        raise RuntimeError("A target URL is required.")

    executable_steps = [
        step
        for step in steps
        if not (
            step.get("keyword", "").strip().lower().startswith("given")
            and "navigate to" in step.get("text", "").lower()
        )
    ]

    executor = ExecutorService()
    step_results = []
    try:
        status_slot.info("Opening browser and navigating...")
        await executor.start_session(target_url)
        executor.feature_name = feature_name or parsed.get("feature_name")
        executor.scenario_name = scenario_name or scenario.get("name")

        total = max(len(executable_steps), 1)
        for index, step in enumerate(executable_steps, start=1):
            text = step.get("text", "")
            status_slot.info(f"Step {index}/{len(executable_steps)}: {text}")
            try:
                result = await executor.execute_gherkin_step(text)
            except Exception as exc:
                screenshot_path = await executor._take_step_screenshot(text)
                result = {
                    "status": "failed",
                    "step": text,
                    "error": str(exc),
                    "screenshot": screenshot_path,
                }
            step_results.append(result)

            progress_slot.progress(index / total)
            if result.get("status") == "failed":
                status_slot.error(f"Step failed: {text}")
                break

        execution_report = executor.get_execution_report()
        report_paths = report_service.save_both_reports(execution_report)
        return {
            "status": "completed",
            "execution_id": execution_report.execution_id,
            "feature_name": execution_report.feature_name,
            "scenario_name": execution_report.scenario_name,
            "summary": execution_report.summary.model_dump(mode="json"),
            "steps": step_results,
            "reports": report_paths,
        }
    finally:
        try:
            await executor.stop_session()
        except Exception:
            pass


def run_live_feature(**kwargs: Any) -> dict[str, Any]:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(execute_live_feature(**kwargs))


def render_status() -> None:
    st.subheader("Backend Status")
    st.success("Streamlit interface is running.")
    backend_url = get_backend_url()
    if backend_url:
        st.caption(f"Connected backend: {backend_url}")
    else:
        st.caption("No BACKEND_URL is configured. Local mode will import the FastAPI backend when needed.")
    if st.button("Check backend health", width="stretch"):
        try:
            data = request_json("GET", "/health")
            st.success(f"{data['service']} is {data['status']} ({data['environment']})")
            show_json(data)
        except Exception as exc:
            st.error(f"Health check failed: {exc}")


def render_studio() -> None:
    st.subheader("Scenario Studio")
    left, right = st.columns([0.52, 0.48], gap="large")

    with left:
        feature_name = st.text_input("Feature name", value="Google search pipeline smoke")
        scenario_name = st.text_input("Scenario name", value="Search for OpenAI on Google")
        target_url = st.text_input("Website URL", value="https://www.google.com/search?q=OpenAI")
        gherkin_text = st.text_area("Gherkin scenario", value=SAMPLE_GHERKIN, height=280)

        actions = st.columns(3)
        parse_clicked = actions[0].button("Parse", width="stretch")
        generate_clicked = actions[1].button("Generate Script", width="stretch")
        execute_clicked = actions[2].button("Run Pipeline", type="primary", width="stretch")

    with right:
        output = st.empty()
        live_status = st.empty()
        live_progress = st.empty()

    if parse_clicked:
        with st.spinner("Parsing Gherkin with NLP..."):
            try:
                output.json(request_json("POST", "/api/ia/parse-gherkin", {"gherkin_text": gherkin_text}))
            except Exception as exc:
                output.error(str(exc))

    if generate_clicked:
        with st.spinner("Generating Playwright script..."):
            try:
                result = request_json(
                    "POST",
                    "/api/ia/generate-test",
                    {
                        "gherkin_text": gherkin_text,
                        "test_name": slugify(scenario_name),
                        "base_url": target_url,
                    },
                )
                output.code(result.get("script", ""), language="javascript")
                with st.expander("Generated actions", expanded=False):
                    show_json(result.get("actions", []))
            except Exception as exc:
                output.error(str(exc))

    if execute_clicked:
        with st.spinner("Running browser automation. This can take a moment..."):
            try:
                if get_backend_url():
                    result = request_json(
                        "POST",
                        "/api/ia/execute-feature",
                        {
                            "url": target_url,
                            "gherkin_text": gherkin_text,
                            "feature_name": feature_name,
                            "scenario_name": scenario_name,
                        },
                    )
                else:
                    ensure_playwright_browser()
                    result = run_live_feature(
                        url=target_url,
                        gherkin_text=gherkin_text,
                        feature_name=feature_name,
                        scenario_name=scenario_name,
                        status_slot=live_status,
                        progress_slot=live_progress,
                    )
                live_status.empty()
                live_progress.empty()
                with output.container():
                    execution_id = result.get("execution_id")
                    if get_backend_url() and execution_id:
                        render_api_report(execution_id)
                    else:
                        render_report_files(result.get("reports", {}))
            except Exception as exc:
                live_status.empty()
                live_progress.empty()
                output.error(str(exc))


def render_screenshot_analyzer() -> None:
    st.subheader("Screenshot Analyzer")
    uploaded = st.file_uploader("Upload a UI screenshot", type=["png", "jpg", "jpeg", "webp"])
    target_text = st.text_input("Target text or element label", placeholder="Login, Search, email...")
    min_confidence = st.slider("Minimum confidence", 0.05, 0.95, 0.25, 0.05)

    if uploaded:
        st.image(uploaded, caption=uploaded.name, width="stretch")

    if st.button("Analyze Screenshot", type="primary", disabled=uploaded is None):
        image_bytes = uploaded.getvalue()
        image_base64 = "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")
        with st.spinner("Running YOLO/OCR detection..."):
            try:
                result = request_json(
                    "POST",
                    "/api/ia/analyze-screenshot",
                    {
                        "image_base64": image_base64,
                        "filename": uploaded.name,
                        "target_text": target_text or None,
                        "include_ocr": True,
                        "min_confidence": min_confidence,
                    },
                )
                st.success(f"Detected {len(result['detection']['elements'])} UI elements.")
                show_json(result)
            except Exception as exc:
                st.error(str(exc))


def render_reports() -> None:
    st.subheader("Reports")

    if get_backend_url():
        try:
            data = request_json("GET", "/api/ia/reports")
            reports = data.get("reports", [])
        except Exception as exc:
            st.error(f"Could not load reports: {exc}")
            return

        if not reports:
            st.info("No reports yet. Run a scenario to create one.")
            return

        st.dataframe(reports, width="stretch", hide_index=True)
        execution_ids = [report["execution_id"] for report in reports]
        selected = st.selectbox("Open report", execution_ids)
        render_api_report(selected)
        return

    reports = list_local_reports()
    if not reports:
        st.info("No reports yet. Run a scenario to create one.")
        return

    table_rows = [{key: value for key, value in report.items() if key != "path"} for report in reports]
    st.dataframe(table_rows, width="stretch", hide_index=True)
    execution_ids = [report["execution_id"] for report in reports]
    selected = st.selectbox("Open report", execution_ids)
    selected_report = next(report for report in reports if report["execution_id"] == selected)
    html_path = find_html_report(selected)

    json_tab, html_tab = st.tabs(["JSON file", "HTML report"])
    with json_tab:
        show_json(load_json_file(selected_report["path"]))
    with html_tab:
        if html_path:
            st.components.v1.html(read_text_file(html_path), height=700, scrolling=True)
        else:
            st.warning("HTML report file was not found.")


def main() -> None:
    st.title("Data-AI Test Studio")
    st.caption("Streamlit interface for the self-healing functional test automation pipeline.")

    page = st.sidebar.radio(
        "Page",
        ["Status", "Scenario Studio", "Reports", "Screenshot Analyzer"],
        label_visibility="collapsed",
    )

    if page == "Status":
        render_status()
    elif page == "Scenario Studio":
        render_studio()
    elif page == "Reports":
        render_reports()
    elif page == "Screenshot Analyzer":
        render_screenshot_analyzer()


if __name__ == "__main__":
    main()
