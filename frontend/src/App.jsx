import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "▦" },
  { id: "risk", label: "Risk Analysis", icon: "◉" },
  { id: "benchmark", label: "Project Benchmarking", icon: "⇄" },
  { id: "scenario", label: "Scenario Analysis", icon: "⌁" },
  { id: "recommendations", label: "Action Recommendations", icon: "✓" },
  { id: "warnings", label: "Early Warnings", icon: "!" },
];

const SCENARIO_FIELDS = [
  {
    key: "Approvals_Pending",
    label: "Pending Approvals",
    unit: "",
    min: 0,
    step: 1,
  },
  {
    key: "Procurement_Delay_Days",
    label: "Procurement Delay",
    unit: "days",
    min: 0,
    step: 1,
  },
  {
    key: "Milestones_Delayed",
    label: "Milestones Delayed",
    unit: "",
    min: 0,
    step: 1,
  },
  {
    key: "Physical_Progress",
    label: "Physical Progress",
    unit: "%",
    min: 0,
    max: 100,
    step: 0.1,
  },
  {
    key: "Scope_Changes",
    label: "Scope Changes",
    unit: "",
    min: 0,
    step: 1,
  },
  {
    key: "Average_Milestone_Delay_Days",
    label: "Average Milestone Delay",
    unit: "days",
    min: 0,
    step: 0.1,
  },
  {
    key: "Land_Acquisition_Progress",
    label: "Land Acquisition Progress",
    unit: "%",
    min: 0,
    max: 100,
    step: 0.1,
  },
  {
    key: "Planned_Progress",
    label: "Planned Progress",
    unit: "%",
    min: 0,
    max: 100,
    step: 0.1,
  },
  {
    key: "Financial_Progress",
    label: "Financial Progress",
    unit: "%",
    min: 0,
    max: 100,
    step: 0.1,
  },
];

const FALLBACK_PROJECT = {
  Project_ID: "PRJ-0003", Sector: "Energy", Project_Type: "Power",
  Approved_Cost: 2346.94, Planned_Duration: 30, Elapsed_Duration: 23,
  Physical_Progress: 72.8, Planned_Progress: 79.8, Financial_Progress: 77.8,
  Expenditure: 1815.63, Milestones_Total: 14, Milestones_Delayed: 3,
  Average_Milestone_Delay_Days: 32.9, Procurement_Delay_Days: 7,
  Land_Acquisition_Progress: 93.1, Approvals_Pending: 2, Scope_Changes: 1,
  Contractor_Performance: "Good",
};

async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(await response.text() || "Request failed");
  return response.json();
}

