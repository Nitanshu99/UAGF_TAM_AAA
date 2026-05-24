import { useState } from "react";

const SCHEMA_VERSION = "1.0.0";
const AGREED_WEEK = 4;

const SECTIONS = [
  {
    id: "metadata",
    label: "metadata",
    tag: "REQUIRED",
    tagColor: "#185FA5",
    description: "Identifies the organisation, AI system under audit, and the CGSA run. Used by AAA to match governance phase input to the correct Phase 1 Scope classification.",
    fields: [
      { name: "assessment_id", type: "string (uuid)", required: true, description: "Unique CGSA run identifier. AAA uses this to deduplicate and trace governance phase input.", example: '"a3f7c2d1-8b4e-4f9a-bc12-0e5d6f7a8b9c"' },
      { name: "organisation_name", type: "string", required: true, description: "Organisation whose governance documentation was assessed.", example: '"Hamburg Hub GmbH"' },
      { name: "system_under_audit", type: "string", required: true, description: "Name or ID of the specific AI system. AAA matches this to the Phase 1 (Scope) system identifier.", example: '"Credit Risk Scoring Model v2.1"' },
      { name: "cgsa_version", type: "string", required: true, description: "Semantic version of the CGSA tool.", example: '"1.0.0"' },
      { name: "assessment_timestamp", type: "string (ISO 8601)", required: true, description: "When the CGSA assessment completed.", example: '"2026-03-16T14:30:00Z"' },
      { name: "risk_tier", type: "enum", required: true, description: "EU AI Act risk tier. Determines which hard constraints are active in the CSP model. AAA confirms this matches Phase 1 output.", values: ["minimal", "limited", "high"], example: '"high"' },
      { name: "document_sources", type: "string[]", required: true, description: "Governance document filenames parsed by the LangChain pipeline.", example: '["AI_Policy_v3.pdf", "Risk_Management_Framework.docx"]' },
      { name: "uagf_gmm_version", type: "string", required: false, description: "Version of the 38-control UAGF-GMM library used for scoring.", example: '"1.0.0"' },
    ],
  },
  {
    id: "overall_scores",
    label: "overall_scores",
    tag: "REQUIRED",
    tagColor: "#185FA5",
    description: "Top-level summary scores consumed by AAA for the Phase 5 executive summary and the audit report compliance matrix.",
    fields: [
      { name: "composite_maturity_score", type: "float (0.0–4.0)", required: true, description: "Weighted average maturity score across all 38 controls. 0=Absent → 4=Optimised.", example: "2.7" },
      { name: "composite_maturity_label", type: "enum", required: true, description: "Human-readable label for the composite score band.", values: ["absent", "initial", "developing", "defined", "optimised"], example: '"developing"' },
      { name: "eu_ai_act_coverage_pct", type: "float (0–100)", required: true, description: "Percentage of EU AI Act Arts. 9, 10, 13 requirements satisfied by controls meeting or exceeding their thresholds.", example: "68.4" },
      { name: "csp_satisfiable", type: "boolean", required: true, description: "Whether the python-constraint CSP solver found a valid assignment. FALSE = hard constraint violation = non-compliant. AAA uses this as a binary gate for Phase 5 verdict.", example: "false" },
      { name: "governance_verdict", type: "enum", required: true, description: "Overall governance compliance verdict. Derived from csp_satisfiable and coverage_pct. AAA inserts this directly into Phase 5.", values: ["compliant", "partially_compliant", "non_compliant"], example: '"partially_compliant"' },
      { name: "controls_assessed", type: "integer", required: false, description: "Total controls scored (should equal 38 for full run).", example: "38" },
      { name: "controls_meeting_threshold", type: "integer", required: false, description: "Controls meeting or exceeding their required threshold for the risk_tier.", example: "24" },
      { name: "controls_below_threshold", type: "integer", required: false, description: "Controls failing the minimum required threshold. AAA uses this count in the Phase 5 gap summary.", example: "14" },
    ],
  },
  {
    id: "domains",
    label: "domains [ ]",
    tag: "REQUIRED · 6 items",
    tagColor: "#0F6E56",
    description: "The 6 governance domains of the UAGF-GMM, each containing their controls. AAA iterates these to populate the Phase 5 governance findings table.",
    nested: true,
    domainNames: [
      "D1 — Risk Management",
      "D2 — Data Governance",
      "D3 — Model Development and Testing",
      "D4 — Transparency and Explainability",
      "D5 — Human Oversight and Accountability",
      "D6 — Monitoring and Incident Response",
    ],
    fields: [
      { name: "domain_id", type: "enum", required: true, description: "Domain identifier.", values: ["D1", "D2", "D3", "D4", "D5", "D6"] },
      { name: "domain_name", type: "string", required: true, description: "Human-readable domain name (see 6 domains above)." },
      { name: "domain_score", type: "float (0.0–4.0)", required: true, description: "Mean maturity score across all controls in this domain." },
      { name: "domain_eu_ai_act_articles", type: "string[]", required: false, description: "EU AI Act articles primarily satisfied by controls in this domain.", example: '["Article 9", "Article 10"]' },
      { name: "controls [ ]", type: "object[]", required: true, description: "Individual UAGF-GMM controls for this domain. Each control contains the fields below.", isControlsHeader: true },
    ],
    controlFields: [
      { name: "control_id", type: "string (C01–C38)", required: true, description: "Unique control identifier across all 38 UAGF-GMM controls.", example: '"C07"' },
      { name: "control_name", type: "string", required: true, description: "Short descriptive name.", example: '"Data Quality Management"' },
      { name: "control_description", type: "string", required: false, description: "Full description including what each maturity level means for this control." },
      { name: "source_frameworks", type: "string[]", required: false, description: "Subset of the 12 synthesised standards from which this control was derived.", example: '["EU AI Act", "ISO 42001", "NIST AI RMF"]' },
      { name: "maturity_score", type: "integer (0–4)", required: true, description: "Ordinal score assigned by the CSP solver. 0=Absent, 1=Initial, 2=Developing, 3=Defined, 4=Optimised.", example: "2" },
      { name: "maturity_label", type: "enum", required: true, description: "Human-readable label for maturity_score.", values: ["absent", "initial", "developing", "defined", "optimised"] },
      { name: "maturity_descriptor", type: "string", required: false, description: "Full text description of what the assigned maturity level means for this specific control." },
      { name: "evidence_summary", type: "string", required: true, description: "Condensed excerpt from governance documents supporting this score. AAA may include this in the Phase 5 findings table.", example: '"Policy doc Section 3.2 references data quality checks but no automated validation pipeline is documented."' },
      { name: "evidence_source_document", type: "string", required: false, description: "Filename of the source document.", example: '"AI_Policy_v3.pdf"' },
      { name: "evidence_page_reference", type: "string | null", required: false, description: "Page or section reference within the source document.", example: '"p. 14, Section 3.2"' },
      { name: "confidence", type: "float (0.0–1.0)", required: true, description: "LangChain parser confidence for evidence extraction. Values < 0.60 are flagged by AAA for human reviewer verification.", example: "0.82" },
      { name: "eu_ai_act_articles", type: "string[]", required: true, description: "EU AI Act articles this control directly addresses. AAA uses these to build the regulatory compliance matrix.", example: '["Article 10 point 2", "Article 10 point 3"]' },
      { name: "hard_constraint.applicable", type: "boolean", required: true, description: "Whether a hard constraint applies to this control under the assessed risk_tier. High-risk systems have more active hard constraints.", example: "true" },
      { name: "hard_constraint.threshold_score", type: "integer | null", required: true, description: "Minimum maturity_score required to satisfy the constraint. NULL if not applicable.", example: "3" },
      { name: "hard_constraint.satisfied", type: "boolean | null", required: true, description: "Whether maturity_score ≥ threshold_score. NULL if not applicable. FALSE = hard constraint violation = blocking compliance gap.", example: "false" },
      { name: "hard_constraint.eu_ai_act_obligation", type: "string | null", required: false, description: "Specific EU AI Act obligation this constraint encodes.", example: '"Article 10 point 2: Training, validation and testing data shall be subject to appropriate data governance..."' },
      { name: "gap_severity", type: "enum | null", required: true, description: "Gap severity. Critical = hard constraint violated on high-risk. High = hard constraint on limited-risk. Medium = soft gap on high-risk. Low = any gap on minimal. NULL if no gap.", values: ["critical", "high", "medium", "low", "null"] },
      { name: "gap_detail", type: "string | null", required: false, description: "Explanation of the gap with what is missing, what is required, and regulatory consequence. AAA uses this text in Phase 5 remediation.", example: '"No automated data validation pipeline documented. Article 10 requires data governance for high-risk systems..."' },
    ],
  },
  {
    id: "eu_ai_act_compliance_matrix",
    label: "eu_ai_act_compliance_matrix",
    tag: "REQUIRED",
    tagColor: "#185FA5",
    description: "Consolidated compliance status by EU AI Act article. AAA inserts this matrix directly into the Phase 5 section of the audit report PDF. Articles 9, 10, 13 are hard-constraint-encoded; 14 and 17 are informationally mapped.",
    articles: [
      { id: "article_9", label: "Article 9", title: "Risk management system", required: true, note: "Hard-constraint-encoded in CGSA v1.0" },
      { id: "article_10", label: "Article 10", title: "Data and data governance", required: true, note: "Hard-constraint-encoded in CGSA v1.0" },
      { id: "article_13", label: "Article 13", title: "Transparency and provision of information", required: true, note: "Hard-constraint-encoded in CGSA v1.0" },
      { id: "article_14", label: "Article 14", title: "Human oversight", required: false, note: "Informational mapping only in v1.0" },
      { id: "article_17", label: "Article 17", title: "Quality management system", required: false, note: "Informational mapping only in v1.0" },
    ],
    fields: [
      { name: "article_reference", type: "string", required: true, description: "EU AI Act article citation.", example: '"Article 9"' },
      { name: "article_title", type: "string", required: true, description: "Article title.", example: '"Risk management system"' },
      { name: "status", type: "enum", required: true, description: "Compliance status for this article based on control scores and hard constraint results.", values: ["satisfied", "partially_satisfied", "not_satisfied"] },
      { name: "controls_mapped", type: "string[]", required: true, description: "Control IDs mapped to this article.", example: '["C01", "C02", "C03", "C04"]' },
      { name: "controls_satisfied", type: "string[]", required: true, description: "Subset of controls_mapped that meet their threshold.", example: '["C01", "C03"]' },
      { name: "coverage_pct", type: "float (0–100)", required: true, description: "Percentage of mapped controls satisfying their threshold for this article.", example: "50.0" },
      { name: "hard_constraints_violated", type: "string[]", required: false, description: "Control IDs with hard constraint violations under this article.", example: '["C02", "C04"]' },
      { name: "article_summary", type: "string", required: false, description: "One-sentence compliance summary. AAA inserts this into the regulatory compliance matrix table.", example: '"Article 9 is partially satisfied: risk identification (C01, C03) documented but mitigation (C02, C04) below threshold."' },
    ],
  },
  {
    id: "hard_constraint_results",
    label: "hard_constraint_results",
    tag: "REQUIRED",
    tagColor: "#185FA5",
    description: "Summary of CSP solver results. AAA uses this as the primary input for the binary compliance gate in Phase 5.",
    fields: [
      { name: "csp_satisfiable", type: "boolean", required: true, description: "Mirrors overall_scores.csp_satisfiable. TRUE = all hard constraints satisfied = governance-compliant for risk tier.", example: "false" },
      { name: "total_hard_constraints", type: "integer", required: false, description: "Total hard constraints active for the assessed risk_tier.", example: "18" },
    ],
    subsections: [
      {
        label: "violated_constraints [ ]",
        tag: "REQUIRED",
        description: "Hard constraint violations. AAA iterates this list to populate the Phase 5 critical findings table. Each item pinpoints the control, article, and gap.",
        fields: [
          { name: "control_id", type: "string", required: true, example: '"C07"' },
          { name: "control_name", type: "string", required: true, example: '"Data Quality Management"' },
          { name: "required_score", type: "integer (0–4)", required: true, example: "3" },
          { name: "actual_score", type: "integer (0–4)", required: true, example: "2" },
          { name: "score_delta", type: "integer", required: false, description: "required_score minus actual_score. AAA uses this to sort violations by severity.", example: "1" },
          { name: "eu_ai_act_article", type: "string", required: true, example: '"Article 10 point 2"' },
          { name: "violation_description", type: "string", required: true, description: "Human-readable violation description for the audit report.", example: '"Data governance practices are developing but not formally defined. A documented data validation pipeline is required."' },
        ],
      },
      {
        label: "satisfied_constraints [ ]",
        tag: "REQUIRED",
        description: "Hard constraints that ARE satisfied. Used for the positive findings section of the audit report.",
        fields: [
          { name: "control_id", type: "string", required: true },
          { name: "control_name", type: "string", required: true },
          { name: "required_score", type: "integer (0–4)", required: true },
          { name: "actual_score", type: "integer (0–4)", required: true },
          { name: "eu_ai_act_article", type: "string", required: true },
        ],
      },
    ],
  },
  {
    id: "remediation_roadmap",
    label: "remediation_roadmap [ ]",
    tag: "REQUIRED",
    tagColor: "#185FA5",
    description: "Ordered list of remediation actions, ranked by gap_severity (critical first), then score_delta. AAA extracts this into the Phase 5 remediation section. Items with gap_severity=critical are surfaced as blocking findings.",
    fields: [
      { name: "rank", type: "integer", required: true, description: "Remediation priority rank. 1 = highest priority.", example: "1" },
      { name: "control_id", type: "string", required: true, example: '"C07"' },
      { name: "control_name", type: "string", required: true, example: '"Data Quality Management"' },
      { name: "gap_severity", type: "enum", required: true, values: ["critical", "high", "medium", "low"] },
      { name: "current_score", type: "integer (0–4)", required: false, example: "2" },
      { name: "target_score", type: "integer (0–4)", required: false, example: "3" },
      { name: "action", type: "string", required: true, description: "Specific, actionable remediation step.", example: '"Define and document a formal data validation pipeline including completeness checks, bias scanning, and dataset version control."' },
      { name: "eu_ai_act_article", type: "string", required: true, description: "The specific EU AI Act article obligation this remediation addresses.", example: '"Article 10 point 2"' },
      { name: "effort_estimate", type: "enum", required: true, description: "Low=documentation update. Medium=process change. High=tooling/system change.", values: ["low", "medium", "high"] },
      { name: "timeline_weeks", type: "integer | null", required: false, example: "4" },
      { name: "priority_rationale", type: "string", required: true, description: "Explanation of ranking. AAA may include this in the Phase 5 narrative.", example: '"Hard constraint violation on high-risk system. Non-compliance with Article 10 is a blocking finding."' },
    ],
  },
  {
    id: "aaa_phase5_handoff",
    label: "aaa_phase5_handoff",
    tag: "PRIMARY INTEGRATION SURFACE",
    tagColor: "#854F0B",
    description: "Dedicated handoff block for AAA Phase 5 (Governance) consumption. Contains pre-computed summary fields that AAA can insert directly into the audit report without re-processing the full domain/control arrays.",
    fields: [
      { name: "phase5_verdict", type: "enum", required: true, description: "Binary-ternary verdict for Phase 5. PASS = csp_satisfiable=true AND coverage ≥80%. PASS_WITH_OBSERVATIONS = csp_satisfiable=true but coverage <80%. FAIL = csp_satisfiable=false. AAA uses this for the traffic-light status in the executive summary.", values: ["PASS", "PASS_WITH_OBSERVATIONS", "FAIL"], example: '"FAIL"' },
      { name: "phase5_narrative_summary", type: "string", required: true, description: "Pre-written 3–5 sentence narrative ready for AAA to insert into Phase 5 with minimal editing. Written in audit report register.", example: '"The governance documentation demonstrates developing maturity (2.7/4.0)..."' },
      { name: "blocking_findings_count", type: "integer", required: true, description: "Count of critical/hard-constraint-violating findings. AAA displays this prominently in Phase 5 header.", example: "3" },
      { name: "blocking_findings [ ]", type: "object[]", required: true, description: "Condensed critical findings for AAA Phase 5 report table. Each item maps to a violated hard constraint.", isBold: true },
      { name: "  control_id", type: "string", required: true, indent: true },
      { name: "  control_name", type: "string", required: true, indent: true },
      { name: "  finding", type: "string", required: true, description: "One-sentence finding in audit register.", indent: true, example: '"No formal data validation pipeline documented; practices are developing but not defined."' },
      { name: "  eu_ai_act_article", type: "string", required: true, indent: true, example: '"Article 10 point 2"' },
      { name: "  remediation_action", type: "string", required: true, description: "Condensed remediation for the audit report table.", indent: true },
      { name: "positive_findings [ ]", type: "object[]", required: true, description: "Controls meeting or exceeding threshold — for the positive findings section of Phase 5.", isBold: true },
      { name: "  control_id", type: "string", required: true, indent: true },
      { name: "  control_name", type: "string", required: true, indent: true },
      { name: "  maturity_score", type: "integer (0–4)", required: true, indent: true },
      { name: "  finding", type: "string", required: true, description: "One-sentence positive finding in audit register.", indent: true },
      { name: "low_confidence_controls [ ]", type: "object[]", required: true, description: "Controls where LangChain extraction confidence < 0.60. AAA flags each in the Phase 5 limitations section and recommends human reviewer verification.", isBold: true },
      { name: "  control_id", type: "string", required: true, indent: true },
      { name: "  control_name", type: "string", required: true, indent: true },
      { name: "  confidence", type: "float (0.0–1.0)", required: true, indent: true },
      { name: "  flag_reason", type: "string", required: true, description: "Reason for low confidence.", indent: true, example: '"Governance document contains no dedicated risk management section; score inferred from meeting minutes."' },
      { name: "aaa_recommended_follow_up [ ]", type: "object[]", required: true, description: "CGSA-recommended follow-up actions for AAA Phase 5 — e.g. requesting additional documents, scheduling interviews, escalating to human reviewer.", isBold: true },
      { name: "  recommendation", type: "string", required: true, indent: true },
      { name: "  rationale", type: "string", required: true, indent: true },
      { name: "  urgency", type: "enum", required: false, indent: true, values: ["required_before_report_completion", "recommended", "optional"] },
      { name: "cgsa_report_url", type: "string (uri) | null", required: false, description: "URL of the full CGSA Streamlit PDF report. AAA includes this as a hyperlink in Phase 5.", example: '"https://cgsa.streamlit.app/reports/a3f7c2d1"' },
    ],
  },
];

