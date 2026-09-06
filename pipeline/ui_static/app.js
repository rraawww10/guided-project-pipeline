/* Guided Project Pipeline - control and monitoring UI.
 *
 * Every value on this page comes from GET /api/... which reads the pipeline's
 * own files. There is no local timer that advances anything, no simulated
 * progress and no placeholder output: if a field is blank it is because the
 * pipeline has not recorded it yet. */

const app = document.querySelector("#app");
const banner = document.querySelector("#banner");
const titleEl = document.querySelector("#view-title");
const subEl = document.querySelector("#view-sub");
const providerLine = document.querySelector("#provider-line");
const rootLine = document.querySelector("#root-line");
const navButtons = [...document.querySelectorAll("nav button")];
const refreshButton = document.querySelector("#refresh");
const liveDot = document.querySelector("#live-dot");
const drawer = document.querySelector("#drawer");

const TITLES = {
  dashboard: ["Dashboard", "Everything the pipeline is doing right now"],
  create: ["Create Project", "Step 0 - the human gives the stack. The AI does not choose it."],
  projects: ["Projects", "Every project directory under projects/"],
  queue: ["Queue", "Projects that are ready to run but not running"],
  running: ["Running Workflows", "Live view of every workflow in flight"],
  reviews: ["Human Gates", "The only points where a person decides"],
  agents: ["Agents", "Seven agents, run against OpenRouter with their own prompt and skill"],
  scripts: ["Scripts", "Deterministic checkers - the same command a person runs in a terminal"],
  artifacts: ["Artifacts", "Files the pipeline has produced"],
  project: ["Project", ""],
};

const ICONS = {
  COMPLETED: "✓", RUNNING: "●", PENDING: "○", QUEUED: "◌",
  FAILED: "!", BLOCKED: "✗", WAITING_FOR_REVIEW: "◉",
  WAITING_FOR_INPUT: "◍", INTERRUPTED: "–", IDLE: "○",
  SUCCEEDED: "✓", APPROVED: "✓", REJECTED: "!", TOTAL: "Σ", "NOT REACHED": "○",
};

let view = "dashboard";
let overview = null;
let detail = null;
let slug = null;
let eventSeq = 0;
let poller = null;
let overviewPoller = null;
let uploads = [];
let draft = {
  slug: "", flow: "2", stack: "", sessions: "3", minutes: "40",
  track: "fullstack", limits: "", by: "", idea: "",
};
let openArtifact = null;
let artifactFilter = "";
let target = null;          // which project the Agents/Scripts pages act on

/* ---------------------------------------------------------------- helpers */
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function cls(value) {
  return String(value || "pending").toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
function pretty(value) {
  return String(value || "").replace(/_/g, " ").toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());
}
function chip(value) {
  const v = String(value || "PENDING").toUpperCase();
  return `<span class="status ${cls(v)}"><i>${ICONS[v] || "○"}</i>${esc(pretty(v))}</span>`;
}
function bar(pct, label) {
  const n = Math.max(0, Math.min(100, Math.round(Number(pct) || 0)));
  return `<div class="progress" title="${n}%"><div class="bar" style="width:${n}%"></div>
    <span>${esc(label || n + "%")}</span></div>`;
}
function time(value) {
  if (!value && value !== 0) return "";
  if (typeof value === "number") return new Date(value * 1000).toLocaleTimeString();
  const d = new Date(value);
  return isNaN(d) ? String(value) : d.toLocaleString();
}
function clock(value) {
  if (!value && value !== 0) return "";
  const d = typeof value === "number" ? new Date(value * 1000) : new Date(value);
  return isNaN(d) ? String(value).slice(11, 19) : d.toLocaleTimeString();
}
function elapsed(seconds) {
  if (seconds === null || seconds === undefined || seconds === "") return "";
  const n = Math.max(0, Math.round(Number(seconds) || 0));
  if (n < 60) return `${n}s`;
  const m = Math.floor(n / 60);
  return m < 60 ? `${m}m ${n % 60}s` : `${Math.floor(m / 60)}h ${m % 60}m`;
}
function bytes(n) {
  const v = Number(n) || 0;
  if (v < 1024) return `${v} B`;
  if (v < 1024 * 1024) return `${(v / 1024).toFixed(1)} KB`;
  return `${(v / 1048576).toFixed(1)} MB`;
}
function pre(text, extra = "") {
  const t = String(text || "").trim();
  return t ? `<pre class="${extra}">${esc(t)}</pre>` : "";
}
function field(label, value, extra = "") {
  return `<div class="field ${extra}"><span>${esc(label)}</span><strong>${
    value === "" || value === null || value === undefined
      ? '<em class="muted">not recorded</em>' : value}</strong></div>`;
}
function empty(text) {
  return `<div class="empty">${esc(text)}</div>`;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "content-type": "application/json" }, ...options,
  });
  let data;
  try { data = await res.json(); } catch { data = {}; }
  if (!res.ok) throw new Error(data.error || `${res.status} ${res.statusText}`);
  return data;
}
function say(message, kind = "error") {
  banner.innerHTML = `<div class="banner ${kind}"><span>${esc(message)}</span>
    <button class="link" data-dismiss>dismiss</button></div>`;
  banner.querySelector("[data-dismiss]").onclick = () => (banner.innerHTML = "");
  if (kind !== "error") setTimeout(() => (banner.innerHTML = ""), 6000);
}

/* -------------------------------------------------------------- data load */
async function loadOverview(rerender = true) {
  overview = await api("/api/overview");
  const or = overview.openrouter;
  providerLine.textContent = or.available
    ? `OpenRouter - ${or.model}` : "OPENROUTER_API_KEY not set";
  providerLine.className = or.available ? "muted" : "muted warn";
  rootLine.textContent = overview.root;
  if (rerender) render();
}
async function loadDetail(rerender = true) {
  detail = await api(`/api/projects/${encodeURIComponent(slug)}`);
  eventSeq = detail.event_seq || 0;
  if (rerender) render();
}

function setView(next, projectSlug) {
  view = next;
  openArtifact = null;
  if (projectSlug) slug = projectSlug;
  navButtons.forEach(b => b.classList.toggle("active", b.dataset.view === view));
  render();
  if (view === "project") loadDetail().catch(e => say(e.message));
}

/* ---------------------------------------------------------------- routing */
function render() {
  const [t, s] = TITLES[view] || TITLES.dashboard;
  titleEl.textContent = view === "project" ? (slug || "Project") : t;
  subEl.textContent = view === "project"
    ? "The live window into one workflow" : s;
  if (!overview) { app.innerHTML = empty("Loading"); return; }
  const views = {
    dashboard: viewDashboard, create: viewCreate, projects: viewProjects,
    queue: viewQueue, running: viewRunning, reviews: viewReviews,
    agents: viewAgents, scripts: viewScripts, artifacts: viewArtifacts,
    project: viewProject,
  };
  app.innerHTML = (views[view] || viewDashboard)();
  wire(app);
  schedulePolling();
}

