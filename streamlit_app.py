import base64
import json
import os
import re
from typing import Any

import streamlit as st
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "production")

from app.main import app


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


@st.cache_resource(show_spinner="Loading NLP and vision models...")
def get_client() -> TestClient:
    return TestClient(app)


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    client = get_client()
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


def render_status() -> None:
    st.subheader("Backend Status")
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
        parse_clicked = actions[0].button("Parse", use_container_width=True)
        generate_clicked = actions[1].button("Generate Script", use_container_width=True)
        execute_clicked = actions[2].button("Run Pipeline", type="primary", use_container_width=True)

    with right:
        output = st.empty()

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
                summary = result.get("summary", {})
                if summary.get("failed_steps", 0):
                    output.warning("Pipeline completed with failed steps.")
                else:
                    output.success("Pipeline passed.")
                output.json(result)
            except Exception as exc:
                output.error(str(exc))


def render_screenshot_analyzer() -> None:
    st.subheader("Screenshot Analyzer")
    uploaded = st.file_uploader("Upload a UI screenshot", type=["png", "jpg", "jpeg", "webp"])
    target_text = st.text_input("Target text or element label", placeholder="Login, Search, email...")
    min_confidence = st.slider("Minimum confidence", 0.05, 0.95, 0.25, 0.05)

    if uploaded:
        st.image(uploaded, caption=uploaded.name, use_container_width=True)

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
    try:
        data = request_json("GET", "/api/ia/reports")
    except Exception as exc:
        st.error(f"Could not load reports: {exc}")
        return

    reports = data.get("reports", [])
    if not reports:
        st.info("No reports yet. Run a scenario to create one.")
        return

    st.dataframe(reports, use_container_width=True, hide_index=True)
    execution_ids = [report["execution_id"] for report in reports]
    selected = st.selectbox("Open report", execution_ids)
    col1, col2 = st.columns(2)

    if col1.button("Show JSON", use_container_width=True):
        show_json(request_json("GET", f"/api/ia/reports/{selected}"))

    if col2.button("Show HTML", use_container_width=True):
        html_report = request_json("GET", f"/api/ia/reports/{selected}?format=html")
        st.components.v1.html(html_report["content"], height=700, scrolling=True)


def main() -> None:
    st.title("Data-AI Test Studio")
    st.caption("Streamlit interface for the self-healing functional test automation pipeline.")

    tabs = st.tabs(["Status", "Scenario Studio", "Screenshot Analyzer", "Reports"])
    with tabs[0]:
        render_status()
    with tabs[1]:
        render_studio()
    with tabs[2]:
        render_screenshot_analyzer()
    with tabs[3]:
        render_reports()


if __name__ == "__main__":
    main()