const AUDIT_FLOW = [
  { id: "S4", label: "S4 CGSA", color: "#0F6E56", bg: "#E1F5EE", desc: "Runs 38-control UAGF-GMM assessment on governance docs" },
  { id: "JSON", label: "JSON API", color: "#854F0B", bg: "#FAEEDA", desc: "uagf-cgsa-aaa-schema v1.0.0" },
  { id: "S5", label: "S5 AAA Phase 5", color: "#185FA5", bg: "#E6F1FB", desc: "Inserts governance findings into 6-phase UAGF-TAM audit report" },
];

const VERDICT_RULES = [
  { verdict: "PASS", rule: "csp_satisfiable = true AND eu_ai_act_coverage_pct ≥ 80%", color: "#3B6D11", bg: "#EAF3DE" },
  { verdict: "PASS_WITH_OBSERVATIONS", rule: "csp_satisfiable = true AND coverage < 80% (or soft gaps only)", color: "#854F0B", bg: "#FAEEDA" },
  { verdict: "FAIL", rule: "csp_satisfiable = false (one or more hard constraints violated)", color: "#A32D2D", bg: "#FCEBEB" },
];

function Tag({ children, color, bg }) {
  return (
    <span style={{
      background: bg || "#E6F1FB",
      color: color || "#185FA5",
      fontSize: 10,
      fontWeight: 500,
      padding: "2px 7px",
      borderRadius: 4,
      letterSpacing: "0.04em",
      whiteSpace: "nowrap",
    }}>{children}</span>
  );
}