/* -------------------------------------------------------------- dashboard */
function viewDashboard() {
  const c = overview.counts;
  const order = ["TOTAL", "RUNNING", "QUEUED", "WAITING_FOR_REVIEW", "WAITING_FOR_INPUT",
                 "COMPLETED", "FAILED", "BLOCKED"];
  return `
  <div class="grid cols-4 stats">
    ${order.map(k => `<div class="stat ${cls(k)}"><span>${esc(pretty(k))}</span>
      <strong>${c[k] || 0}</strong></div>`).join("")}
  </div>
  <div class="grid cols-2">
    <div class="panel">
      <h2>Workflows in flight</h2>
      ${overview.running.length ? overview.running.map(liveCard).join("")
        : empty("Nothing is running. Open a project and press Start Workflow.")}
    </div>
    <div class="panel">
      <h2>Waiting for a person</h2>
      ${overview.reviews.length
        ? overview.reviews.map(r => `<div class="mini">
            <div><strong>${esc(r.project)}</strong> ${chip(r.status.toUpperCase())}</div>
            <div class="muted">${esc(r.title)}</div>
            <button class="button small" data-open="${esc(r.project)}">Open</button>
          </div>`).join("")
        : empty("No gate is waiting.")}
      ${overview.queued.filter(p => p.status === "WAITING_FOR_INPUT").map(p => `
        <div class="mini"><div><strong>${esc(p.slug)}</strong> ${chip(p.status)}</div>
        <div class="muted">${esc(p.step_description || "")}</div>
        <button class="button small" data-open="${esc(p.slug)}">Open</button></div>`).join("")}
    </div>
  </div>
  <div class="panel">
    <h2>All projects</h2>
    ${projectTable(overview.projects)}
  </div>
  <div class="panel">
    <h2>Recent events</h2>
    ${eventTable(overview.activity, true)}
  </div>`;
}

function liveCard(p) {
  return `<div class="live-card">
    <div class="live-head">
      <strong>${esc(p.slug)}</strong>${chip(p.status)}
    </div>
    <div class="muted">${esc(p.phase_title || p.phase || "")} - step ${
      p.step ?? "-"}: ${esc(p.step_description || "")}</div>
    <div class="muted">Component: <code>${esc(p.current_component || "-")}</code>
      (${esc(p.current_kind || "-")})</div>
    ${bar(p.progress, `${p.completed_actions}/${p.total_actions} actions`)}
    <button class="button small" data-open="${esc(p.slug)}">Open Workflow</button>
  </div>`;
}

function projectTable(list) {
  if (!list.length) return empty("No projects yet.");
  return `<table class="table">
    <thead><tr><th>Project</th><th>Flow</th><th>Status</th><th>Phase</th>
      <th>Step</th><th>Next</th><th>Progress</th><th>Retries</th><th></th></tr></thead>
    <tbody>${list.map(p => `<tr>
      <td><button class="link" data-open="${esc(p.slug)}">${esc(p.slug)}</button>
        <div class="muted">${esc(p.stack || "no stack recorded")}</div></td>
      <td>${p.flow}</td>
      <td>${chip(p.status)}</td>
      <td>${esc(p.phase_title || p.phase || "")}</td>
      <td>${p.step ?? "-"}</td>
      <td><code>${esc(p.current_component || "-")}</code></td>
      <td>${bar(p.progress, `${p.completed_actions}/${p.total_actions}`)}</td>
      <td>${p.retry_count}/${p.retry_limit}</td>
      <td><button class="button small" data-open="${esc(p.slug)}">Open</button></td>
    </tr>`).join("")}</tbody></table>`;
}

/* ------------------------------------------------------------------ create */
function viewCreate() {
  const flow1 = draft.flow === "1";
  return `<div class="panel narrow">
    <h2>New guided project</h2>
    <p class="muted">Flow 2 is the current 16-step design with four gates. Flow 1 is
      the original 12 steps and three gates, kept for the projects already shipped
      under it.</p>
    <form id="create-form" class="form-grid">
      <label>Project slug<input name="slug" value="${esc(draft.slug)}"
        placeholder="budget-planner" required></label>
      <label>Flow<select name="flow">
        <option value="2"${flow1 ? "" : " selected"}>Flow 2 - 16 steps, 4 gates (default)</option>
        <option value="1"${flow1 ? " selected" : ""}>Flow 1 - 12 steps, 3 gates</option>
      </select></label>
      ${flow1 ? `
      <label class="span-2">The one-page idea (step 1 is a person, in flow 1)
        <textarea name="idea" rows="10" placeholder="Theme, scope, sessions, stack. One page."
        >${esc(draft.idea)}</textarea></label>`
      : `
      <label class="span-2">Tech stack - comma separated. The human gives the stack.
        <input name="stack" value="${esc(draft.stack)}"
          placeholder="next, react, typescript" required></label>
      <label>Sessions<input name="sessions" type="number" min="1" max="12"
        value="${esc(draft.sessions)}"></label>
      <label>Minutes per session<input name="minutes" type="number" min="10" max="240"
        value="${esc(draft.minutes)}"></label>
      <label>Track<input name="track" value="${esc(draft.track)}"></label>
      <label>Given by<input name="by" value="${esc(draft.by)}" placeholder="your name"></label>
      <label class="span-2">Limits - anything the ideas must respect
        <input name="limits" value="${esc(draft.limits)}"
          placeholder="no database, no API key at run time"></label>`}
      <label class="span-2">Reference material (optional) - stored in
        <code>projects/&lt;slug&gt;/uploads/</code>
        <input type="file" id="uploads" multiple></label>
      <div id="upload-list" class="span-2"></div>
      <div class="actions span-2">
        <button class="button primary" type="submit" data-start="1">Create and Start Workflow</button>
        <button class="button" type="submit" data-start="">Create Only</button>
      </div>
    </form>
  </div>`;
}

/* ---------------------------------------------------------------- lists */
function viewProjects() {
  return `<div class="panel">${projectTable(overview.projects)}</div>`;
}

function viewQueue() {
  const queue = overview.queued;
  const running = overview.running;
  return `
  <div class="panel">
    <h2>Queued - ready to run, not running</h2>
    ${queue.length ? `<table class="table">
      <thead><tr><th>Position</th><th>Project</th><th>Status</th><th>Waiting on</th><th></th></tr></thead>
      <tbody>${queue.map((p, i) => `<tr>
        <td>${i + 1}</td>
        <td><button class="link" data-open="${esc(p.slug)}">${esc(p.slug)}</button></td>
        <td>${chip(p.status)}</td>
        <td><code>${esc(p.current_component || "-")}</code>
          <div class="muted">${esc(p.step_description || "")}</div></td>
        <td>${p.status === "WAITING_FOR_INPUT"
          ? `<button class="button small" data-open="${esc(p.slug)}">Give input</button>`
          : `<button class="button small" data-start-workflow="${esc(p.slug)}">Start</button>`}</td>
      </tr>`).join("")}</tbody></table>` : empty("The queue is empty.")}
  </div>
  <div class="panel">
    <h2>Running now</h2>
    ${running.length ? running.map(liveCard).join("")
      : empty("Nothing is running - a project leaves the queue and appears here when it starts.")}
  </div>
  <div class="panel">
    <h2>Waiting for review</h2>
    ${overview.review.length ? projectTable(overview.review)
      : empty("No project is paused at a gate.")}
  </div>`;
}

function viewRunning() {
  const running = overview.running;
  if (!running.length) {
    return `<div class="panel">${empty(
      "No workflow is running. Open a project and press Start Workflow - the phases, " +
      "the agent or script in flight and the event log all update here as it goes.")}</div>`;
  }
  return `<div class="grid cols-2">${running.map(p => `
    <div class="panel">
      <div class="live-head"><h2>${esc(p.slug)}</h2>${chip(p.status)}</div>
      ${field("Phase", esc(p.phase_title || p.phase))}
      ${field("Step", `${p.step ?? "-"} - ${esc(p.step_description || "")}`)}
      ${field("Component", `<code>${esc(p.current_component || "-")}</code> (${esc(p.current_kind || "")})`)}
      ${field("Retries", `${p.retry_count} / ${p.retry_limit}`)}
      ${bar(p.progress, `${p.completed_actions} of ${p.total_actions} actions done`)}
      <div class="actions">
        <button class="button primary" data-open="${esc(p.slug)}">Open Workflow</button>
        <button class="button" data-pause-workflow="${esc(p.slug)}">Pause</button>
      </div>
    </div>`).join("")}</div>`;
}

