const defaultApiBase = "http://localhost:8000/api/ia";

const templates = {
  google: {
    url: "https://www.google.com/search?q=OpenAI",
    feature: "Google search pipeline smoke",
    scenario: "Search for OpenAI on Google",
    gherkin: `Feature: Google search pipeline smoke

Scenario: Search for OpenAI on Google
  Given I navigate to "https://www.google.com/search?q=OpenAI"
  Then I should see "OpenAI"`
  },
  facebook: {
    url: "https://www.facebook.com",
    feature: "Facebook login validation",
    scenario: "Invalid login shows an error",
    gherkin: `Feature: Facebook login validation

Scenario: Invalid login shows an error
  Given I navigate to "https://www.facebook.com"
  When I click the "Allow all cookies" button
  And I fill the "email" field with "demo@example.com"
  And I fill the "pass" field with "demo password"
  And I click the "login" button
  Then I should see the error message "The email address you entered isn't connected to an account"`
  }
};

const state = {
  apiBase: localStorage.getItem("dataAiApiBase") || defaultApiBase,
  user: JSON.parse(localStorage.getItem("dataAiUser") || "null"),
  selectedFile: null,
  reports: []
};

const qs = (selector) => document.querySelector(selector);
const qsa = (selector) => [...document.querySelectorAll(selector)];

document.addEventListener("DOMContentLoaded", () => {
  initAuth();
  initNavigation();
  initSettings();
  initStudio();
  initScreenshots();
  initReports();

  if (state.user) {
    showApp();
  }
});

function apiUrl(path) {
  return `${state.apiBase.replace(/\/$/, "")}${path}`;
}

function toast(message, type = "primary") {
  const container = qs("#toast-container");
  const id = `toast-${Date.now()}`;
  const element = document.createElement("div");
  element.id = id;
  element.className = `toast align-items-center text-bg-${type} border-0`;
  element.role = "alert";
  element.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${escapeHtml(message)}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(element);
  const instance = new bootstrap.Toast(element, { delay: 3500 });
  instance.show();
  element.addEventListener("hidden.bs.toast", () => element.remove());
}

function setOutput(element, value) {
  element.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function initAuth() {
  qs("#auth-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const name = qs("#auth-name").value.trim();
    const email = qs("#auth-email").value.trim();
    const role = qs("#auth-role").value;
    state.user = { name, email, role };
    localStorage.setItem("dataAiUser", JSON.stringify(state.user));
    showApp();
  });

  qs("#logout-btn").addEventListener("click", () => {
    localStorage.removeItem("dataAiUser");
    state.user = null;
    qs("#app-shell").classList.add("d-none");
    qs("#auth-screen").classList.remove("d-none");
  });
}

function showApp() {
  qs("#auth-screen").classList.add("d-none");
  qs("#app-shell").classList.remove("d-none");
  qs("#user-name").textContent = state.user.name;
  qs("#user-role").textContent = state.user.role;
  qs("#user-initials").textContent = initials(state.user.name);
  qs("#api-base").value = state.apiBase;
  checkBackend();
  loadReports();
}

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("") || "QA";
}

function initNavigation() {
  qsa("[data-view]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      showView(button.dataset.view);
    });
  });

  qsa("[data-jump]").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.jump));
  });
}

function showView(viewId) {
  qsa(".view").forEach((view) => view.classList.toggle("active", view.id === viewId));
  qsa(".sidebar .nav-link").forEach((item) => item.classList.toggle("active", item.dataset.view === viewId));
  const active = qs(`[data-view="${viewId}"]`);
  qs("#page-title").textContent = active ? active.textContent.trim() : "Workspace";
}

function initSettings() {
  const dark = localStorage.getItem("dataAiDarkMode") === "true";
  document.body.classList.toggle("dark-mode", dark);
  qs("#theme-switch").checked = dark;

  qs("#theme-switch").addEventListener("change", (event) => {
    document.body.classList.toggle("dark-mode", event.target.checked);
    localStorage.setItem("dataAiDarkMode", String(event.target.checked));
  });

  qs("#save-settings").addEventListener("click", () => {
    state.apiBase = qs("#api-base").value.trim() || defaultApiBase;
    localStorage.setItem("dataAiApiBase", state.apiBase);
    toast("Settings saved", "success");
    checkBackend();
  });
}