function FieldRow({ field }) {
  const [open, setOpen] = useState(false);
  const hasDetail = field.description || field.example || field.values;
  return (
    <div
      style={{
        borderBottom: "0.5px solid var(--color-border-tertiary)",
        cursor: hasDetail ? "pointer" : "default",
      }}
      onClick={() => hasDetail && setOpen(o => !o)}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "8px 12px", paddingLeft: field.indent ? 28 : 12 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: field.isBold ? "var(--color-text-primary)" : "#185FA5", fontWeight: field.isBold ? 500 : 400, minWidth: 220, flexShrink: 0, paddingTop: 1 }}>{field.name}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--color-text-secondary)", minWidth: 140, flexShrink: 0, paddingTop: 2 }}>{field.type}</span>
        <span style={{ marginLeft: "auto", flexShrink: 0 }}>
          {field.required ? <Tag color="#185FA5" bg="#E6F1FB">required</Tag> : <Tag color="#5F5E5A" bg="#F1EFE8">optional</Tag>}
        </span>
        {hasDetail && <span style={{ color: "var(--color-text-tertiary)", fontSize: 11, paddingTop: 2, marginLeft: 4 }}>{open ? "▲" : "▼"}</span>}
      </div>
      {open && hasDetail && (
        <div style={{ padding: "0 12px 10px", paddingLeft: field.indent ? 28 : 12, borderTop: "0.5px solid var(--color-border-tertiary)", background: "var(--color-background-secondary)" }}>
          {field.description && <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "8px 0 4px", lineHeight: 1.55 }}>{field.description}</p>}
          {field.values && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, margin: "4px 0" }}>
              {field.values.map(v => (
                <span key={v} style={{ fontFamily: "var(--font-mono)", fontSize: 11, background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-secondary)", borderRadius: 4, padding: "2px 6px", color: "var(--color-text-primary)" }}>{v}</span>
              ))}
            </div>
          )}
          {field.example && (
            <div style={{ marginTop: 4 }}>
              <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>example: </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--color-text-primary)" }}>{field.example}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SectionCard({ section, isActive, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        border: isActive ? "1px solid #185FA5" : "0.5px solid var(--color-border-tertiary)",
        borderRadius: 8,
        background: isActive ? "#E6F1FB" : "var(--color-background-primary)",
        padding: "10px 14px",
        cursor: "pointer",
        transition: "all 0.15s",
        marginBottom: 6,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: isActive ? "#185FA5" : "var(--color-text-primary)", fontWeight: 500 }}>{section.label}</span>
        <Tag color={isActive ? "#185FA5" : section.tagColor} bg={isActive ? "#B5D4F4" : undefined}>{section.tag}</Tag>
      </div>
    </div>
  );
}