function viewReviews() {
  const waiting = overview.reviews.filter(r => r.waiting);
  const rest = overview.reviews.filter(r => !r.waiting);
  return `<div class="panel">
    <h2>Waiting for a decision</h2>
    ${waiting.length ? waiting.map(r => gatePanel(r, r.project)).join("")
      : empty("No gate is waiting for a decision.")}
  </div>
  ${rest.length ? `<div class="panel"><h2>Other gates</h2>
    ${rest.map(r => `<div class="mini"><strong>${esc(r.project)}</strong>
      ${chip(r.status.toUpperCase())} ${esc(r.title)}</div>`).join("")}</div>` : ""}`;
}

/* --------------------------------------------------------- agents/scripts */
function targetPicker(note) {
  const list = overview.projects;
  if (!list.length) return "";
  if (!target || !list.some(p => p.slug === target)) target = slug || list[0].slug;
  return `<div class="panel"><label class="inline">Run against project
    <select id="target-project">${list.map(p => `<option value="${esc(p.slug)}"${
      p.slug === target ? " selected" : ""}>${esc(p.slug)} - ${esc(p.status)}</option>`
    ).join("")}</select></label>
    <p class="muted">${esc(note)}</p></div>`;
}

function viewAgents() {
  const or = overview.openrouter;
  return `
  ${or.available ? "" : `<div class="panel warn-panel">OPENROUTER_API_KEY is not set,
    so agent steps cannot start from this UI. Put it in <code>.env</code> and restart,
    or run the phase from Claude Code with its <code>/workflow</code> command.</div>`}
  ${targetPicker("Running an agent here runs it for real, out of the workflow's order. " +
    "The orchestrator on the project page is the normal way; this is for repairing one step.")}
  <div class="grid cols-2">
  ${overview.agents.map(a => `<div class="panel agent-card ${cls(a.status)}">
    <div class="live-head"><h2>${esc(a.name)}</h2>${chip(a.status)}</div>
    <p class="muted">${esc(a.purpose)}</p>
    ${field("Type", esc(a.type))}
    ${field("Phase", `${esc(a.phase_title)} (${esc(a.phase)})`)}
    ${field("LLM provider", esc(a.provider))}
    ${field("Model", `<code>${esc(a.model)}</code>`)}
    ${field("Current project", a.project ? `<button class="link" data-open="${
      esc(a.project)}">${esc(a.project)}</button>` : "")}
    ${field("Attempt", a.attempt ?? "")}
    ${field("Started", a.started ? time(a.started) : "")}
    ${field("Last execution", a.finished ? time(a.finished) : "")}
    ${field("Duration", a.duration ? `${a.duration}s` : "")}
    ${field("Runs recorded", a.runs)}
    ${field("Phase retries", `${a.retry_count} / ${a.retry_limit}`)}
    ${field("Prompt", `<code>${esc(a.prompt_path)}</code>`)}
    <div class="out-label">Latest output</div>
    ${a.output ? pre(a.output, "scroll") : empty("This agent has not run from the UI yet.")}
    <div class="actions">
      <button class="button small" data-run-agent="${esc(a.name)}" data-target="1"
        ${or.available ? "" : "disabled"}>Run ${esc(a.name)}</button>
      ${a.run_id ? `<button class="button small ghost" data-run-log="${
        esc(a.run_id)}">View full run</button>` : ""}
    </div>
  </div>`).join("")}</div>`;
}

function viewScripts() {
  return `
  ${targetPicker("Every one of these is the same command a person runs in a terminal.")}
  <div class="grid cols-2">
  ${overview.scripts.map(s => `<div class="panel script-card ${cls(s.status)}">
    <div class="live-head"><h2>${esc(s.label)}</h2>${chip(s.status)}</div>
    <p class="muted">${esc(s.purpose)}</p>
    ${field("Type", esc(s.type))}
    ${field("Phase", esc(s.phase))}
    ${field("Command", `<code>${esc(s.command)}</code>`)}
    ${field("Project", s.project ? `<button class="link" data-open="${
      esc(s.project)}">${esc(s.project)}</button>` : "")}
    ${field("Started", s.started ? time(s.started) : "")}
    ${field("Finished", s.finished ? time(s.finished) : "")}
    ${field("Duration", s.duration ? `${s.duration}s` : "")}
    ${field("Exit code", s.returncode === null || s.returncode === undefined ? "" : s.returncode)}
    ${field("Result", s.result ? esc(s.result) : "")}
    ${s.output ? `<div class="out-label">Output</div>${pre(s.output, "scroll")}` : ""}
    ${s.error ? `<div class="out-label">stderr</div>${pre(s.error, "scroll bad")}` : ""}
    <div class="actions">
      <button class="button small" data-run-script="${esc(s.name)}" data-target="1">Run</button>
      ${s.run_id ? `<button class="button small ghost" data-run-log="${
        esc(s.run_id)}">View full run</button>` : ""}
    </div>
  </div>`).join("")}</div>`;
}

/* -------------------------------------------------------------- artifacts */
function viewArtifacts() {
  const list = overview.projects;
  if (!list.length) return `<div class="panel">${empty("No projects yet.")}</div>`;
  const chosen = list.some(p => p.slug === slug) ? slug : list[0].slug;
  return `<div class="panel">
    <label>Project<select id="artifact-project">
      ${list.map(p => `<option value="${esc(p.slug)}"${
        p.slug === chosen ? " selected" : ""}>${esc(p.slug)}</option>`).join("")}
    </select></label>
    <div id="artifact-body">${empty("Choose a project.")}</div>
  </div>`;
}

/* -------------------------------------------------- the project workflow page */
function viewProject() {
  if (!detail || detail.slug !== slug) return empty("Loading project");
  return `
  <div id="pd-header">${projectHeader()}</div>
  <div id="pd-controls">${projectControls()}</div>
  <div id="pd-error">${errorPanel()}</div>
  <div id="pd-timeline">${timelinePanel()}</div>
  <div class="grid cols-2 top">
    <div id="pd-current">${currentPanel()}</div>
    <div id="pd-gate">${gateSection()}</div>
  </div>
  <div class="grid cols-2">
    <div class="panel events-panel">
      <div class="live-head"><h2>Workflow events</h2>
        <span class="muted" id="pd-event-count">${detail.events.length} recorded</span></div>
      <div id="pd-events" class="events">${eventLog(detail.events)}</div>
    </div>
    <div class="panel">
      <h2>Runs</h2>
      <div id="pd-runs">${runList(detail.runs)}</div>
    </div>
  </div>
  <div id="pd-preview">${previewPanel()}</div>
  <div id="pd-steps">${stepPanel()}</div>
  <div class="panel">
    <div class="live-head"><h2>Artifacts</h2>
      <span class="muted">${detail.artifacts.length} files under projects/${esc(slug)}/</span></div>
    <input id="artifact-filter" placeholder="filter by path" value="${esc(artifactFilter)}">
    <div id="pd-artifacts">${artifactTable(detail.artifacts)}</div>
  </div>
  <div id="pd-viewer">${artifactViewer()}</div>
  <div class="panel">
    <h2>Human records</h2>
    ${humanForms()}
  </div>`;
}

function projectHeader() {
  const d = detail;
  return `<div class="panel header-panel">
    <div class="live-head">
      <div>
        <h2>${esc(d.slug)} ${chip(d.status)}</h2>
        <p class="muted">${esc(d.stack || "no stack recorded")}${
          d.sessions ? ` - ${d.sessions} sessions x ${d.minutes} min` : ""}</p>
      </div>
      ${bar(d.progress, `${d.completed_actions} of ${d.total_actions} actions`)}
    </div>
    <div class="field-row">
      ${field("Flow", `${d.flow} (${d.flow === 2 ? "16 steps, 4 gates" : "12 steps, 3 gates"})`)}
      ${field("Created", time(d.created))}
      ${field("Phase", esc(d.phase_title || d.phase || ""))}
      ${field("Track", esc(d.track || ""))}
      ${field("Spec frozen", d.spec_frozen ? "yes - Gate 1 approved it" : "no")}
      ${field("Shipped", d.shipped ? "yes" : "no")}
    </div>
  </div>`;
}

