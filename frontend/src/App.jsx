import { useEffect, useMemo, useState, useRef } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "▦" },
  { id: "risk", label: "Risk Analysis", icon: "◉" },
  { id: "benchmark", label: "Project Benchmarking", icon: "⇄" },
  { id: "scenario", label: "Scenario Analysis", icon: "⌁" },
  { id: "recommendations", label: "Action Recommendations", icon: "✓" },
  { id: "warnings", label: "Early Warnings", icon: "!" },
  { id: "chat", label: "AI Assistant", icon: "💬" },
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

const FALLBACK_PAIMANA_PROJECT = {
  Project_ID: "PAIMANA-706718",
  Project_Name: "C/o NITB Imphal Airport",
  Line_Ministry: "Ministry of Civil Aviation",
  Executing_Agency: "Airport Authority of India [AAI]",
  Sector: "Civil Aviation",
  Project_Type: "Airport",
  Approved_Cost: 499.0,
  Planned_Duration: 32,
  Elapsed_Duration: 57,
  Physical_Progress: 54.0,
  Planned_Progress: 100.0,
  Financial_Progress: 43.1,
  Expenditure: 215.1,
  Time_Overrun_Months: 29.0,
  Cost_Overrun_Pct: 0.0,
  Time_Overrun_Flag: 1,
  Cost_Overrun_Flag: 0,
  Implementation_Risk_Flag: 1,
};

async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(await response.text() || "Request failed");
  return response.json();
}