async function checkBackend() {
  const badge = qs("#backend-state");
  badge.className = "backend-state";
  badge.querySelector("span:last-child").textContent = "Checking backend";
  try {
    const response = await fetch(state.apiBase.replace("/api/ia", "") + "/health");
    if (!response.ok) throw new Error("Backend unavailable");
    badge.classList.add("online");
    badge.querySelector("span:last-child").textContent = "Backend online";
  } catch {
    badge.classList.add("offline");
    badge.querySelector("span:last-child").textContent = "Backend offline";
  }
}

function initStudio() {
  qsa("[data-template]").forEach((button) => {
    button.addEventListener("click", () => applyTemplate(button.dataset.template));
  });

  qs("#parse-btn").addEventListener("click", parseGherkin);
  qs("#generate-btn").addEventListener("click", generateScript);
  qs("#scenario-form").addEventListener("submit", executeScenario);
}

function applyTemplate(name) {
  const template = templates[name];
  qs("#target-url").value = template.url;
  qs("#feature-name").value = template.feature;
  qs("#scenario-name").value = template.scenario;
  qs("#gherkin-input").value = template.gherkin;
}

function setRunState(label, type = "secondary", loading = false) {
  const badge = qs("#run-badge");
  badge.className = `badge text-bg-${type}`;
  badge.textContent = label;
  qs("#run-loader").classList.toggle("d-none", !loading);
}

async function parseGherkin() {
  setRunState("Parsing", "warning", true);
  setOutput(qs("#execution-output"), "Parsing Gherkin with NLP service...");
  try {
    const data = await postJson("/parse-gherkin", { gherkin_text: qs("#gherkin-input").value });
    setOutput(qs("#execution-output"), data);
    setRunState("Parsed", "success");
    toast("Scenario parsed successfully", "success");
  } catch (error) {
    setRunState("Parse failed", "danger");
    setOutput(qs("#execution-output"), error.message);
    toast(error.message, "danger");
  }
}

async function generateScript() {
  setRunState("Generating", "warning", true);
  setOutput(qs("#script-output"), "Generating Playwright script...");
  try {
    const data = await postJson("/generate-test", {
      gherkin_text: qs("#gherkin-input").value,
      test_name: slugify(qs("#scenario-name").value || "generated-gherkin-test"),
      base_url: qs("#target-url").value
    });
    setOutput(qs("#script-output"), data.script);
    setOutput(qs("#execution-output"), data.actions);
    setRunState("Script ready", "success");
    toast("Playwright script generated", "success");
  } catch (error) {
    setRunState("Generation failed", "danger");
    setOutput(qs("#script-output"), error.message);
    toast(error.message, "danger");
  }
}

async function executeScenario(event) {
  event.preventDefault();
  setRunState("Running", "primary", true);
  qs("#execute-btn").disabled = true;
  setOutput(qs("#execution-output"), "Starting browser session and executing scenario...");

  try {
    const data = await postJson("/execute-feature", {
      url: qs("#target-url").value,
      gherkin_text: qs("#gherkin-input").value,
      feature_name: qs("#feature-name").value,
      scenario_name: qs("#scenario-name").value
    });
    setOutput(qs("#execution-output"), data);
    setRunState(data.summary.failed_steps ? "Completed with failures" : "Passed", data.summary.failed_steps ? "danger" : "success");
    toast("Pipeline completed and report saved", data.summary.failed_steps ? "warning" : "success");
    await loadReports();
  } catch (error) {
    setRunState("Run failed", "danger");
    setOutput(qs("#execution-output"), error.message);
    toast(error.message, "danger");
  } finally {
    qs("#execute-btn").disabled = false;
    qs("#run-loader").classList.add("d-none");
  }
}

function slugify(value) {
  return String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "generated-test";
}