// The built project, served so a person can look at it. deploy_check builds and
// serves too, but tears the server down the moment its check passes - the URL in
// deploy.json answers nothing by the time anyone reads it.
function previewPanel() {
  const pv = detail.preview || {};
  const slug = esc(detail.slug);
  const has = (detail.artifacts || []).some(a => a.path.startsWith("app/"));
  const hasSkeleton = (detail.artifacts || []).some(a => a.path.startsWith("skeleton/"));
  if (!has && !hasSkeleton) return "";
  const starting = pv.running && pv.status === "starting";
  return `<div class="panel">
    <div class="live-head"><h2>Preview</h2>${
      pv.status ? chip(pv.status.toUpperCase()) : ""}</div>
    <p class="muted">Installs, builds and serves the project, the same way the
      test runner does. First start takes a minute or so.</p>
    <div class="control-row">
      <button class="button primary" data-preview-start="${slug}" data-preview-target="app"
        ${!has || pv.running ? "disabled" : ""}>${
        starting && pv.target === "app" ? "Building..." : "Preview app"}</button>
      <button class="button" data-preview-start="${slug}" data-preview-target="skeleton"
        ${!hasSkeleton || pv.running ? "disabled" : ""}>${
        starting && pv.target === "skeleton" ? "Building..." : "Preview skeleton"}</button>
      <button class="button ghost" data-preview-stop="${slug}"
        ${pv.running ? "" : "disabled"}>Stop</button>
    </div>
    ${pv.url ? `<div class="reason completed">Serving <code>${esc(pv.target)}/</code> at
      <a href="${esc(pv.url)}" target="_blank" rel="noopener">${esc(pv.url)}</a>
      - it stops when you press Stop or the UI shuts down.</div>` : ""}
    ${starting ? `<div class="reason">Building <code>${esc(pv.target)}/</code> -
      the link appears here when it answers.</div>` : ""}
    ${pv.error ? `<div class="reason">${esc(pv.error)}</div>` : ""}
    ${!has ? `<div class="muted">No app/ yet - the Builder has not run.</div>` : ""}
  </div>`;
}