export default function App() {
  const [activeSection, setActiveSection] = useState("aaa_phase5_handoff");
  const [showFlow, setShowFlow] = useState(true);

  const section = SECTIONS.find(s => s.id === activeSection);

  return (
    <div style={{ fontFamily: "var(--font-sans)", padding: "0 0 2rem" }}>
      <h2 className="sr-only">UAGF CGSA to AAA JSON API Schema Explorer</h2>

      {/* Header */}
      <div style={{ borderBottom: "0.5px solid var(--color-border-tertiary)", paddingBottom: 16, marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
          <span style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)" }}>UAGF CGSA → AAA API Contract</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--color-text-tertiary)" }}>schema v{SCHEMA_VERSION}</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--color-text-tertiary)" }}>· agreed by Week {AGREED_WEEK}</span>
          <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>· EU AI Act (Regulation (EU) 2024/1689)</span>
        </div>
      </div>

      {/* Flow diagram toggle */}
      <div style={{ marginBottom: 16 }}>
        <button
          onClick={() => setShowFlow(o => !o)}
          style={{ fontSize: 12, padding: "5px 12px", cursor: "pointer" }}
        >{showFlow ? "▲ hide" : "▼ show"} integration flow</button>
      </div>

      {showFlow && (
        <div style={{ marginBottom: 20 }}>
          {/* Integration flow */}
          <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 14, flexWrap: "wrap" }}>
            {AUDIT_FLOW.map((node, i) => (
              <div key={node.id} style={{ display: "flex", alignItems: "center" }}>
                <div style={{ background: node.bg, border: `1px solid ${node.color}30`, borderRadius: 8, padding: "10px 16px", textAlign: "center", minWidth: 120 }}>
                  <div style={{ fontWeight: 500, fontSize: 12, color: node.color }}>{node.label}</div>
                  <div style={{ fontSize: 10, color: "var(--color-text-secondary)", marginTop: 3, maxWidth: 160 }}>{node.desc}</div>
                </div>
                {i < AUDIT_FLOW.length - 1 && (
                  <div style={{ display: "flex", alignItems: "center", padding: "0 8px", color: "var(--color-text-tertiary)" }}>
                    <span style={{ fontSize: 14 }}>→</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Phase 5 verdict rules */}
          <div style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 6, fontWeight: 500, letterSpacing: "0.04em" }}>PHASE 5 VERDICT DERIVATION</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 6 }}>
              {VERDICT_RULES.map(v => (
                <div key={v.verdict} style={{ background: v.bg, border: `0.5px solid ${v.color}40`, borderRadius: 6, padding: "8px 10px" }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 500, color: v.color, marginBottom: 3 }}>{v.verdict}</div>
                  <div style={{ fontSize: 10, color: "var(--color-text-secondary)", lineHeight: 1.4 }}>{v.rule}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 6 domains */}
          <div style={{ marginTop: 10 }}>
            <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 6, fontWeight: 500, letterSpacing: "0.04em" }}>6 UAGF-GMM DOMAINS (38 controls total)</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 5 }}>
              {["D1 Risk Management", "D2 Data Governance", "D3 Model Dev & Testing", "D4 Transparency & Explainability", "D5 Human Oversight", "D6 Monitoring & Incident Response"].map((d, i) => (
                <div key={i} style={{ background: "var(--color-background-secondary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 6, padding: "6px 10px", fontSize: 11, color: "var(--color-text-secondary)" }}>
                  <span style={{ fontFamily: "var(--font-mono)", color: "#0F6E56", fontWeight: 500 }}>{d.slice(0, 2)}</span>
                  <span style={{ marginLeft: 4 }}>{d.slice(3)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main layout */}
      <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: 16, alignItems: "start" }}>
        {/* Section nav */}
        <div style={{ position: "sticky", top: 16 }}>
          <div style={{ fontSize: 10, color: "var(--color-text-tertiary)", marginBottom: 8, fontWeight: 500, letterSpacing: "0.06em" }}>SCHEMA SECTIONS</div>
          {SECTIONS.map(s => (
            <SectionCard key={s.id} section={s} isActive={activeSection === s.id} onClick={() => setActiveSection(s.id)} />
          ))}
        </div>

        {/* Section detail */}
        <div>
          {section && (
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, flexWrap: "wrap" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 14, fontWeight: 500, color: "var(--color-text-primary)" }}>{section.label}</span>
                <Tag color={section.tagColor} bg={section.id === "aaa_phase5_handoff" ? "#FAEEDA" : undefined}>{section.tag}</Tag>
              </div>
              <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 14px", lineHeight: 1.6 }}>{section.description}</p>

              {/* Domain names for domains section */}
              {section.domainNames && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 5, marginBottom: 12 }}>
                  {section.domainNames.map(d => (
                    <div key={d} style={{ background: "#E1F5EE", border: "0.5px solid #1D9E7540", borderRadius: 5, padding: "5px 10px", fontSize: 11, color: "#085041", fontFamily: "var(--font-mono)" }}>{d}</div>
                  ))}
                </div>
              )}

              {/* Articles for compliance matrix */}
              {section.articles && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10, color: "var(--color-text-tertiary)", marginBottom: 6, fontWeight: 500, letterSpacing: "0.06em" }}>ARTICLES IN THIS OBJECT</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 5, marginBottom: 8 }}>
                    {section.articles.map(a => (
                      <div key={a.id} style={{
                        background: a.required ? "#E6F1FB" : "var(--color-background-secondary)",
                        border: a.required ? "0.5px solid #185FA540" : "0.5px solid var(--color-border-tertiary)",
                        borderRadius: 6, padding: "7px 10px",
                      }}>
                        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 500, color: a.required ? "#185FA5" : "var(--color-text-secondary)" }}>{a.label}</div>
                        <div style={{ fontSize: 10, color: "var(--color-text-secondary)", marginTop: 2 }}>{a.title}</div>
                        <div style={{ fontSize: 9, color: "var(--color-text-tertiary)", marginTop: 3 }}>{a.note}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Fields table */}
              <div style={{ border: "0.5px solid var(--color-border-tertiary)", borderRadius: 8, overflow: "hidden", marginBottom: 14 }}>
                {/* Table header */}
                <div style={{ display: "flex", gap: 10, padding: "6px 12px", background: "var(--color-background-secondary)", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                  <span style={{ fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, minWidth: 220, letterSpacing: "0.06em" }}>FIELD</span>
                  <span style={{ fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, minWidth: 140, letterSpacing: "0.06em" }}>TYPE</span>
                  <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, letterSpacing: "0.06em" }}>STATUS</span>
                </div>
                {section.fields.map((f, i) => <FieldRow key={i} field={f} />)}
              </div>

              {/* Control fields for domains section */}
              {section.controlFields && (
                <div>
                  <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 6, fontWeight: 500, letterSpacing: "0.06em" }}>CONTROL OBJECT FIELDS (per item in controls[ ])</div>
                  <div style={{ border: "0.5px solid var(--color-border-tertiary)", borderRadius: 8, overflow: "hidden", marginBottom: 14 }}>
                    <div style={{ display: "flex", gap: 10, padding: "6px 12px", background: "var(--color-background-secondary)", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                      <span style={{ fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, minWidth: 220, letterSpacing: "0.06em" }}>FIELD</span>
                      <span style={{ fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, minWidth: 140, letterSpacing: "0.06em" }}>TYPE</span>
                      <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, letterSpacing: "0.06em" }}>STATUS</span>
                    </div>
                    {section.controlFields.map((f, i) => <FieldRow key={i} field={f} />)}
                  </div>
                </div>
              )}

              {/* Subsections (for hard_constraint_results) */}
              {section.subsections && section.subsections.map((sub, si) => (
                <div key={si} style={{ marginBottom: 14 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)" }}>{sub.label}</span>
                    <Tag color="#185FA5">{sub.tag}</Tag>
                  </div>
                  <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 8px", lineHeight: 1.55 }}>{sub.description}</p>
                  <div style={{ border: "0.5px solid var(--color-border-tertiary)", borderRadius: 8, overflow: "hidden" }}>
                    <div style={{ display: "flex", gap: 10, padding: "6px 12px", background: "var(--color-background-secondary)", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                      <span style={{ fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, minWidth: 220, letterSpacing: "0.06em" }}>FIELD</span>
                      <span style={{ fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, minWidth: 140, letterSpacing: "0.06em" }}>TYPE</span>
                      <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--color-text-tertiary)", fontWeight: 500, letterSpacing: "0.06em" }}>STATUS</span>
                    </div>
                    {sub.fields.map((f, i) => <FieldRow key={i} field={f} />)}
                  </div>
                </div>
              ))}

              {/* Tip for handoff section */}
              {section.id === "aaa_phase5_handoff" && (
                <div style={{ background: "#FAEEDA", border: "0.5px solid #BA751740", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "#633806", lineHeight: 1.55 }}>
                  <strong>AAA integration note:</strong> This is the primary block S5 AAA should read first. <code style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>phase5_verdict</code>, <code style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>blocking_findings</code>, and <code style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>phase5_narrative_summary</code> are pre-computed for direct insertion into the Phase 5 audit report. The full <code style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>domains[ ]</code> array is available for detailed evidence tracing.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{ borderTop: "0.5px solid var(--color-border-tertiary)", marginTop: 24, paddingTop: 12, display: "flex", gap: 16, flexWrap: "wrap" }}>
        <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>schema_version: {SCHEMA_VERSION}</span>
        <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>agreed_by_week: {AGREED_WEEK}</span>
        <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>regulation: EU AI Act (2024/1689)</span>
        <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>click any field row to expand description</span>
      </div>
    </div>
  );
}