function App() {
  const [activeView, setActiveView] = useState("dashboard");
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState("PRJ-0003");
  const [projectData, setProjectData] = useState(FALLBACK_PROJECT);
  const [riskData, setRiskData] = useState(null);
  const [explainData, setExplainData] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [warningData, setWarningData] = useState(null);
  const [recommendationData, setRecommendationData] = useState(null);
  const [whatIfData, setWhatIfData] = useState(null);
  const [loadingProjects, setLoadingProjects] = useState(true);

  const [loading, setLoading] = useState(true);
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [error, setError] = useState("");

  const [scenarioRows, setScenarioRows] = useState([
    { id: 1, field: "Approvals_Pending", value: "" },
  ]);
  const [scenarioMessage, setScenarioMessage] = useState("");

  useEffect(() => {
    async function loadProjects() {
      try {
        setLoadingProjects(true);
        const data = await fetchJSON(`${API_BASE}/projects`);
        const list = data.projects || [];
        setProjects(list.length ? list : [FALLBACK_PROJECT]);
        const selected = list.find(p => p.Project_ID === selectedProjectId) || list[0] || FALLBACK_PROJECT;
        setSelectedProjectId(selected.Project_ID);
        setProjectData(selected);
      } catch (err) {
        console.error(err);
        setProjects([FALLBACK_PROJECT]);
        setProjectData(FALLBACK_PROJECT);
        setSelectedProjectId(FALLBACK_PROJECT.Project_ID);
        setError("Project list could not be loaded. Showing the prototype project.");
      } finally {
        setLoadingProjects(false);
      }
    }
    loadProjects();
  }, []);

  useEffect(() => {
    if (!projectData) return;
    async function loadIntelligence() {
      try {
        setLoading(true);
        setError("");

        setRiskData(null);
        setExplainData(null);
        setBenchmarkData(null);
        setWarningData(null);
        setRecommendationData(null);
        setWhatIfData(null);

        setScenarioRows([
          {
            id: 1,
            field: "Approvals_Pending",
            value: "",
          },
        ]);

        setScenarioMessage("");
        const body = { headers: { "Content-Type": "application/json" }, body: JSON.stringify({ project: projectData }) };
        const [predict, explain, benchmark, warning, recommendations] = await Promise.all([
          fetchJSON(`${API_BASE}/predict`, { method: "POST", ...body }),
          fetchJSON(`${API_BASE}/explain`, { method: "POST", ...body }),
          fetchJSON(`${API_BASE}/benchmark`, { method: "POST", ...body }),
          fetchJSON(`${API_BASE}/early-warning`, { method: "POST", ...body }),
          fetchJSON(`${API_BASE}/recommendations`, { method: "POST", ...body }),
        ]);
        setRiskData(predict.result); setExplainData(explain.result); setBenchmarkData(benchmark.result);
        setWarningData(warning.result); setRecommendationData(recommendations.result);
      } catch (err) {
        console.error(err);
        setError("Unable to connect to the OnTrack AI prediction service. Make sure the backend is running.");
      } finally { setLoading(false); }
    }
    loadIntelligence();
  }, [projectData]);

  const goTo = view => { setActiveView(view); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const handleProjectChange = e => {
    const selected = projects.find(p => p.Project_ID === e.target.value);
    if (selected) { setSelectedProjectId(selected.Project_ID); setProjectData(selected); }
  };

  const getScenarioField = key =>
    SCENARIO_FIELDS.find(field => field.key === key);

  const getCurrentValue = key =>
    projectData?.[key] ?? "";

  const getUsedScenarioFields = () =>
    scenarioRows.map(row => row.field);

  const handleScenarioFieldChange = (id, field) => {
    setScenarioRows(rows =>
      rows.map(row =>
        row.id === id
          ? {
            ...row,
            field,
            value: getCurrentValue(field),
          }
          : row
      )
    );
    setScenarioMessage("");
    setWhatIfData(null);
  };

  const handleScenarioValueChange = (id, value) => {
    setScenarioRows(rows =>
      rows.map(row =>
        row.id === id
          ? { ...row, value }
          : row
      )
    );
    setScenarioMessage("");
    setWhatIfData(null);
  };

  const addScenarioRow = () => {
    const usedFields = getUsedScenarioFields();
    const nextField = SCENARIO_FIELDS.find(
      field => !usedFields.includes(field.key)
    );

    if (!nextField) {
      setScenarioMessage("All supported project factors have already been added.");
      return;
    }

    const nextId =
      Math.max(...scenarioRows.map(row => row.id), 0) + 1;

    setScenarioRows(rows => [
      ...rows,
      {
        id: nextId,
        field: nextField.key,
        value: getCurrentValue(nextField.key),
      },
    ]);

    setScenarioMessage("");
  };

  const removeScenarioRow = id => {
    if (scenarioRows.length === 1) {
      setScenarioRows([
        {
          id: 1,
          field: "Approvals_Pending",
          value: "",
        },
      ]);
    } else {
      setScenarioRows(rows => rows.filter(row => row.id !== id));
    }

    setScenarioMessage("");
    setWhatIfData(null);
  };

  async function runWhatIf() {
    const modifications = {};

    for (const row of scenarioRows) {
      if (row.value === "" || row.value === null || row.value === undefined) {
        setScenarioMessage(
          `Enter a proposed value for ${getScenarioField(row.field)?.label || "the selected factor"}.`
        );
        return;
      }

      const numericValue = Number(row.value);

      if (!Number.isFinite(numericValue)) {
        setScenarioMessage(
          `Enter a valid numeric value for ${getScenarioField(row.field)?.label || "the selected factor"}.`
        );
        return;
      }

      const fieldConfig = getScenarioField(row.field);

      if (fieldConfig?.min !== undefined && numericValue < fieldConfig.min) {
        setScenarioMessage(
          `${fieldConfig.label} cannot be below ${fieldConfig.min}.`
        );
        return;
      }

      if (
        fieldConfig?.max !== undefined &&
        numericValue > fieldConfig.max
      ) {
        setScenarioMessage(
          `${fieldConfig.label} cannot be above ${fieldConfig.max}.`
        );
        return;
      }

      modifications[row.field] = numericValue;
    }

    try {
      setWhatIfLoading(true);
      setError("");
      setScenarioMessage("");

      const data = await fetchJSON(`${API_BASE}/what-if`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project: projectData,
          modifications,
          include_explanations: true,
        }),
      });

      setWhatIfData(data.result);
    } catch (err) {
      console.error(err);
      setScenarioMessage(
        "Scenario analysis could not be completed. Please check the backend connection."
      );
    } finally {
      setWhatIfLoading(false);
    }
  }

  // async function runWhatIf() {
  //   try {
  //     setWhatIfLoading(true); setError("");
  //     const data = await fetchJSON(`${API_BASE}/what-if`, {
  //       method: "POST", headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify({ project: projectData, modifications: { Approvals_Pending: 0 }, include_explanations: true }),
  //     });
  //     setWhatIfData(data.result);
  //   } catch (err) { console.error(err); setError("Scenario analysis could not be completed."); }
  //   finally { setWhatIfLoading(false); }
  // }

  const riskScore = riskData?.overall_risk_score;
  const riskLevel = riskData?.risk_level || "--";
  const timeRisk = riskData ? (riskData.time_risk_probability * 100).toFixed(2) : "--";
  const costRisk = riskData ? (riskData.cost_risk_probability * 100).toFixed(2) : "--";
  const implementationRisk = riskData ? (riskData.implementation_risk_probability * 100).toFixed(2) : "--";
  const peerDistribution = benchmarkData?.peer_risk_distribution || {};
  const warnings = warningData?.warnings || [];
  const drivers = explainData?.time_overrun?.top_risk_factors || explainData?.time_overrun?.positive_drivers || [];
  const recommendations = Array.isArray(recommendationData) ? recommendationData : recommendationData?.recommendations || [];
  const selectedLabel = useMemo(() => `${projectData?.Project_ID || selectedProjectId} — ${projectData?.Sector || ""} / ${projectData?.Project_Type || ""}`, [projectData, selectedProjectId]);

  const PageHeader = ({ eyebrow, title, description }) => <header className="topbar"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="header-description">{description}</p></div></header>;
  const RiskCard = ({ title, value, description, fillClass }) => <div className="landscape-card"><div className="landscape-top"><span>{title}</span><strong>{value}%</strong></div><div className="landscape-bar"><div className={`landscape-fill ${fillClass}`} style={{ width: `${Number(value) || 0}%` }} /></div><p>{description}</p></div>;

  function Dashboard() {
    return (
      <>
        <PageHeader

          eyebrow="PREDICTIVE INFRASTRUCTURE INTELLIGENCE"
          title="Project Dashboard"
          description="A focused overview of the selected project's current risk and performance."
        />

        {/* APPLICATION INTRO */}
        <section className="hero-section">
          <div className="hero-content">
            <div className="hero-label">
              <span className="pulse-dot" />
              AI-POWERED INFRASTRUCTURE INTELLIGENCE
            </div>

            <h2>
              Predict project risk
              <br />
              <span>before it becomes a problem.</span>
            </h2>

            <p>
              <strong>OnTrack AI</strong> analyses project data to identify
              potential time overruns, cost escalation and implementation risks.
            </p>

            <p className="hero-secondary">
              Understand why risk is emerging, compare the project with relevant
              peers, simulate possible interventions and prioritize early action.
            </p>

            <button className="hero-button" onClick={() => goTo("risk")}>
              Explore Risk Intelligence <span>→</span>
            </button>

            <div className="hero-features">
              <span>Predict</span>
              <span>Explain</span>
              <span>Benchmark</span>
              <span>Simulate</span>
              <span>Recommend</span>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-grid" />

            <div className="intelligence-visual">
              <div className="visual-ring ring-one" />
              <div className="visual-ring ring-two" />

              <div className="visual-center">
                <div className="center-icon">SIH</div>
                <strong>
                  OnTrack AI
                  <br />
                  Kratarthaka
                </strong>
              </div>

              <div className="signal-card signal-one">
                <span className="signal-icon blue" />
                <div>
                  <strong>Predict</strong>
                  <small>Risk Detection</small>
                </div>
              </div>

              <div className="signal-card signal-two">
                <span className="signal-icon amber" />
                <div>
                  <strong>Explain</strong>
                  <small>Risk Drivers</small>
                </div>
              </div>

              <div className="signal-card signal-three">
                <span className="signal-icon green" />
                <div>
                  <strong>Act</strong>
                  <small>Early Intervention</small>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ACTIVE PROJECT + PROJECT SELECTOR */}
        <section className="section">
          <div className="project-selector-bar">
            <div>
              <span className="selector-label">Active project</span>
              <strong>{selectedProjectId}</strong>
            </div>

            <div className="project-selector">
              <label htmlFor="project-select">Select Project</label>

              <select
                id="project-select"
                value={selectedProjectId}
                onChange={handleProjectChange}
                disabled={loadingProjects || !projects.length}
              >
                {projects.map((p) => (
                  <option key={p.Project_ID} value={p.Project_ID}>
                    {p.Project_ID} — {p.Sector} / {p.Project_Type}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* SELECTED PROJECT */}
        <section className="section">
          <div className="section-heading">
            <div>
              <h2>Selected Project</h2>
              <p>{selectedLabel}</p>
            </div>

            <button
              className="text-button"
              onClick={() => goTo("risk")}
            >
              View Risk →
            </button>
          </div>

          <div className="summary-grid">
            <div className="summary-card">
              <span>Overall Risk</span>
              <strong>
                {loading ? "--" : riskScore ?? "--"}
              </strong>
              <small>{riskLevel}</small>
            </div>

            <div className="summary-card">
              <span>Time Overrun Risk</span>
              <strong>{timeRisk}%</strong>
              <small>Likelihood of schedule delay</small>
            </div>

            <div className="summary-card">
              <span>Cost Overrun Risk</span>
              <strong>{costRisk}%</strong>
              <small>Likelihood of exceeding approved cost</small>
            </div>

            <div className="summary-card">
              <span>Comparable Projects</span>
              <strong>
                {benchmarkData?.comparable_project_count ?? "--"}
              </strong>
              <small>Projects used for benchmarking</small>
            </div>
          </div>
        </section>

        {/* AI DECISION SUPPORT */}
        <section className="section">
          <div className="section-heading">
            <div>
              <h2>AI Decision Support</h2>
              <p>
                Move from risk detection to evidence-based intervention.
              </p>
            </div>
          </div>

          <div className="action-grid">
            <ActionCard
              icon="◉"
              title="Risk Analysis"
              text="Understand the factors driving project risk."
              view="risk"
            />

            <ActionCard
              icon="⇄"
              title="Project Benchmarking"
              text="Compare the project with relevant peers."
              view="benchmark"
            />

            <ActionCard
              icon="⌁"
              title="Scenario Analysis"
              text="Evaluate how a proposed change may affect risk."
              view="scenario"
            />

            <ActionCard
              icon="✓"
              title="Action Recommendations"
              text="Get prioritized actions based on identified risks."
              view="recommendations"
            />
          </div>
        </section>
      </>
    );
  }

  function ActionCard({ icon, title, text, view }) { return <button className="action-card" onClick={() => goTo(view)}><span className="action-icon">{icon}</span><div><strong>{title}</strong><p>{text}</p></div><span className="arrow">→</span></button>; }

  function RiskAnalysis() {
    return <><PageHeader eyebrow="RISK INTELLIGENCE" title="Risk Analysis" description="Identify the key factors contributing to project risk." /><section className="section"><div className="section-heading"><div><h2>Current Project Risk</h2><p>{selectedLabel}</p></div><div className="risk-score-display"><span>Overall Risk</span><strong>{loading ? "--" : riskScore ?? "--"}</strong><small>{riskLevel}</small></div></div><div className="risk-landscape-grid"><RiskCard title="Time Overrun Risk" value={timeRisk} description="Likelihood of schedule delay" fillClass="time" /><RiskCard title="Cost Overrun Risk" value={costRisk} description="Likelihood of exceeding the approved cost" fillClass="cost" /><RiskCard title="Implementation Risk" value={implementationRisk} description="Current risk to project execution" fillClass="implementation" /></div></section><section className="section"><div className="drivers-layout"><div className="driver-panel"><div className="panel-heading"><div><h2>Risk Drivers</h2><p>Key factors contributing to the time overrun risk.</p></div></div>{drivers.length ? drivers.slice(0, 6).map((d, i) => { const c = Number(d.contribution ?? d.shap_value ?? 0); return <div className="driver" key={i}><div><span>{d.feature || d.name || d.feature_key || "Project factor"}</span><strong>Risk Driver</strong></div><div className="driver-bar"><div className="driver-fill high" style={{ width: `${Math.min(100, Math.max(8, Math.abs(c) * 70))}%` }} /></div></div>; }) : <p>{loading ? "Analysing risk drivers..." : "No risk drivers available."}</p>}</div><div className="driver-panel"><div className="panel-heading"><div><h2>Project Factors</h2><p>Current indicators used by the prediction models.</p></div></div><div className="status-grid">{[["Physical Progress", `${projectData.Physical_Progress}%`], ["Planned Progress", `${projectData.Planned_Progress}%`], ["Financial Progress", `${projectData.Financial_Progress}%`], ["Land Acquisition", `${projectData.Land_Acquisition_Progress}%`], ["Procurement Delay", `${projectData.Procurement_Delay_Days} days`], ["Pending Approvals", projectData.Approvals_Pending]].map(([a, b]) => <div key={a}><span>{a}</span><strong>{b}</strong></div>)}</div></div></div></section></>;
  }

  function Benchmark() {
    const m = benchmarkData?.metrics || {};
    const rows = [
      ["Physical Progress", m.physical_progress],
      ["Financial Progress", m.financial_progress],
      ["Procurement Delay", m.procurement_delay_days],
      ["Milestone Delay", m.average_milestone_delay_days],
      ["Pending Approvals", m.approvals_pending],
      ["Land Acquisition", m.land_acquisition_progress],
      ["Overall Risk Score", m.overall_risk_score]
    ];

    return (
      <> {/* <-- Fragment starts here */}
        <PageHeader
          eyebrow="PROJECT BENCHMARKING"
          title="Project Benchmarking"
          description="Compare performance with similar projects."
        />

        <section className="section">
          <div className="summary-grid">
            <div className="summary-card">
              <span>Comparable Projects</span>
              <strong>{benchmarkData?.comparable_project_count ?? "--"}</strong>
              <small>Matching sector, type and scale</small>
            </div>

            <div className="summary-card">
              <span>Sector</span>
              <strong>{projectData.Sector}</strong>
              <small>{projectData.Project_Type}</small>
            </div>

            <div className="summary-card">
              <span>Project Risk</span>
              <strong>{m.overall_risk_score?.project ?? "--"}</strong>
              <small>Current overall risk score</small>
            </div>

            <div className="summary-card">
              <span>Peer Average Risk</span>
              <strong>{m.overall_risk_score?.peer_average ?? "--"}</strong>
              <small>Comparable project average</small>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="driver-panel">
            <div className="panel-heading">
              <div>
                <h2>Peer Comparison</h2>
                <p>Project values alongside comparable-project averages.</p>
              </div>
            </div>

            <div className="benchmark-table">

              <div className="benchmark-row">
                <span><strong>PROJECT METRIC</strong></span>
                <strong>SELECTED PROJECT</strong>
                <strong>PEER AVERAGE</strong>
              </div>

              {rows.map(([label, metric]) => (
                <div className="benchmark-row" key={label}>
                  <span>{label}</span>
                  <strong>{metric?.project ?? "--"}</strong>
                  <strong>{metric?.peer_average ?? "--"}</strong>
                </div>
              ))}

            </div>

            {benchmarkData?.dataset_notice && (
              <div className="prototype-notice">
                <strong>Data note:</strong> {benchmarkData.dataset_notice}
              </div>
            )}
          </div>
        </section>
      </>
    ); // <-- Fragment ends here
  }


  function Scenario() {
    const o = whatIfData?.original_prediction;
    const s = whatIfData?.scenario_prediction;
    const d = whatIfData?.deltas;

    return (
      <>
        <PageHeader
          eyebrow="SCENARIO ANALYSIS"
          title="Scenario Analysis"
          description="Evaluate how proposed project changes may affect the overall risk."
        />

        <section className="section">
          <div className="driver-panel scenario-builder">

            <div className="panel-heading">
              <div>
                <h2>Build a What-If Scenario</h2>
                <p>
                  Select one or more project factors and enter the proposed
                  values to evaluate their model-projected impact.
                </p>
              </div>
            </div>

            <div className="scenario-table">

              <div className="scenario-table-header">
                <span>Project Factor</span>
                <span>Current Value</span>
                <span>Proposed Value</span>
                <span></span>
              </div>

              {scenarioRows.map(row => {
                const field = getScenarioField(row.field);
                const currentValue = getCurrentValue(row.field);
                const usedFields = getUsedScenarioFields();

                return (
                  <div className="scenario-row" key={row.id}>

                    <div className="scenario-field">
                      <select
                        value={row.field}
                        onChange={e =>
                          handleScenarioFieldChange(
                            row.id,
                            e.target.value
                          )
                        }
                      >
                        {SCENARIO_FIELDS.map(option => (
                          <option
                            key={option.key}
                            value={option.key}
                            disabled={
                              usedFields.includes(option.key) &&
                              option.key !== row.field
                            }
                          >
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="scenario-current">
                      <strong>{currentValue}</strong>
                      {field?.unit && <span>{field.unit}</span>}
                    </div>

                    <div className="scenario-input-wrap">
                      <input
                        type="number"
                        min={field?.min}
                        max={field?.max}
                        step={field?.step || 1}
                        value={row.value}
                        onChange={e =>
                          handleScenarioValueChange(
                            row.id,
                            e.target.value
                          )
                        }
                        placeholder={`Enter ${field?.label?.toLowerCase() || "value"}`}
                      />
                      {field?.unit && <span>{field.unit}</span>}
                    </div>

                    <button
                      type="button"
                      className="scenario-remove"
                      onClick={() => removeScenarioRow(row.id)}
                      title="Remove factor"
                    >
                      ×
                    </button>

                  </div>
                );
              })}

            </div>

            {scenarioMessage && (
              <div className="scenario-message">
                {scenarioMessage}
              </div>
            )}

            <div className="scenario-actions">

              <button
                type="button"
                className="secondary-button"
                onClick={addScenarioRow}
              >
                + Add Project Factor
              </button>

              <button
                type="button"
                className="hero-button"
                onClick={runWhatIf}
                disabled={whatIfLoading}
              >
                {whatIfLoading
                  ? "Running Scenario..."
                  : "Run Scenario"}
                <span>→</span>
              </button>

            </div>

            {whatIfData && o && s && (
              <div className="what-if-result">

                <div className="what-if-result-header">
                  <div>
                    <span className="what-if-kicker">
                      Scenario Result
                    </span>
                    <h3>Risk After Change</h3>
                  </div>

                  <div className="scenario-result-score">
                    <span>Projected Overall Risk</span>
                    <strong>
                      {Number(s.overall_risk_score).toFixed(1)}
                    </strong>
                    <small>{s.risk_level}</small>
                  </div>
                </div>

                <div className="what-if-risk-summary">

                  <div className="what-if-risk-box">
                    <span>Current Project Risk</span>
                    <strong>
                      {Number(o.overall_risk_score).toFixed(1)}
                    </strong>
                    <small>{o.risk_level}</small>
                  </div>

                  <div className="what-if-transition">
                    →
                  </div>

                  <div className="what-if-risk-box">
                    <span>Risk After Change</span>
                    <strong>
                      {Number(s.overall_risk_score).toFixed(1)}
                    </strong>
                    <small>{s.risk_level}</small>
                  </div>

                </div>

                <div className="scenario-changes">

                  <h3>Changes Tested</h3>

                  <div className="scenario-change-list">

                    {scenarioRows.map(row => {
                      const field = getScenarioField(row.field);

                      return (
                        <div
                          className="scenario-change"
                          key={row.id}
                        >
                          <span>{field?.label}</span>

                          <strong>
                            {getCurrentValue(row.field)}
                            {field?.unit ? ` ${field.unit}` : ""}
                            {" → "}
                            {row.value}
                            {field?.unit ? ` ${field.unit}` : ""}
                          </strong>
                        </div>
                      );
                    })}

                  </div>

                </div>

                <div className="what-if-metrics">

                  <div className="what-if-metric">
                    <span>Time risk change</span>
                    <strong>
                      {(
                        (d?.time_risk_probability_delta ?? 0) * 100
                      ).toFixed(2)}{" "}
                      pp
                    </strong>
                  </div>

                  <div className="what-if-metric">
                    <span>Cost risk change</span>
                    <strong>
                      {(
                        (d?.cost_risk_probability_delta ?? 0) * 100
                      ).toFixed(2)}{" "}
                      pp
                    </strong>
                  </div>

                  <div className="what-if-metric">
                    <span>Implementation risk change</span>
                    <strong>
                      {(
                        (d?.implementation_risk_probability_delta ?? 0) *
                        100
                      ).toFixed(2)}{" "}
                      pp
                    </strong>
                  </div>

                  <div className="what-if-metric">
                    <span>Overall risk change</span>
                    <strong>
                      {Number(
                        d?.overall_risk_score_delta ?? 0
                      ).toFixed(1)}
                    </strong>
                  </div>

                </div>

                <div className="what-if-verification">
                  Calculated using the trained ML models.
                </div>

                <div className="what-if-disclaimer">
                  This is a model-projected scenario using representative
                  synthetic data; it is not causal proof.
                </div>

              </div>
            )}

          </div>
        </section>
      </>
    );
  }

  function Recommendations() {
    return <><PageHeader eyebrow="DECISION SUPPORT" title="Action Recommendations" description="Get prioritized actions based on identified project risks." /><section className="section"><div className="driver-panel"><div className="panel-heading"><div><h2>Recommended Actions</h2><p>Actions generated from the selected project's current risk indicators.</p></div></div>{recommendations.length ? <div className="recommendation-list">{recommendations.map((r, i) => { const p = r.priority || r.severity || r.level || "Medium"; const title = r.title || r.action || r.recommendation || `Recommended action ${i + 1}`; const desc = r.description || r.reason || r.message || r.action_description || ""; return <div className="warning-item" key={i}><span className="warning-icon">✓</span><div><strong>{p} Priority · {title}</strong><p>{desc}</p></div></div>; })}</div> : <p>{loading ? "Generating recommendations..." : "No recommendations were returned for this project."}</p>}</div></section></>;
  }

  function EarlyWarnings() {
    return <><PageHeader eyebrow="EARLY WARNING MONITORING" title="Early Warnings" description="Review current conditions that may require closer project monitoring." /><section className="section"><div className="summary-grid"><div className="summary-card"><span>Warning Level</span><strong>{warningData?.warning_level ?? "--"}</strong><small>{warningData?.message ?? "Current monitoring status"}</small></div><div className="summary-card"><span>Overall Risk</span><strong>{warningData?.risk_score ?? "--"}</strong><small>Current model risk score</small></div><div className="summary-card"><span>Pending Approvals</span><strong>{projectData.Approvals_Pending}</strong><small>Current project indicator</small></div><div className="summary-card"><span>Milestones Delayed</span><strong>{projectData.Milestones_Delayed}</strong><small>Current project indicator</small></div></div></section><section className="section"><div className="driver-panel warning-panel"><div className="panel-heading"><div><h2>Warning Signals</h2><p>Conditions currently contributing to project risk.</p></div></div>{warnings.length ? warnings.map((w, i) => <div className="warning-item" key={i}><span className="warning-icon">!</span><div><strong>Risk signal detected</strong><p>{typeof w === "string" ? w : w.message}</p></div></div>) : <p>{loading ? "Analysing project conditions..." : "No warning signals returned"}</p>}</div></section></>;
  }

  function ActivePage() {
    if (activeView === "risk") return <RiskAnalysis />;
    if (activeView === "benchmark") return <Benchmark />;
    if (activeView === "scenario") return <Scenario />;
    if (activeView === "recommendations") return <Recommendations />;
    if (activeView === "warnings") return <EarlyWarnings />;
    return <Dashboard />;
  }

  return <div className="app">
    <aside className="sidebar"><div className="brand"><div className="brand-icon">SIH</div><div><h2>OnTrack AI</h2><span>Team Kratarthaka</span></div></div><nav className="navigation">{NAV_ITEMS.map(item => <button key={item.id} className={`nav-item ${activeView === item.id ? "active" : ""}`} onClick={() => goTo(item.id)}><span>{item.icon}</span>{item.label}</button>)}</nav><div className="sidebar-footer"><span className="status-dot" />AI Monitoring Active</div></aside>
    <main className="main-content">

      {error && <div className="prototype-notice"><strong>Notice:</strong> {error}</div>}
      <ActivePage />
      <div className="prototype-notice"><strong>Data note:</strong> This prototype uses representative synthetic project data. Results should be recalibrated using verified government project data before real-world deployment.</div>
    </main>
  </div>;
}

export default App;