function projectControls() {
  const d = detail;
  const wf = d.workflow || {};
  const running = d.status === "RUNNING";
  const done = d.status === "COMPLETED";
  const next = d.repair || d.next_action;
  const canAuto = next && (next.kind === "agent" || next.kind === "script");
  return `<div class="panel control-panel">
    <div class="control-row">
      <button class="button primary" data-start-workflow="${esc(d.slug)}"
        ${running || done || !canAuto ? "disabled" : ""}>
        ${wf.state === "paused" || wf.state === "waiting_review" ? "Resume Workflow" : "Start Workflow"}</button>
      <button class="button" data-step-workflow="${esc(d.slug)}"
        ${running || done || !canAuto ? "disabled" : ""}>Run Next Step Only</button>
      <button class="button" data-pause-workflow="${esc(d.slug)}"
        ${running && !wf.stop_requested ? "" : "disabled"}>${
        wf.stop_requested && running ? "Pausing..." : "Pause"}</button>
      <button class="button ghost" data-refresh-project="${esc(d.slug)}">Refresh Status</button>
      <span class="spacer"></span>
      <span class="muted">orchestrator: <strong>${esc(pretty(wf.state || "idle"))}</strong></span>
    </div>
    ${wf.stop_requested && running ? `<div class="reason waiting">Pause requested.
      The orchestrator stops as soon as the action in flight finishes - it does not
      kill a running agent or checker mid-way.</div>` : ""}
    ${wf.reason ? `<div class="reason ${cls(wf.state)}">${esc(wf.reason)}</div>` : ""}
    ${!canAuto && next ? `<div class="reason waiting">Next is
      <strong>${esc(next.label)}</strong> - ${esc(next.note || next.description || "")}.
      That is a person's decision, so the Start button stays off until it is made.</div>` : ""}
    ${done ? `<div class="reason completed">The workflow is complete. Every artifact is
      listed below.</div>` : ""}
  </div>`;
}

function errorPanel() {
  const t = detail.state.ticket;
  const wf = detail.workflow || {};
  const failedRuns = (detail.runs || []).filter(r => r.status === "failed").slice(0, 1);
  if (!t && wf.state !== "blocked" && !failedRuns.length && !detail.repair) return "";
  const r = failedRuns[0];
  return `<div class="panel fail-panel">
    <h2>! Attention</h2>
    ${t ? `
      ${field("Ticket raised", time(t.raised))}
      ${field("Phase", esc(t.phase))}
      ${field("Kind", esc(t.kind || "code problem"))}
      ${field("Retries burned", `${t.retries} / ${detail.retry_limit}`)}
      ${field("Re-enters at step", t.re_enter_at)}
      <div class="out-label">Last error</div>${pre(t.last_error)}
      <p class="muted">Rule 6: the run stops at ${detail.retry_limit} retries and a
        person fixes it between steps. Nothing in this UI clears a ticket.</p>` : ""}
    ${wf.state === "blocked" ? `<div class="out-label">The orchestrator stopped</div>
      ${pre(wf.reason)}` : ""}
    ${detail.repair ? (() => {
      const exhausted = t || detail.retry_count >= detail.retry_limit;
      return `
      ${field("Red report", `<code>${esc(detail.repair.repair_of)}</code>`)}
      ${field("Goes back to", `<code>${esc(detail.repair.component)}</code> (${
        esc(detail.repair.kind)})`)}
      ${field("Why", esc(detail.repair.note))}
      ${field("Phase retries", `${detail.retry_count} / ${detail.retry_limit}`)}
      ${field("Then re-run", (detail.repair.then || []).map(x =>
        `<code>${esc(x)}</code>`).join(" ") || "")}
      <div class="actions">
        <button class="button" data-run-${esc(detail.repair.kind)}="${
          esc(detail.repair.component)}" data-repair="${esc(detail.repair.repair_of)}"
          ${exhausted ? "disabled" : ""}>Re-run ${esc(detail.repair.label)}</button>
        <button class="button ghost" data-artifact="${esc(detail.repair.repair_of)}"
          >View ${esc(detail.repair.repair_of)}</button>
      </div>
      ${exhausted ? `<div class="reason blocked">Retrying is off: this phase is at
        ${detail.retry_count}/${detail.retry_limit}. Rule 6 stops the run there and a
        person fixes it between steps.</div>` : ""}`;
    })() : ""}
    ${r ? `<div class="out-label">Last failed run - ${esc(r.label)} at ${time(r.started)}</div>
      ${pre((r.stderr || r.stdout || "").slice(-2500), "bad scroll")}
      <button class="button small" data-run-log="${esc(r.id)}">View full run</button>` : ""}
  </div>`;
}

function timelinePanel() {
  const phases = detail.phases || [];
  const cur = detail.current_execution || {};
  const doneCount = phases.filter(p => p.status === "COMPLETED").length;
  const pct = phases.length ? Math.round((doneCount / phases.length) * 100) : 0;
  return `<div class="panel timeline-panel">
    <h2>Workflow progress</h2>
    <div class="timeline">
      ${phases.map(p => `<div class="phase ${cls(p.status)}">
        <div class="phase-icon">${ICONS[p.status] || "○"}</div>
        <strong>${esc(p.title)}</strong>
        <span class="muted">${esc(pretty(p.status))}</span>
        <span class="muted">${p.completed_steps}/${p.total_steps} steps</span>
        ${p.retry_count ? `<span class="muted">retries ${p.retry_count}/${p.retry_limit}</span>` : ""}
      </div>`).join('<div class="phase-link"></div>')}
    </div>
    <div class="rail"><div class="rail-fill" style="width:${pct}%"></div></div>
    <div class="phase-current">
      <div>
        <span class="muted">Current phase</span>
        <strong>${esc(cur.phase_title || cur.phase || "-")}</strong>
      </div>
      <div>
        <span class="muted">Current step</span>
        <strong>${cur.step ?? "-"} - ${esc(cur.step_description || "")}</strong>
      </div>
      <div>
        <span class="muted">${esc(pretty(cur.kind || "component"))}</span>
        <strong><code>${esc(cur.component_label || cur.component || "-")}</code></strong>
      </div>
      <div>
        <span class="muted">Status</span>
        <strong>${chip(cur.status)}</strong>
      </div>
      <div>
        <span class="muted">Retry</span>
        <strong>${cur.retry_count} / ${cur.retry_limit}</strong>
      </div>
    </div>
  </div>`;
}

function currentPanel() {
  const c = detail.current_execution || {};
  return `<div class="panel current-panel ${cls(c.status)}">
    <div class="live-head"><h2>Current execution</h2>${chip(c.status)}</div>
    ${field("Phase", esc(c.phase_title || c.phase || ""))}
    ${field("Step", c.step === null || c.step === undefined ? "" :
      `${c.step} - ${esc(c.step_description || "")}`)}
    ${field("Component", c.component ? `<code>${esc(c.component)}</code> (${esc(c.kind || "")})` : "")}
    ${c.provider ? field("LLM provider", esc(c.provider)) : ""}
    ${c.model ? field("Model", `<code>${esc(c.model)}</code>`) : ""}
    ${field("Started", c.started_at ? time(c.started_at) : "")}
    ${field("Elapsed", elapsed(c.elapsed_seconds))}
    ${field("Attempt", c.attempt ?? "")}
    ${field("Retry", `${c.retry_count} / ${c.retry_limit}`)}
    ${field("Latest event", c.latest_event ? `${esc(c.latest_event)}
      <span class="muted">${clock(c.latest_event_at)}</span>` : "")}
    ${attemptStrip(c.component)}
    ${c.reason ? `<div class="reason">${esc(c.reason)}</div>` : ""}
    ${(() => { const f = currentPersonForm(); return f
      ? `<div class="out-label">This step needs you</div>${f}` : ""; })()}
    <div class="out-label">Live output</div>
    ${c.output ? pre(c.output, "scroll live") : empty(
      c.status === "RUNNING" ? "Waiting for the first output"
        : "Nothing is executing right now.")}
    ${c.run_id ? `<button class="button small" data-run-log="${esc(c.run_id)}">Open full log</button>` : ""}
  </div>`;
}

// Every attempt of the component in flight, oldest first, straight off the run
// ledger - so a retry reads as "attempt 1 failed, attempt 2 running".
function attemptStrip(component) {
  if (!component) return "";
  const runs = (detail.runs || [])
    .filter(r => r.component === component)
    .sort((a, b) => (a.started || 0) - (b.started || 0));
  if (runs.length < 2) return "";
  return `<div class="out-label">Attempts</div><div class="attempts">${
    runs.map(r => `<button class="attempt ${cls(r.status)}" data-run-log="${esc(r.id)}">
      <strong>Attempt ${r.attempt ?? "?"}</strong>
      <span>${esc(pretty(r.status))}</span>
      <span class="muted">${clock(r.started)}${
        r.finished ? ` - ${elapsed(r.finished - r.started)}` : ""}</span>
    </button>`).join('<span class="attempt-arrow">-></span>')}</div>`;
}

function gateSection() {
  const waiting = (detail.gates || []).filter(g => g.waiting);
  const others = (detail.gates || []).filter(g => !g.waiting);
  return `<div class="panel">
    <h2>Human gates</h2>
    ${waiting.length ? waiting.map(g => gatePanel(g, detail.slug)).join("")
      : empty("No gate is waiting right now.")}
    ${others.map(g => `<div class="mini">
      <div><strong>${esc(g.title)}</strong> ${chip(g.status.toUpperCase())}</div>
      ${g.at ? `<div class="muted">${time(g.at)}</div>` : ""}
      ${g.note ? `<div class="muted">${esc(g.note.slice(0, 300))}</div>` : ""}
      ${g.status === "not reached" && g.blockers.length ? `<details><summary class="muted"
        >${g.blockers.length} thing(s) must pass first</summary>
        <ul class="muted">${g.blockers.map(b => `<li>${esc(b)}</li>`).join("")}</ul>
        </details>` : ""}
    </div>`).join("")}
  </div>`;
}

function gatePanel(g, project) {
  const isPick = g.gate === "gate0";
  return `<div class="gate-panel ${g.status === "rejected" ? "rejected" : ""}">
    <div class="live-head">
      <h3>${esc(g.title)}</h3>${chip(g.status === "rejected" ? "FAILED" : "WAITING_FOR_REVIEW")}
    </div>
    <p class="muted">Project <strong>${esc(project)}</strong> - phase
      ${esc(g.phase_title)}, step ${g.step}. The workflow is paused here; nothing
      after this gate runs until a person decides. Approving records the decision
      with <code>pipeline gate</code> and resumes the run; rejecting records it and
      leaves the workflow stopped.</p>
    ${g.status === "rejected" ? `<div class="reason failed">This gate was rejected.
      ${esc(g.note || "")} Archive the round with <em>Revise</em> below, or fix the
      findings and approve.</div>` : ""}
    ${g.blockers.length ? `<div class="reason waiting">
      <strong>The CLI will refuse to approve until:</strong>
      <ul>${g.blockers.map(b => `<li>${esc(b)}</li>`).join("")}</ul></div>` : ""}
    ${g.findings ? `<div class="out-label">What to read</div>${pre(g.findings, "scroll")}` : ""}
    ${g.artifacts.length ? `<div class="out-label">Artifacts for this gate</div>
      <div class="chips">${g.artifacts.map(a => `<button class="chip-btn"
        data-artifact="${esc(a)}" data-artifact-project="${esc(project)}">${esc(a)}</button>`
      ).join("")}</div>` : ""}
    <form class="gate-form" data-gate="${esc(g.gate)}" data-project="${esc(project)}">
      ${isPick ? `<label>Pick an idea
        <select name="n">${(g.ideas.length ? g.ideas : []).map((f, i) =>
          `<option value="${i + 1}">${esc(f)}</option>`).join("")}</select></label>` : ""}
      <label>Comment${isPick ? "" : " (recorded in state.json)"}
        <textarea name="note" rows="3" placeholder="why"></textarea></label>
      ${g.gate === "gate1" ? `<label class="inline"><input type="checkbox" name="override">
        Override the Gate 1 stopping rule (needs a reason, and is recorded as an override)</label>` : ""}
      <div class="actions">
        <button class="button primary" data-decision="approve">${
          isPick ? "Pick This Idea" : "Approve"}</button>
        ${isPick ? "" : `<button class="button danger" data-decision="reject">Reject</button>`}
        ${g.gate === "gate1" ? `<button class="button ghost" data-revise="${esc(project)}"
          >Revise - archive the round and reset Gate 1</button>` : ""}
      </div>
    </form>
  </div>`;
}

function stepPanel() {
  return `<div class="panel">
    <h2>Every step, and what runs inside it</h2>
    ${(detail.phases || []).map(p => `<div class="step-phase">
      <div class="step-phase-head">
        <strong>${esc(p.title)}</strong>${chip(p.status)}
        <span class="muted">${p.completed_steps}/${p.total_steps} steps -
          retries ${p.retry_count}/${p.retry_limit}</span>
        ${p.workflow_command ? `<code class="muted">${esc(p.workflow_command)}</code>` : ""}
      </div>
      <div class="step-list">
        ${p.steps.map(s => `<div class="step-row ${cls(s.status)}">
          <div class="step-number">${s.number}</div>
          <div class="step-main">
            <div><strong>${esc(s.who)}</strong> ${esc(s.description)}</div>
            <div class="step-actions">
              ${s.actions.map(a => `<span class="action-chip ${cls(a.status)}"
                title="${esc(a.kind)}">${ICONS[a.status] || "○"} ${esc(a.label)}</span>`
              ).join("")}
            </div>
            ${s.artifacts.length ? `<div class="chips">${s.artifacts.map(x =>
              `<button class="chip-btn" data-artifact="${esc(x)}">${esc(x)}</button>`
            ).join("")}</div>` : ""}
          </div>
          <div class="step-side">
            ${chip(s.status)}
            ${s.run_count ? `<span class="muted">${s.run_count} run(s)</span>` : ""}
            ${runButtons(s)}
          </div>
        </div>`).join("")}
      </div>
    </div>`).join("")}
  </div>`;
}

function runButtons(step) {
  const out = [];
  for (const a of step.actions) {
    if (a.kind === "agent") {
      out.push(`<button class="button small" data-run-agent="${esc(a.component)}"
        data-step="${step.number}">Run ${esc(a.label)}</button>`);
    } else if (a.kind === "script") {
      out.push(`<button class="button small ghost" data-run-script="${esc(a.component)}"
        data-step="${step.number}">Run ${esc(a.label)}</button>`);
    }
  }
  return out.join("");
}

function eventLog(events) {
  if (!events || !events.length) return empty("No events yet.");
  return events.map(eventRow).join("");
}
function eventRow(e) {
  return `<div class="event ${cls(e.level)}" data-seq="${e.seq}">
    <span class="event-time">${clock(e.at)}</span>
    <span class="event-kind">${esc(e.kind || "")}</span>
    <span class="event-msg">${esc(e.message)}${
      e.detail ? `<span class="muted"> - ${esc(String(e.detail).slice(0, 400))}</span>` : ""}</span>
  </div>`;
}
function eventTable(rows, withProject) {
  if (!rows || !rows.length) return empty("Nothing recorded yet.");
  return `<div class="events">${rows.map(e => `<div class="event ${cls(e.level)}">
    <span class="event-time">${clock(e.at)}</span>
    ${withProject ? `<span class="event-kind"><button class="link" data-open="${
      esc(e.project)}">${esc(e.project)}</button></span>` : ""}
    <span class="event-msg">${esc(e.message)}${
      e.detail ? `<span class="muted"> - ${esc(String(e.detail).slice(0, 200))}</span>` : ""}</span>
  </div>`).join("")}</div>`;
}

function runList(runs) {
  if (!runs || !runs.length) return empty("Nothing has been run from the UI yet.");
  return `<table class="table compact"><thead><tr><th>When</th><th>What</th>
    <th>Kind</th><th>Attempt</th><th>Status</th><th>Took</th><th></th></tr></thead>
    <tbody>${runs.map(r => `<tr class="${cls(r.status)}">
      <td>${clock(r.started)}</td>
      <td><code>${esc(r.label || r.component)}</code></td>
      <td>${esc(r.kind)}${r.auto ? ' <span class="muted">auto</span>' : ""}</td>
      <td>${r.attempt ?? ""}</td>
      <td>${chip((r.status || "").toUpperCase())}</td>
      <td>${r.finished && r.started ? elapsed(r.finished - r.started) : ""}</td>
      <td><button class="button small ghost" data-run-log="${esc(r.id)}">Log</button></td>
    </tr>`).join("")}</tbody></table>`;
}

function artifactTable(list) {
  const rows = list.filter(a => !artifactFilter ||
    a.path.toLowerCase().includes(artifactFilter.toLowerCase()));
  if (!rows.length) return empty("No artifacts match.");
  return `<table class="table compact"><thead><tr><th>Path</th><th>Kind</th>
    <th>Size</th><th>Modified</th><th></th></tr></thead><tbody>
    ${rows.slice(0, 400).map(a => `<tr>
      <td><code>${esc(a.path)}</code></td>
      <td>${esc(a.kind)}</td>
      <td>${bytes(a.size)}</td>
      <td>${a.modified ? time(a.modified) : ""}</td>
      <td>
        ${a.viewable ? `<button class="button small ghost" data-artifact="${
          esc(a.path)}">View</button>` : ""}
        <a class="button small ghost" href="/api/projects/${encodeURIComponent(slug)}/download?path=${
          encodeURIComponent(a.path)}">Download</a>
      </td></tr>`).join("")}</tbody></table>
    ${rows.length > 400 ? `<p class="muted">showing 400 of ${rows.length}</p>` : ""}`;
}