function App() {
  const [activeView, setActiveView] = useState("dashboard");
  const [selectedSource, setSelectedSource] = useState("sih"); // "sih" or "synthetic"
  const [sourceMetadata, setSourceMetadata] = useState(null);
  const [paimanaAvailable, setPaimanaAvailable] = useState(true);
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState("PAIMANA-706718");
  const [projectData, setProjectData] = useState(FALLBACK_PAIMANA_PROJECT);
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

  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [llmStatus, setLlmStatus] = useState({ available: false, model: null });
  const [riskSummary, setRiskSummary] = useState(null);

  const [simData, setSimData] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [sliderValues, setSliderValues] = useState({});
  const debounceTimer = useRef(null);
  const [simExplanation, setSimExplanation] = useState("");
  const [isExplaining, setIsExplaining] = useState(false);
  const [savedScenarios, setSavedScenarios] = useState([]);
  const [showCompare, setShowCompare] = useState(false);

  const initVals = {
    Approved_Cost: projectData?.Approved_Cost || 0,
    Expenditure: projectData?.Expenditure || 0,
    Physical_Progress: projectData?.Physical_Progress || 0,
    Financial_Progress: projectData?.Financial_Progress || 0,
    Elapsed_Duration: projectData?.Elapsed_Duration || 0,
    Planned_Duration: projectData?.Planned_Duration || 1,
    Milestones_Delayed: projectData?.Milestones_Delayed || 0,
    Procurement_Delay_Days: projectData?.Procurement_Delay_Days || 0,
  };

  useEffect(() => {
    setSliderValues(initVals);
    setSimData(null);
    setSimExplanation("");
  }, [projectData?.Project_ID]);

  const [scenarioRows, setScenarioRows] = useState([
    { id: 1, field: "Approvals_Pending", value: "" },
  ]);
  const [scenarioMessage, setScenarioMessage] = useState("");

  async function loadProjects(source = "sih") {
    try {
      setLoadingProjects(true);
      setError("");
      const data = await fetchJSON(`${API_BASE}/projects?source=${source}`);
      setSourceMetadata(data);
      const list = data.projects || [];
      if (list.length) {
        setProjects(list);
        setSelectedProjectId(list[0].Project_ID);
        setProjectData(list[0]);
        if (source === "sih") setPaimanaAvailable(true);
      } else {
        if (source === "sih") {
          setPaimanaAvailable(false);
          setError("No official MoSPI PAIMANA records found. Synthetic data will NOT be substituted.");
          setProjects([]);
          setProjectData(null);
          setSelectedProjectId("");
        }
      }
    } catch (err) {
      console.error(err);
      if (source === "sih") {
        setPaimanaAvailable(false);
        setError(`Failed to load official MoSPI PAIMANA dataset: ${err.message}. Per SIH26103 specification, synthetic data is not substituted.`);
        setProjects([]);
        setProjectData(null);
        setSelectedProjectId("");
      } else {
        setProjects([FALLBACK_PROJECT]);
        setProjectData(FALLBACK_PROJECT);
        setSelectedProjectId(FALLBACK_PROJECT.Project_ID);
      }
    } finally {
      setLoadingProjects(false);
    }
  }

  useEffect(() => {
    loadProjects(selectedSource);
  }, []);

  const handleSourceChange = (newSource) => {
    if (newSource === selectedSource) return;
    setSelectedSource(newSource);
    loadProjects(newSource);
  };

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
        setRiskSummary(null);
        setChatMessages([{ role: "assistant", content: "Hello! I am OnTrack AI. I have analyzed this project's parameters and risk profile. How can I help you today?" }]);

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

        // Fetch LLM Status and Risk Summary asynchronously without blocking the UI
        fetchJSON(`${API_BASE}/llm-status`)
          .then(status => {
            setLlmStatus({ available: status.llm_available, model: status.active_model });
            if (status.llm_available) {
              return fetchJSON(`${API_BASE}/risk-summary`, { 
                method: "POST", 
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                  project: projectData, 
                  risk_data: predict.result, 
                  explain_data: explain.result 
                }) 
              });
            }
          })
          .then(summaryData => {
            if (summaryData?.success) setRiskSummary(summaryData.response);
          })
          .catch(e => console.log("LLM features unavailable:", e));

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
  const selectedLabel = useMemo(() => {
    if (projectData?.Project_Name) {
      return `${projectData.Project_ID} — ${projectData.Project_Name}`;
    }
    return `${projectData?.Project_ID || selectedProjectId} — ${projectData?.Sector || ""} / ${projectData?.Project_Type || ""}`;
  }, [projectData, selectedProjectId]);

  const PageHeader = ({ eyebrow, title, description }) => <header className="topbar"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="header-description">{description}</p></div></header>;
  const RiskCard = ({ title, value, description, fillClass }) => <div className="landscape-card"><div className="landscape-top"><span>{title}</span><strong>{value}%</strong></div><div className="landscape-bar"><div className={`landscape-fill ${fillClass}`} style={{ width: `${Number(value) || 0}%` }} /></div><p>{description}</p></div>;

  const SourceSelectorBar = () => (
    <div className="source-selector-bar">
      <div className="source-toggle-group">
        <button
          className={`source-toggle-btn ${selectedSource === "sih" ? "active" : ""}`}
          onClick={() => handleSourceChange("sih")}
        >
          <span>🇮🇳</span> SIH / PAIMANA (MoSPI Official)
        </button>
        <button
          className={`source-toggle-btn ${selectedSource === "synthetic" ? "active" : ""}`}
          onClick={() => handleSourceChange("synthetic")}
        >
          <span>⚙️</span> Synthetic Demo
        </button>
      </div>
      <div className="source-indicator">
        <span className={`source-badge ${selectedSource === "sih" ? "badge-sih" : "badge-synthetic"}`}>
          {selectedSource === "sih" ? "Source: MoSPI PAIMANA" : "Source: Synthetic Demonstration Data"}
        </span>
      </div>
    </div>
  );

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
              <label htmlFor="project-select">Select Project ({projects.length} loaded)</label>

              <select
                id="project-select"
                value={selectedProjectId}
                onChange={handleProjectChange}
                disabled={loadingProjects || !projects.length}
              >
                {projects.map((p) => (
                  <option key={p.Project_ID} value={p.Project_ID}>
                    {p.Project_ID} — {p.Project_Name ? (p.Project_Name.length > 55 ? `${p.Project_Name.substring(0, 52)}...` : p.Project_Name) : `${p.Sector} / ${p.Project_Type}`}
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
            <div className="kpi-card highlight" style={{ gridColumn: '1 / -1', marginBottom: '1rem' }}>
              <span>Executive AI Summary</span>
              <strong>{riskLevel} RISK</strong>
              <small>{riskScore}/100 Composite Score</small>
              {riskSummary ? (
                <p style={{ marginTop: '1rem', fontSize: '0.9rem', lineHeight: 1.5, color: 'var(--text)' }}>
                  {riskSummary}
                </p>
              ) : (
                <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {llmStatus.available ? "Generating AI summary..." : "LLM offline."}
                </p>
              )}
            </div>

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

          {projectData && (selectedSource === "sih" || projectData.Project_Name) && (
            <div className="paimana-project-card">
              <div className="paimana-card-header">
                <div>
                  <h3>{projectData.Project_Name || projectData.Project_ID}</h3>
                  <p><strong>Ministry:</strong> {projectData.Line_Ministry || "Ministry of Statistics & Programme Implementation"} &bull; <strong>Executing Agency:</strong> {projectData.Executing_Agency || "Central Infrastructure PSU"}</p>
                </div>
                <span className="source-badge badge-sih">Source: MoSPI PAIMANA</span>
              </div>
              <div className="paimana-meta-grid">
                <div className="paimana-meta-item">
                  <span>Sector</span>
                  <strong>{projectData.Sector || "--"}</strong>
                </div>
                <div className="paimana-meta-item">
                  <span>Approved Sanction Cost</span>
                  <strong>{projectData.Approved_Cost ? `₹${Number(projectData.Approved_Cost).toLocaleString()} Cr` : "--"}</strong>
                </div>
                <div className="paimana-meta-item">
                  <span>Cumulative Expenditure</span>
                  <strong>{projectData.Expenditure ? `₹${Number(projectData.Expenditure).toLocaleString()} Cr` : "--"}</strong>
                </div>
                <div className="paimana-meta-item">
                  <span>Physical Progress</span>
                  <strong>{projectData.Physical_Progress !== null && projectData.Physical_Progress !== undefined ? `${projectData.Physical_Progress}%` : "--"}</strong>
                </div>
                <div className="paimana-meta-item">
                  <span>Financial Progress</span>
                  <strong>{projectData.Financial_Progress !== null && projectData.Financial_Progress !== undefined ? `${projectData.Financial_Progress}%` : "--"}</strong>
                </div>
                <div className="paimana-meta-item">
                  <span>Schedule Slippage</span>
                  <strong style={{ color: Number(projectData.Time_Overrun_Months || 0) > 0 ? "#dc2626" : "#16a34a" }}>
                    {projectData.Time_Overrun_Months !== null && projectData.Time_Overrun_Months !== undefined ? (Number(projectData.Time_Overrun_Months) > 0 ? `${projectData.Time_Overrun_Months} mo delay` : "On Schedule") : "--"}
                  </strong>
                </div>
                <div className="paimana-meta-item">
                  <span>Cost Escalation</span>
                  <strong style={{ color: Number(projectData.Cost_Overrun_Pct || 0) > 0 ? "#dc2626" : "#16a34a" }}>
                    {projectData.Cost_Overrun_Pct !== null && projectData.Cost_Overrun_Pct !== undefined ? (Number(projectData.Cost_Overrun_Pct) > 0 ? `+${projectData.Cost_Overrun_Pct}% overrun` : "Within Sanction") : "--"}
                  </strong>
                </div>
                <div className="paimana-meta-item">
                  <span>Planned Duration</span>
                  <strong>{projectData.Planned_Duration ? `${projectData.Planned_Duration} mo` : "--"}</strong>
                </div>
              </div>
            </div>
          )}
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
    return (
      <>
        <PageHeader eyebrow="RISK INTELLIGENCE" title="Risk Analysis" description="Identify the key factors contributing to project risk." />

        <section className="section">
          <div className="section-heading">
            <div>
              <h2>Current Project Risk</h2>
              <p>{selectedLabel}</p>
            </div>
            <div className="risk-score-display">
              <span>Overall Risk</span>
              <strong>{loading ? "--" : riskScore ?? "--"}</strong>
              <small>{riskLevel}</small>
            </div>
          </div>
          <div className="risk-landscape-grid">
            <RiskCard title="Time Overrun Risk" value={timeRisk} description="Likelihood of schedule delay" fillClass="time" />
            <RiskCard title="Cost Overrun Risk" value={costRisk} description="Likelihood of exceeding the approved cost" fillClass="cost" />
            <RiskCard title="Implementation Risk" value={implementationRisk} description="Current risk to project execution" fillClass="implementation" />
          </div>
        </section>
        <section className="section">
          <div className="drivers-layout">
            <div className="driver-panel">
              <div className="panel-heading">
                <div>
                  <h2>Risk Drivers</h2>
                  <p>Key factors contributing to the time overrun risk.</p>
                </div>
              </div>
              {explainData?.time_overrun?.fallback ? (
                <div className="shap-fallback-box">
                  <strong>ℹ️ Explainer Notice:</strong> {explainData.time_overrun.fallback_reason || "SHAP explanation unavailable for this record."}
                  <p style={{ margin: "6px 0 0 0", fontSize: "12px", color: "#64748b" }}>
                    Macro indicators (progress, expenditure, sanction dates) were evaluated directly; unrecorded micro operational factors were safely imputed.
                  </p>
                </div>
              ) : (
                drivers.length ? drivers.slice(0, 6).map((d, i) => {
                  const c = Number(d.contribution ?? d.shap_value ?? 0);
                  return (
                    <div className="driver" key={i}>
                      <div>
                        <span>{d.feature || d.name || d.feature_key || "Project factor"}</span>
                        <strong>Risk Driver</strong>
                      </div>
                      <div className="driver-bar">
                        <div className="driver-fill high" style={{ width: `${Math.min(100, Math.max(8, Math.abs(c) * 70))}%` }} />
                      </div>
                    </div>
                  );
                }) : <p>{loading ? "Analysing risk drivers..." : "No risk drivers available."}</p>
              )}
            </div>
            <div className="driver-panel">
              <div className="panel-heading">
                <div>
                  <h2>Project Factors</h2>
                  <p>Current indicators used by the prediction models.</p>
                </div>
              </div>
              <div className="status-grid">
                {selectedSource === "sih"
                  ? [
                      ["Approved Cost", projectData.Approved_Cost ? `₹${projectData.Approved_Cost} Cr` : "--"],
                      ["Expenditure", projectData.Expenditure ? `₹${projectData.Expenditure} Cr` : "--"],
                      ["Physical Progress", projectData.Physical_Progress !== null && projectData.Physical_Progress !== undefined ? `${projectData.Physical_Progress}%` : "--"],
                      ["Financial Progress", projectData.Financial_Progress !== null && projectData.Financial_Progress !== undefined ? `${projectData.Financial_Progress}%` : "--"],
                      ["Planned Duration", projectData.Planned_Duration ? `${projectData.Planned_Duration} mo` : "--"],
                      ["Time Overrun", projectData.Time_Overrun_Months !== null && projectData.Time_Overrun_Months !== undefined ? `${projectData.Time_Overrun_Months} mo` : "On Schedule"],
                      ["Cost Overrun %", projectData.Cost_Overrun_Pct !== null && projectData.Cost_Overrun_Pct !== undefined ? `${projectData.Cost_Overrun_Pct}%` : "0%"],
                      ["Sector", projectData.Sector || "--"],
                    ].map(([a, b]) => <div key={a}><span>{a}</span><strong>{b}</strong></div>)
                  : [
                      ["Physical Progress", `${projectData.Physical_Progress}%`],
                      ["Planned Progress", `${projectData.Planned_Progress}%`],
                      ["Financial Progress", `${projectData.Financial_Progress}%`],
                      ["Land Acquisition", `${projectData.Land_Acquisition_Progress}%`],
                      ["Procurement Delay", `${projectData.Procurement_Delay_Days} days`],
                      ["Pending Approvals", projectData.Approvals_Pending],
                    ].map(([a, b]) => <div key={a}><span>{a}</span><strong>{b}</strong></div>)
                }
              </div>
            </div>
          </div>
        </section>
      </>
    );
  }

  function Benchmark() {
    const m = benchmarkData?.metrics || {};
    const rows = [
      ["Physical Progress", m.physical_progress],
      ["Financial Progress", m.financial_progress],
      ["Schedule Overrun (Months)", m.time_overrun_months],
      ["Cost Overrun (%)", m.cost_overrun_pct],
      ["Procurement Delay", m.procurement_delay_days],
      ["Milestone Delay", m.average_milestone_delay_days],
      ["Pending Approvals", m.approvals_pending],
      ["Land Acquisition", m.land_acquisition_progress],
      ["Overall Risk Score", m.overall_risk_score]
    ];

    return (
      <>
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
    );
  }


  function Scenario() {
    // Baseline metrics using EVM
    const baseline_physical = initVals.Physical_Progress || 1;
    const baseline_eac_cost = initVals.Approved_Cost > 0 ? (initVals.Expenditure / (baseline_physical / 100)) : 0;
    const baseline_cost_overrun = Math.max(0, baseline_eac_cost - initVals.Approved_Cost);
    const baseline_cost_overrun_pct = initVals.Approved_Cost > 0 ? (baseline_cost_overrun / initVals.Approved_Cost) * 100 : 0;
    
    const baseline_eac_time = initVals.Planned_Duration > 0 ? (initVals.Elapsed_Duration / (baseline_physical / 100)) : 0;
    const baseline_time_overrun = Math.max(0, baseline_eac_time - initVals.Planned_Duration);

    // Scenario metrics using EVM
    const scen_physical = sliderValues.Physical_Progress || 1;
    const scen_eac_cost = initVals.Approved_Cost > 0 ? (sliderValues.Expenditure / (scen_physical / 100)) : 0;
    const scen_cost_overrun = Math.max(0, scen_eac_cost - initVals.Approved_Cost);
    const scen_cost_overrun_pct = initVals.Approved_Cost > 0 ? (scen_cost_overrun / initVals.Approved_Cost) * 100 : 0;
    
    const scen_eac_time = initVals.Planned_Duration > 0 ? (sliderValues.Elapsed_Duration / (scen_physical / 100)) : 0;
    const scen_time_overrun = Math.max(0, scen_eac_time - initVals.Planned_Duration);

    const cost_diff = scen_cost_overrun_pct - baseline_cost_overrun_pct;
    const time_diff = scen_time_overrun - baseline_time_overrun;

    const baseRisk = projectData?.Overall_Risk_Score || 0;
    const baseRiskLvl = projectData?.Risk_Level || "LOW";
    const scenRisk = simData ? simData.scenario_prediction.overall_risk_score : baseRisk;
    const scenRiskLvl = simData ? simData.scenario_prediction.risk_level : baseRiskLvl;
    const riskDiff = scenRisk - baseRisk;

    const topDrivers = explainData?.shap_explanations?.overall_risk?.slice(0, 3) || [];

    const runSimulation = async (newVals) => {
      if (!projectData) return;
      setIsSimulating(true);
      const mods = {};
      for (let k in newVals) {
        if (newVals[k] !== initVals[k]) {
          mods[k] = newVals[k];
        }
      }
      if (Object.keys(mods).length === 0) {
        setSimData(null);
        setIsSimulating(false);
        return;
      }
      try {
        const body = { project: projectData, modifications: mods, include_explanations: true };
        const data = await fetchJSON(`${API_BASE}/what-if`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        setSimData(data.result);
      } catch (e) {
        console.error("Simulation error:", e);
      } finally {
        setIsSimulating(false);
      }
    };

    const handleSliderChange = (field, val) => {
      const newVals = { ...sliderValues, [field]: Number(val) };
      setSliderValues(newVals);
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
      debounceTimer.current = setTimeout(() => runSimulation(newVals), 300);
    };

    const applyPreset = (preset) => {
      let newVals = { ...sliderValues };
      if (preset === "optimistic") {
        newVals.Physical_Progress = Math.min(100, initVals.Physical_Progress + 20);
        newVals.Milestones_Delayed = Math.max(0, initVals.Milestones_Delayed - 2);
      } else if (preset === "pessimistic") {
        newVals.Physical_Progress = Math.max(0, initVals.Physical_Progress - 15);
        newVals.Elapsed_Duration = initVals.Elapsed_Duration + 3;
        newVals.Milestones_Delayed = initVals.Milestones_Delayed + 3;
      } else if (preset === "resources") {
        newVals.Expenditure = initVals.Expenditure + (initVals.Approved_Cost * 0.1);
        newVals.Physical_Progress = Math.min(100, initVals.Physical_Progress + 10);
      } else if (preset === "delay6") {
        newVals.Elapsed_Duration = initVals.Elapsed_Duration + 6;
      } else if (preset === "reset") {
        newVals = initVals;
      }
      setSliderValues(newVals);
      if (preset === "reset") {
        setSimData(null);
      } else {
        runSimulation(newVals);
      }
    };

    const explainScenario = async () => {
      setIsExplaining(true);
      const prompt = `The user is simulating a what-if scenario for project ${projectData.Project_ID}.
Baseline Overall Risk: ${baseRisk}
Scenario Overall Risk: ${scenRisk}
Scenario Risk Level: ${scenRiskLvl}
Baseline Cost Overrun: ${baseline_cost_overrun_pct.toFixed(1)}% -> Scenario: ${scen_cost_overrun_pct.toFixed(1)}%
Baseline Time Overrun: ${baseline_time_overrun.toFixed(1)} mos -> Scenario: ${scen_time_overrun.toFixed(1)} mos
Changes applied: ${simData ? simData.modifications_applied.map(c => `${c.feature}: from ${c.original_value} to ${c.scenario_value}`).join(", ") : "None"}
Please explain in 3-4 simple sentences what changed, why the risk increased or decreased based on these changes, and what management action to take. DO NOT invent numbers.`;

      try {
        const body = {
          message: prompt,
          project: projectData,
          model: llmStatus.model
        };
        const res = await fetchJSON(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        setSimExplanation(res.response);
      } catch (e) {
        setSimExplanation("Error generating explanation.");
      } finally {
        setIsExplaining(false);
      }
    };

    const saveScenario = () => {
      if (savedScenarios.length >= 3) {
        alert("Maximum 3 scenarios can be saved.");
        return;
      }
      setSavedScenarios([...savedScenarios, {
        name: `Scenario ${savedScenarios.length + 1}`,
        risk: scenRisk,
        cost: scen_cost_overrun_pct,
        time: scen_time_overrun
      }]);
    };

    return (
      <div className="scenario-page">
        <div className="scenario-header">
          <div>
            <span className="eyebrow">WHAT-IF SIMULATOR</span>
            <h1>Scenario Analysis</h1>
            <p>Evaluate how proposed project changes may affect the overall risk.</p>
          </div>
          <div className="project-selector">
            <select 
              value={selectedProjectId} 
              onChange={e => {
                const p = projects.find(x => x.Project_ID === e.target.value);
                if (p) {
                  setSelectedProjectId(p.Project_ID);
                  setProjectData(p);
                }
              }}
            >
              {projects.map(p => (
                <option key={p.Project_ID} value={p.Project_ID}>
                  {p.Project_Name} ({p.Sector} - {p.Ministry})
                </option>
              ))}
            </select>
          </div>
        </div>

        <section className="scenario-grid">
          <div className="scenario-left-panel card">
            <h2>Adjust Variables</h2>
            
            <div className="preset-chips">
              <button className={`preset-pill ${sliderValues === initVals ? 'active' : ''}`} onClick={() => applyPreset("optimistic")}>Optimistic</button>
              <button className="preset-pill" onClick={() => applyPreset("pessimistic")}>Pessimistic</button>
              <button className="preset-pill" onClick={() => applyPreset("resources")}>Add Resources</button>
              <button className="preset-pill" onClick={() => applyPreset("delay6")}>Delay 6 Mos</button>
              <button className="preset-pill reset" onClick={() => applyPreset("reset")}>Reset</button>
            </div>

            <div className="custom-slider">
              <div className="slider-header">
                <label htmlFor="phys-prog">Physical Progress (%)</label>
                <span className="slider-badge">{sliderValues.Physical_Progress}%</span>
              </div>
              <input id="phys-prog" type="range" min="0" max="100" step="1" value={sliderValues.Physical_Progress} onChange={e => handleSliderChange("Physical_Progress", e.target.value)} />
              <div className="slider-footer">Original: {initVals.Physical_Progress} <button onClick={() => handleSliderChange("Physical_Progress", initVals.Physical_Progress)}>↺</button></div>
            </div>
            
            <div className="custom-slider">
              <div className="slider-header">
                <label htmlFor="exp-cr">Expenditure (Cr)</label>
                <span className="slider-badge">{sliderValues.Expenditure} Cr</span>
              </div>
              <input id="exp-cr" type="range" min="0" max={Math.max(initVals.Approved_Cost * 2, initVals.Expenditure * 2, 100)} step="1" value={sliderValues.Expenditure} onChange={e => handleSliderChange("Expenditure", e.target.value)} />
              <div className="slider-footer">Original: {initVals.Expenditure} <button onClick={() => handleSliderChange("Expenditure", initVals.Expenditure)}>↺</button></div>
            </div>

            <div className="custom-slider">
              <div className="slider-header">
                <label htmlFor="elap-dur">Elapsed Duration (Months)</label>
                <span className="slider-badge">{sliderValues.Elapsed_Duration} mos</span>
              </div>
              <input id="elap-dur" type="range" min="0" max={Math.max(initVals.Planned_Duration * 3, initVals.Elapsed_Duration * 2, 24)} step="1" value={sliderValues.Elapsed_Duration} onChange={e => handleSliderChange("Elapsed_Duration", e.target.value)} />
              <div className="slider-footer">Original: {initVals.Elapsed_Duration} <button onClick={() => handleSliderChange("Elapsed_Duration", initVals.Elapsed_Duration)}>↺</button></div>
            </div>

            <div className="custom-slider">
              <div className="slider-header">
                <label htmlFor="miles-del">Milestones Delayed</label>
                <span className="slider-badge">{sliderValues.Milestones_Delayed}</span>
              </div>
              <input id="miles-del" type="range" min="0" max="20" step="1" value={sliderValues.Milestones_Delayed} onChange={e => handleSliderChange("Milestones_Delayed", e.target.value)} />
              <div className="slider-footer">Original: {initVals.Milestones_Delayed} <button onClick={() => handleSliderChange("Milestones_Delayed", initVals.Milestones_Delayed)}>↺</button></div>
            </div>
            
            <div className="action-row">
              <button className="action-btn" onClick={() => applyPreset("reset")}>Reset All</button>
              <button className="action-btn primary" onClick={saveScenario}>Save Scenario</button>
              <button className="action-btn" onClick={() => setShowCompare(!showCompare)}>Compare Saved ({savedScenarios.length})</button>
            </div>
            
            {showCompare && savedScenarios.length > 0 && (
              <div className="compare-table">
                <table>
                  <thead>
                    <tr>
                      <th>Scenario</th>
                      <th>Risk</th>
                      <th>Cost Overrun</th>
                      <th>Time Overrun</th>
                    </tr>
                  </thead>
                  <tbody>
                    {savedScenarios.map((s, i) => (
                      <tr key={i}>
                        <td>{s.name}</td>
                        <td>{s.risk.toFixed(1)}</td>
                        <td>{s.cost.toFixed(1)}%</td>
                        <td>{s.time.toFixed(1)} m</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="scenario-right-panel card">
            <div className="panel-heading">
              <h2>Live Results {isSimulating && <span className="loading-spinner small"></span>}</h2>
            </div>
            
            <div className="metric-cards">
              <div className="metric-card risk-card">
                <div className="gauge-container">
                  <svg viewBox="0 0 100 50" className="semi-gauge">
                    <path className="gauge-bg" d="M 10 50 A 40 40 0 0 1 90 50" />
                    <path className="gauge-fill" d="M 10 50 A 40 40 0 0 1 90 50" strokeDasharray={`${(scenRisk / 100) * 125.6} 125.6`} />
                  </svg>
                  <div className="gauge-value">{scenRisk.toFixed(1)}</div>
                </div>
                <h3>Risk Score</h3>
                <span className={`risk-badge risk-${scenRiskLvl.toLowerCase()}`}>{scenRiskLvl}</span>
                <div className="delta-stat">
                  Base: {baseRisk.toFixed(1)} 
                  {riskDiff !== 0 && (
                    <span className={`diff ${riskDiff > 0 ? "worse" : "better"}`}>
                      {riskDiff > 0 ? "▲" : "▼"} {Math.abs(riskDiff).toFixed(1)}
                    </span>
                  )}
                </div>
              </div>

              <div className="metric-card">
                <h3>Cost Overrun</h3>
                <div className="metric-value">{scen_cost_overrun_pct.toFixed(1)}%</div>
                <div className="sub-value">₹{scen_cost_overrun.toFixed(1)} Cr</div>
                <div className="delta-stat">
                  Base: {baseline_cost_overrun_pct.toFixed(1)}%
                  {cost_diff !== 0 && (
                    <span className={`diff ${cost_diff > 0 ? "worse" : "better"}`}>
                      {cost_diff > 0 ? "▲" : "▼"} {Math.abs(cost_diff).toFixed(1)}pp
                    </span>
                  )}
                </div>
              </div>

              <div className="metric-card">
                <h3>Time Overrun</h3>
                <div className="metric-value">{scen_time_overrun.toFixed(1)} <small>mos</small></div>
                <div className="delta-stat">
                  Base: {baseline_time_overrun.toFixed(1)}
                  {time_diff !== 0 && (
                    <span className={`diff ${time_diff > 0 ? "worse" : "better"}`}>
                      {time_diff > 0 ? "▲" : "▼"} {Math.abs(time_diff).toFixed(1)}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="scenario-chart-container">
              <h3>Baseline vs Scenario Comparison</h3>
              <div className="bar-chart">
                <div className="bar-row">
                  <span className="bar-label">Risk</span>
                  <div className="bar-track">
                    <div className="bar base" style={{ width: `${baseRisk}%` }}>{baseRisk.toFixed(1)}</div>
                    <div className="bar scen" style={{ width: `${scenRisk}%` }}>{scenRisk.toFixed(1)}</div>
                  </div>
                </div>
                <div className="bar-row">
                  <span className="bar-label">Cost Ovr (%)</span>
                  <div className="bar-track">
                    <div className="bar base" style={{ width: `${Math.min(baseline_cost_overrun_pct, 100)}%` }}>{baseline_cost_overrun_pct.toFixed(1)}%</div>
                    <div className="bar scen" style={{ width: `${Math.min(scen_cost_overrun_pct, 100)}%` }}>{scen_cost_overrun_pct.toFixed(1)}%</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="shap-drivers">
              <h3>Top Baseline Drivers</h3>
              {topDrivers.length > 0 ? topDrivers.map((driver, i) => (
                <div className="driver-bar-row" key={i}>
                  <div className="driver-name">{driver.feature} ({driver.value})</div>
                  <div className="driver-impact-bar" style={{ width: `${Math.min(Math.abs(driver.shap_value) * 100, 100)}%` }}></div>
                </div>
              )) : (
                <p>No driver data available.</p>
              )}
            </div>
            
            <p className="disclaimer">Estimates are model-based EVM predictions and statistical probabilities, not guaranteed outcomes.</p>

            <button className="explain-btn" onClick={explainScenario} disabled={isExplaining}>
              {isExplaining ? "Generating AI Explanation..." : "Explain this scenario"}
            </button>
            {simExplanation && (
              <div className="ai-explanation">
                {simExplanation}
              </div>
            )}
          </div>
        </section>
      </div>
    );
  }


  function Recommendations() {
    return (
      <>
        <PageHeader eyebrow="DECISION SUPPORT" title="Action Recommendations" description="Get prioritized actions based on identified project risks." />

        <section className="section">
          <div className="driver-panel">
            <div className="panel-heading">
              <div>
                <h2>Recommended Actions</h2>
                <p>Actions generated from the selected project's current risk indicators.</p>
              </div>
            </div>
            {recommendations.length ? (
              <div className="recommendation-list">
                {recommendations.map((r, i) => {
                  const p = r.priority || r.severity || r.level || "Medium";
                  const title = r.title || r.action || r.recommendation || `Recommended action ${i + 1}`;
                  const desc = r.description || r.reason || r.message || r.action_description || "";
                  return (
                    <div className="warning-item" key={i}>
                      <span className="warning-icon">✓</span>
                      <div>
                        <strong>{p} Priority &bull; {title}</strong>
                        <p>{desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p>{loading ? "Generating recommendations..." : "No recommendations were returned for this project."}</p>
            )}
          </div>
        </section>
      </>
    );
  }

  function EarlyWarnings() {
    return (
      <>
        <PageHeader eyebrow="EARLY WARNING MONITORING" title="Early Warnings" description="Review current conditions that may require closer project monitoring." />

        <section className="section">
          <div className="summary-grid">
            <div className="summary-card">
              <span>Warning Level</span>
              <strong>{warningData?.warning_level ?? "--"}</strong>
              <small>{warningData?.message ?? "Current monitoring status"}</small>
            </div>
            <div className="summary-card">
              <span>Overall Risk</span>
              <strong>{warningData?.risk_score ?? "--"}</strong>
              <small>Current model risk score</small>
            </div>
            <div className="summary-card">
              <span>Schedule Slippage</span>
              <strong>{projectData.Time_Overrun_Months !== null && projectData.Time_Overrun_Months !== undefined ? `${projectData.Time_Overrun_Months} mo` : "--"}</strong>
              <small>{selectedSource === "sih" ? "Official delay" : "Current indicator"}</small>
            </div>
            <div className="summary-card">
              <span>Cost Escalation</span>
              <strong>{projectData.Cost_Overrun_Pct !== null && projectData.Cost_Overrun_Pct !== undefined ? `${projectData.Cost_Overrun_Pct}%` : "--"}</strong>
              <small>{selectedSource === "sih" ? "Official escalation" : "Current indicator"}</small>
            </div>
          </div>
        </section>
        <section className="section">
          <div className="driver-panel warning-panel">
            <div className="panel-heading">
              <div>
                <h2>Warning Signals</h2>
                <p>Conditions currently contributing to project risk.</p>
              </div>
            </div>
            {warnings.length ? (
              warnings.map((w, i) => (
                <div className="warning-item" key={i}>
                  <span className="warning-icon">!</span>
                  <div>
                    <strong>Risk signal detected</strong>
                    <p>{typeof w === "string" ? w : w.message}</p>
                  </div>
                </div>
              ))
            ) : (
              <p>{loading ? "Analysing project conditions..." : "No warning signals detected for this project."}</p>
            )}
          </div>
        </section>
      </>
    );
  }

  function AIChat() {
    const handleSend = async () => {
      if (!chatInput.trim()) return;
      
      const newMessages = [...chatMessages, { role: "user", content: chatInput }];
      setChatMessages(newMessages);
      setChatInput("");
      setIsChatLoading(true);

      try {
        const response = await fetchJSON(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: chatInput,
            project: projectData,
            risk_data: riskData,
            explain_data: explainData,
            history: chatMessages
          })
        });

        if (response.success) {
          setChatMessages([...newMessages, { role: "assistant", content: response.response }]);
        } else {
          setChatMessages([...newMessages, { role: "assistant", content: `Error: ${response.error}` }]);
        }
      } catch (err) {
        setChatMessages([...newMessages, { role: "assistant", content: "Sorry, I could not reach the LLM service." }]);
      } finally {
        setIsChatLoading(false);
      }
    };

    return (
      <>
        <PageHeader eyebrow="PROJECT ASSISTANT" title="AI Chat" description="Ask natural language questions about this project's risks and recommendations." />

        
        <section className="section">
          {!llmStatus.available ? (
            <div className="prototype-notice" style={{ borderColor: 'var(--error)' }}>
              <strong>LLM Offline:</strong> The Groq API is not reachable or XAI_API_KEY is not set. Please ensure your <code>.env</code> file contains a valid <code>XAI_API_KEY</code> and you have internet connectivity.
            </div>
          ) : (
            <div className="chat-container">
              <div className="chat-messages" style={{ minHeight: '400px', maxHeight: '500px', overflowY: 'auto', background: 'var(--surface)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
                {chatMessages.map((msg, i) => (
                  <div key={i} style={{ marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>{msg.role === 'user' ? 'You' : 'OnTrack AI'}</div>
                    <div style={{ 
                      background: msg.role === 'user' ? 'var(--primary)' : 'var(--surface-hover)', 
                      color: msg.role === 'user' ? 'white' : 'var(--text)',
                      padding: '1rem', 
                      borderRadius: '8px', 
                      maxWidth: '80%',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {isChatLoading && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>OnTrack AI</div>
                    <div style={{ background: 'var(--surface-hover)', padding: '1rem', borderRadius: '8px' }}>
                      <span className="loading-spinner" style={{ width: '16px', height: '16px', borderWidth: '2px', margin: 0 }}></span>
                    </div>
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                <input 
                  type="text" 
                  value={chatInput} 
                  onChange={e => setChatInput(e.target.value)} 
                  onKeyDown={e => e.key === 'Enter' && handleSend()}
                  placeholder="Ask about project delays, budget, or risks..."
                  style={{ flex: 1, padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
                  disabled={isChatLoading}
                />
                <button 
                  onClick={handleSend} 
                  disabled={isChatLoading || !chatInput.trim()}
                  style={{ padding: '0 2rem', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 500 }}
                >
                  Send
                </button>
              </div>
            </div>
          )}
        </section>
      </>
    );
  }

  function ActivePage() {
    if (activeView === "risk") return RiskAnalysis();
    if (activeView === "benchmark") return Benchmark();
    if (activeView === "scenario") return Scenario();
    if (activeView === "recommendations") return Recommendations();
    if (activeView === "warnings") return EarlyWarnings();
    if (activeView === "chat") return AIChat();
    return Dashboard();
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">SIH</div>
          <div>
            <h2>OnTrack AI</h2>
            <span>Team Kratarthaka</span>
          </div>
        </div>
        <nav className="navigation">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeView === item.id ? "active" : ""}`}
              onClick={() => goTo(item.id)}
            >
              <span>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="status-dot" style={{ background: llmStatus.available ? 'var(--success)' : 'var(--error)' }} />
          {llmStatus.available ? `AI: ${llmStatus.model}` : "AI Offline"}
        </div>
      </aside>

      <main className="main-content">
        {loading ? (
          <div className="loading-screen">
            <div className="loading-spinner"></div>
            <h2>Connecting to OnTrack AI...</h2>
            <p>
              The AI service is waking up. Please wait a few seconds while
              project intelligence is loaded.
            </p>
          </div>
        ) : (
          <>
            {error && (
              <div className="prototype-notice">
                <strong>Notice:</strong> {error}
              </div>
            )}

            {ActivePage()}

            <div className="prototype-notice">
              {selectedSource === "sih" ? (
                <>
                  <strong>Source: MoSPI PAIMANA.</strong> Official Infrastructure Projects dataset from the Ministry of Statistics & Programme Implementation (August 2026 Snapshot). Tracking {projects.length} Central Sector Infrastructure Projects. Operational granularities without official publication are kept unrecorded.
                </>
              ) : (
                <>
                  <strong>Source: Synthetic Demonstration Data.</strong> This prototype uses representative synthetic project data with parameters referenced from the "PAIMAANA April 2026 report". Results should be recalibrated using verified government project data before real-world deployment.
                </>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