async function postJson(path, payload) {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed with ${response.status}`);
  }
  return data;
}

function initScreenshots() {
  const zone = qs("#upload-zone");
  const fileInput = qs("#screenshot-file");

  zone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => setScreenshotFile(fileInput.files[0]));

  ["dragenter", "dragover"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.remove("dragover");
    });
  });

  zone.addEventListener("drop", (event) => setScreenshotFile(event.dataTransfer.files[0]));
  qs("#screenshot-form").addEventListener("submit", analyzeScreenshot);
}

function setScreenshotFile(file) {
  if (!file) return;
  state.selectedFile = file;
  const preview = qs("#screenshot-preview");
  preview.src = URL.createObjectURL(file);
  preview.style.display = "block";
  qs("#empty-preview").style.display = "none";
  qs("#upload-zone strong").textContent = file.name;
  qs("#upload-zone span").textContent = `${Math.round(file.size / 1024)} KB selected`;
}

async function analyzeScreenshot(event) {
  event.preventDefault();
  if (!state.selectedFile) {
    toast("Choose a screenshot first", "warning");
    return;
  }

  const badge = qs("#vision-badge");
  badge.className = "badge text-bg-primary";
  badge.textContent = "Analyzing";
  setOutput(qs("#vision-output"), "Uploading screenshot and running UI detection...");

  try {
    const imageBase64 = await fileToBase64(state.selectedFile);
    const data = await postJson("/analyze-screenshot", {
      image_base64: imageBase64,
      filename: state.selectedFile.name,
      target_text: qs("#target-text").value || null,
      include_ocr: true
    });
    badge.className = "badge text-bg-success";
    badge.textContent = `${data.detection.elements.length} elements`;
    setOutput(qs("#vision-output"), data);
    toast("Screenshot analyzed", "success");
  } catch (error) {
    badge.className = "badge text-bg-danger";
    badge.textContent = "Failed";
    setOutput(qs("#vision-output"), error.message);
    toast(error.message, "danger");
  }
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function initReports() {
  qs("#refresh-reports").addEventListener("click", loadReports);
  qs("#reports-reload").addEventListener("click", loadReports);
}

async function loadReports() {
  try {
    const response = await fetch(apiUrl("/reports"));
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not load reports");
    state.reports = data.reports || [];
    renderReports();
    renderMetrics();
  } catch (error) {
    qs("#latest-reports").innerHTML = `<div class="text-muted">Reports unavailable. ${escapeHtml(error.message)}</div>`;
    qs("#reports-list").innerHTML = `<div class="text-muted">Reports unavailable. ${escapeHtml(error.message)}</div>`;
  }
}

function renderMetrics() {
  qs("#metric-total").textContent = state.reports.length;
  qs("#metric-passed").textContent = state.reports.filter((report) => report.status === "passed").length;
  qs("#metric-failed").textContent = state.reports.filter((report) => report.status === "failed").length;
  qs("#metric-plan-b").textContent = state.reports.reduce((sum, report) => sum + Number(report.plan_b_steps || 0), 0);
}

function renderReports() {
  const latest = state.reports.slice(0, 4);
  qs("#latest-reports").innerHTML = latest.length ? latest.map(reportCard).join("") : emptyReports();
  qs("#reports-list").innerHTML = state.reports.length ? state.reports.map(reportCard).join("") : emptyReports();

  qsa("[data-open-report]").forEach((button) => {
    button.addEventListener("click", () => loadReportHtml(button.dataset.openReport));
  });
}

function reportCard(report) {
  const status = report.status === "passed" ? "success" : "danger";
  return `
    <article class="report-item">
      <div>
        <h3>${escapeHtml(report.feature_name || "Untitled Feature")}</h3>
        <p>${escapeHtml(report.scenario_name || "Unnamed Scenario")} · ${formatDate(report.started_at)}</p>
        <div class="report-stats">
          <span>${escapeHtml(report.status)}</span>
          <span>${report.passed_steps}/${report.total_steps} passed</span>
          <span>Plan A ${report.plan_a_steps}</span>
          <span>Plan B ${report.plan_b_steps}</span>
        </div>
      </div>
      <div class="report-actions">
        <span class="badge text-bg-${status}">${escapeHtml(report.status)}</span>
        <button class="btn btn-sm btn-outline-primary" data-open-report="${escapeHtml(report.execution_id)}">
          <i class="bi bi-eye"></i>
        </button>
      </div>
    </article>`;
}

function emptyReports() {
  return `<div class="text-muted">No reports yet. Run a scenario to create the first report.</div>`;
}

function formatDate(value) {
  if (!value) return "Unknown date";
  return new Date(value).toLocaleString();
}

async function loadReportHtml(executionId) {
  try {
    const response = await fetch(apiUrl(`/reports/${executionId}?format=html`));
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not open report");
    const reportWindow = window.open("", "_blank");
    reportWindow.document.open();
    reportWindow.document.write(data.content);
    reportWindow.document.close();
  } catch (error) {
    toast(error.message, "danger");
  }
}