function artifactViewer() {
  if (!openArtifact) return "";
  return `<div class="panel">
    <div class="live-head"><h2>${esc(openArtifact.path)}</h2>
      <button class="button small ghost" data-close-artifact>Close</button></div>
    <p class="muted">${esc(openArtifact.kind)} - ${bytes(openArtifact.size)}${
      openArtifact.truncated ? " - truncated" : ""}</p>
    ${openArtifact.viewable ? pre(openArtifact.content, "scroll tall")
      : empty("This file is not text - use Download.")}
  </div>`;
}

function stackForm() {
  return `<form class="form-grid" data-human="stack">
      <h3 class="span-2">Step 0 - the stack</h3>
      <label class="span-2">Stack<input name="stack" placeholder="next, react, typescript" required></label>
      <label>Sessions<input name="sessions" type="number" value="3"></label>
      <label>Minutes<input name="minutes" type="number" value="40"></label>
      <label>Track<input name="track" value="fullstack"></label>
      <label>Given by<input name="by"></label>
      <label class="span-2">Limits<input name="limits"></label>
      <div class="actions span-2"><button class="button primary">Record the stack</button></div>
    </form>`;
}

function dryRunForm() {
  const d = detail;
  return `<form class="form-grid" data-human="dryrun">
      <h3 class="span-2">Step 13 - the timed dry run</h3>
      <p class="muted span-2">A person who did not build it teaches one session from the
        guide, with a timer. Gate 3 refuses without it.</p>
      <label>Session<input name="session" type="number" value="1"></label>
      <label>Minutes taken<input name="minutes" type="number" value="40"></label>
      <label>Taught by<input name="by" placeholder="not whoever built it" required></label>
      <label class="inline"><input type="checkbox" name="could_not_teach">
        Could NOT be taught from the guide alone</label>
      <label class="span-2">Note<textarea name="note" rows="2"></textarea></label>
      <div class="actions span-2"><button class="button">Record the dry run</button></div>
      ${d.state.dry_run ? `<div class="span-2 reason completed">On record:
        session ${d.state.dry_run.session}, ${d.state.dry_run.minutes} min, by
        ${esc(d.state.dry_run.by)}, taught without the code:
        ${d.state.dry_run.taught_without_the_code}</div>` : ""}
    </form>`;
}

// The form for the person step the workflow is actually waiting on, so it can be
// shown next to "this step needs a person" instead of only in a panel further
// down the page. WAITING_FOR_INPUT named the step but pointed nowhere.
function currentPersonForm() {
  const c = detail.current_execution || {};
  if (c.kind !== "person" || detail.flow !== 2) return "";
  if (c.component === "dry run") return dryRunForm();
  if (c.component === "stack input") return stackForm();
  return "";
}

function humanForms() {
  const d = detail;
  const flow2 = d.flow === 2;
  const inlined = (d.current_execution || {}).kind === "person"
    ? (d.current_execution || {}).component : "";
  return `
  ${flow2 && !d.stack && inlined !== "stack input" ? stackForm() : ""}
  ${flow2 && inlined !== "dry run" ? dryRunForm() : ""}
  <form class="form-grid" data-human="feedback">
    <h3 class="span-2">Step 15 - instructor feedback</h3>
    <p class="muted span-2">Feedback re-enters the flow at step 3.</p>
    <label>Session<input name="session" type="number"></label>
    <label>From<input name="by"></label>
    <label class="span-2">What happened<textarea name="note" rows="2" required></textarea></label>
    <div class="actions span-2"><button class="button">Record feedback</button></div>
  </form>
  ${(d.state.feedback || []).length ? `<div class="out-label">Feedback on file</div>
    ${d.state.feedback.map(f => `<div class="mini"><span class="muted">${time(f.at)}</span>
      ${esc(f.note)}</div>`).join("")}` : ""}`;
}

/* ------------------------------------------------------------------ wiring */
function wire(root) {
  root.querySelectorAll("[data-open]").forEach(b =>
    b.onclick = () => setView("project", b.dataset.open));

  root.querySelectorAll("[data-start-workflow]").forEach(b =>
    b.onclick = () => act(b, () => api(
      `/api/projects/${encodeURIComponent(b.dataset.startWorkflow)}/start`, { method: "POST" })));
  root.querySelectorAll("[data-step-workflow]").forEach(b =>
    b.onclick = () => act(b, () => api(
      `/api/projects/${encodeURIComponent(b.dataset.stepWorkflow)}/step`, { method: "POST" })));
  root.querySelectorAll("[data-pause-workflow]").forEach(b =>
    b.onclick = () => act(b, () => api(
      `/api/projects/${encodeURIComponent(b.dataset.pauseWorkflow)}/pause`, { method: "POST" })));
  root.querySelectorAll("[data-preview-start]").forEach(b =>
    b.onclick = () => act(b, async () => {
      await api(`/api/projects/${encodeURIComponent(b.dataset.previewStart)}/preview`,
        { method: "POST", body: JSON.stringify({ action: "start", target: b.dataset.previewTarget }) });
      await loadDetail();
    }));
  root.querySelectorAll("[data-preview-stop]").forEach(b =>
    b.onclick = () => act(b, async () => {
      await api(`/api/projects/${encodeURIComponent(b.dataset.previewStop)}/preview`,
        { method: "POST", body: JSON.stringify({ action: "stop" }) });
      await loadDetail();
    }));
  root.querySelectorAll("[data-refresh-project]").forEach(b =>
    b.onclick = () => act(b, async () => { await loadDetail(); }));

  root.querySelectorAll("[data-run-agent]").forEach(b =>
    b.onclick = () => act(b, () => api("/api/run", {
      method: "POST",
      body: JSON.stringify({
        action: "agent", agent: b.dataset.runAgent,
        slug: b.dataset.target ? target : slug,
        step: Number(b.dataset.step) || null, repair_of: b.dataset.repair || "",
      }),
    })));
  root.querySelectorAll("[data-run-script]").forEach(b =>
    b.onclick = () => act(b, () => api("/api/run", {
      method: "POST",
      body: JSON.stringify({
        action: "script", script: b.dataset.runScript,
        slug: b.dataset.target ? target : slug,
        step: Number(b.dataset.step) || null,
      }),
    })));

  root.querySelectorAll("[data-run-log]").forEach(b =>
    b.onclick = () => showRunLog(b.dataset.runLog));

  root.querySelectorAll("[data-artifact]").forEach(b =>
    b.onclick = () => viewArtifact(b.dataset.artifactProject || slug, b.dataset.artifact));
  root.querySelectorAll("[data-close-artifact]").forEach(b =>
    b.onclick = () => { openArtifact = null; patch("pd-viewer", artifactViewer()); });

  root.querySelectorAll("[data-revise]").forEach(b =>
    b.onclick = ev => {
      ev.preventDefault();
      act(b, () => api("/api/run", {
        method: "POST", body: JSON.stringify({ action: "revise", slug: b.dataset.revise }),
      }));
    });

  root.querySelectorAll("form.gate-form").forEach(form => {
    form.querySelectorAll("[data-decision]").forEach(btn =>
      btn.onclick = ev => {
        ev.preventDefault();
        submitGate(form, btn.dataset.decision, btn);
      });
  });

  root.querySelectorAll("form[data-human]").forEach(form =>
    form.onsubmit = ev => { ev.preventDefault(); submitHuman(form); });

  const createForm = root.querySelector("#create-form");
  if (createForm) {
    createForm.querySelectorAll("[name]").forEach(f => {
      const sync = () => {
        draft[f.name] = f.type === "checkbox" ? f.checked : f.value;
        if (f.name === "flow") render();
      };
      f.oninput = sync;
      f.onchange = sync;
    });
    createForm.querySelectorAll("button[type=submit]").forEach(b =>
      b.onclick = ev => { ev.preventDefault(); submitCreate(!!b.dataset.start, b); });
    const fileInput = root.querySelector("#uploads");
    if (fileInput) fileInput.onchange = () => readUploads(fileInput);
    renderUploads();
  }

  const filter = root.querySelector("#artifact-filter");
  if (filter) {
    filter.oninput = () => {
      artifactFilter = filter.value;
      patch("pd-artifacts", artifactTable(detail.artifacts));
    };
  }
  const events = root.querySelector("#pd-events");
  if (events) events.scrollTop = events.scrollHeight;

  const picker = root.querySelector("#target-project");
  if (picker) picker.onchange = () => { target = picker.value; };

  const chooser = root.querySelector("#artifact-project");
  if (chooser) {
    chooser.onchange = () => loadArtifactsFor(chooser.value);
    loadArtifactsFor(chooser.value);
  }
}

function patch(id, html) {
  const node = document.getElementById(id);
  if (!node) return;
  // Never redraw a panel someone is typing into. Background polling patches
  // pd-current every few seconds, and a person-step form now lives there - a
  // redraw mid-sentence would silently discard what had been entered, and the
  // person would have no idea why the field emptied.
  const focused = document.activeElement;
  if (focused && node.contains(focused) && focused.closest("form")) return;
  node.innerHTML = html;
  wire(node);
}

async function act(button, work) {
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "Working...";
  try {
    const result = await work();
    if (result && result.error) throw new Error(result.error);
    say(result && result.reason ? result.reason : "Started", "ok");
    if (view === "project") await loadDetail();
    else await loadOverview();
  } catch (err) {
    say(err.message);
    button.disabled = false;
    button.textContent = label;
    return;
  }
  button.disabled = false;
  button.textContent = label;
}

async function submitGate(form, decision, button) {
  const data = Object.fromEntries(new FormData(form).entries());
  const gate = form.dataset.gate;
  const project = form.dataset.project;
  const payload = gate === "gate0"
    ? { action: "pick", slug: project, n: Number(data.n) || 1, note: data.note || "" }
    : {
        action: "gate", slug: project, gate: Number(gate.slice(-1)),
        decision, note: data.note || "", override: !!data.override,
      };
  if (decision === "reject" && !payload.note) {
    say("A rejection needs a reason - it is the permanent record the next round reads.");
    return;
  }
  await act(button, async () => {
    const run = await api("/api/run", { method: "POST", body: JSON.stringify(payload) });
    await waitForRun(run.id);
    if (decision === "approve") {
      // the pipeline's own behaviour: an approved gate opens the next phase, so
      // hand the project straight back to the orchestrator. A rejection does not
      // resume - it waits for a person to revise or fix.
      await api(`/api/projects/${encodeURIComponent(project)}/start`, { method: "POST" });
      return { reason: `${gate} approved - the workflow is resuming` };
    }
    return { reason: `${gate} rejected - the workflow stays paused here` };
  });
}

async function submitHuman(form) {
  const button = form.querySelector("button");
  const data = Object.fromEntries(new FormData(form).entries());
  const payload = { action: form.dataset.human, slug, ...data };
  payload.could_not_teach = !!data.could_not_teach;
  await act(button, async () => {
    const run = await api("/api/run", { method: "POST", body: JSON.stringify(payload) });
    await waitForRun(run.id);
    return run;
  });
}

async function waitForRun(runId, tries = 60) {
  for (let i = 0; i < tries; i++) {
    const run = await api(`/api/runs/${runId}`);
    if (run.status !== "running") {
      if (run.status === "failed") {
        throw new Error((run.stderr || run.stdout || "the command failed").slice(-600));
      }
      return run;
    }
    await new Promise(r => setTimeout(r, 400));
  }
  return null;
}

async function submitCreate(start, button) {
  const form = document.querySelector("#create-form");
  const data = Object.fromEntries(new FormData(form).entries());
  if (!data.slug) { say("A project slug is required."); return; }
  if (data.flow === "2" && !data.stack) { say("The human gives the stack - it is required."); return; }
  await act(button, async () => {
    const created = await api("/api/projects", {
      method: "POST",
      body: JSON.stringify({ ...data, uploads }),
    });
    if (created.stack_error) throw new Error(created.stack_error);
    uploads = [];
    slug = created.slug;
    if (start) {
      await api(`/api/projects/${encodeURIComponent(created.slug)}/start`, { method: "POST" });
    }
    await loadOverview(false);
    setView("project", created.slug);
    return { reason: `${created.slug} created${start ? " and started" : ""}` };
  });
}

function readUploads(input) {
  const files = [...input.files];
  Promise.all(files.map(f => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve({ name: f.name, size: f.size, data: reader.result });
    reader.onerror = reject;
    reader.readAsDataURL(f);
  }))).then(list => { uploads = uploads.concat(list); renderUploads(); })
    .catch(e => say(e.message));
}
function renderUploads() {
  const node = document.querySelector("#upload-list");
  if (!node) return;
  node.innerHTML = uploads.length
    ? `<div class="chips">${uploads.map((u, i) => `<span class="chip-btn">${
        esc(u.name)} (${bytes(u.size)}) <button class="link" data-drop="${i}">x</button>
      </span>`).join("")}</div>` : "";
  node.querySelectorAll("[data-drop]").forEach(b =>
    b.onclick = () => { uploads.splice(Number(b.dataset.drop), 1); renderUploads(); });
}

async function viewArtifact(project, path) {
  try {
    openArtifact = await api(`/api/projects/${encodeURIComponent(project)}/artifact?path=${
      encodeURIComponent(path)}`);
    if (view === "project") {
      patch("pd-viewer", artifactViewer());
      document.querySelector("#pd-viewer").scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      showDrawer(`<h2>${esc(path)}</h2>${pre(openArtifact.content, "scroll tall")}`);
    }
  } catch (err) { say(err.message); }
}

async function loadArtifactsFor(project) {
  try {
    slug = project;
    const d = await api(`/api/projects/${encodeURIComponent(project)}`);
    const body = document.querySelector("#artifact-body");
    if (!body) return;
    body.innerHTML = artifactTable(d.artifacts);
    wire(body);
  } catch (err) { say(err.message); }
}

async function showRunLog(runId) {
  try {
    const run = await api(`/api/runs/${runId}`);
    showDrawer(`
      <div class="live-head"><h2>${esc(run.label || run.component)} ${
        chip((run.status || "").toUpperCase())}</h2></div>
      <div class="field-row">
        ${field("Project", esc(run.slug || ""))}
        ${field("Kind", esc(run.kind || ""))}
        ${field("Attempt", run.attempt ?? "")}
        ${field("Started", time(run.started))}
        ${field("Finished", run.finished ? time(run.finished) : "")}
        ${field("Exit code", run.returncode === null || run.returncode === undefined
          ? "" : run.returncode)}
        ${run.model ? field("Model", `<code>${esc(run.model)}</code>`) : ""}
        ${run.args && run.args.length ? field("Command",
          `<code>python -m pipeline ${esc(run.args.join(" "))}</code>`) : ""}
      </div>
      <div class="out-label">Output</div>${pre(run.stdout, "scroll tall") ||
        empty("no output recorded")}
      ${run.stderr ? `<div class="out-label">stderr</div>${pre(run.stderr, "scroll bad")}` : ""}`);
  } catch (err) { say(err.message); }
}

function showDrawer(html) {
  drawer.hidden = false;
  drawer.innerHTML = `<div class="drawer-inner">
    <button class="button small ghost drawer-close">Close</button>${html}</div>`;
  drawer.querySelector(".drawer-close").onclick = () => { drawer.hidden = true; };
  drawer.onclick = ev => { if (ev.target === drawer) drawer.hidden = true; };
}

/* ------------------------------------------------------------------ polling
 * Poll only while something can change, and stop when it cannot. */
function schedulePolling() {
  clearInterval(poller); clearInterval(overviewPoller);
  poller = null; overviewPoller = null;
  if (view === "project" && detail) {
    const live = ["RUNNING", "QUEUED"].includes(detail.status) ||
      (detail.workflow || {}).state === "running";
    liveDot.classList.toggle("on", live);
    if (live) poller = setInterval(pollProject, 1500);
    else poller = setInterval(pollProject, 6000);
    return;
  }
  const anyLive = overview && overview.counts.RUNNING > 0;
  liveDot.classList.toggle("on", !!anyLive);
  overviewPoller = setInterval(() => loadOverview().catch(() => {}), anyLive ? 2500 : 8000);
}

// The status payload carries only the gates that matter; the detail payload
// carries all four. Compare the same subset or every poll looks like a change.
function gateSignature(gates) {
  return JSON.stringify((gates || [])
    .filter(g => g.waiting || g.status === "approved" || g.status === "rejected")
    .map(g => [g.gate, g.status, g.waiting]));
}

async function pollProject() {
  if (view !== "project" || !slug) return;
  let status;
  try {
    status = await api(`/api/projects/${encodeURIComponent(slug)}/status?after=${eventSeq}`);
  } catch { return; }
  if (!detail || detail.slug !== slug) return;

  const structural =
    status.status !== detail.status ||
    status.step !== detail.step ||
    status.progress !== detail.progress ||
    JSON.stringify(status.workflow || {}) !== JSON.stringify(detail.workflow || {}) ||
    gateSignature(status.gates) !== gateSignature(detail.gates);

  Object.assign(detail, {
    status: status.status, phase: status.phase, phase_title: status.phase_title,
    step: status.step, step_description: status.step_description,
    progress: status.progress, completed_actions: status.completed_actions,
    total_actions: status.total_actions, retry_count: status.retry_count,
    workflow: status.workflow, phases: status.phases,
    current_execution: status.current_execution, runs: status.runs,
  });
  detail.state.ticket = status.ticket;

  if (status.events && status.events.length) {
    eventSeq = status.event_seq || eventSeq;
    const box = document.getElementById("pd-events");
    if (box) {
      if (box.querySelector(".empty")) box.innerHTML = "";
      box.insertAdjacentHTML("beforeend", status.events.map(eventRow).join(""));
      box.scrollTop = box.scrollHeight;
      const counter = document.getElementById("pd-event-count");
      if (counter) counter.textContent = `${box.children.length} recorded`;
    }
  }

  patch("pd-timeline", timelinePanel());
  patch("pd-current", currentPanel());
  patch("pd-preview", previewPanel());
  patch("pd-runs", runList(detail.runs));
  patch("pd-controls", projectControls());
  patch("pd-error", errorPanel());
  if (structural) {
    await loadDetail(false);
    patch("pd-header", projectHeader());
    patch("pd-gate", gateSection());
    patch("pd-steps", stepPanel());
    patch("pd-artifacts", artifactTable(detail.artifacts));
    schedulePolling();
  }
}

/* --------------------------------------------------------------------- boot */
navButtons.forEach(b => b.onclick = () => setView(b.dataset.view));
refreshButton.onclick = async () => {
  refreshButton.disabled = true;
  try {
    await loadOverview(view !== "project");
    if (view === "project") await loadDetail();
  } catch (err) { say(err.message); }
  refreshButton.disabled = false;
};
document.addEventListener("keydown", ev => {
  if (ev.key === "Escape") drawer.hidden = true;
});
loadOverview().catch(err => say(err.message));
