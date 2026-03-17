import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

import "./analysis.css";

import logo from "../assets/logo.png";
import FeaturesPanel from "../components/FeaturesPanel";
import AccountDropdown from "../components/AccountDropdown";

export default function Analysis() {

  const navigate = useNavigate();
  const location = useLocation();

  const data = location.state?.data;
  const fileName = location.state?.fileName || "Uploaded File";

  const [missingOpen, setMissingOpen] = useState(false);
  const [anomalyOpen, setAnomalyOpen] = useState(false);
  const [formulaOpen, setFormulaOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);

  const [sheetFilter, setSheetFilter] = useState("");
  const [siteFilter, setSiteFilter] = useState("");

  const [anomalySheetFilter, setAnomalySheetFilter] = useState("");
  const [anomalySiteFilter, setAnomalySiteFilter] = useState("");

  if (!data) {
    return <h2 style={{ padding: "40px" }}>No analysis data found</h2>;
  }

  const summary = data.summary || {};
  const missingData = data.missing || [];
  const anomalyData = data.anomalies || [];
  const formulaData = data.formulas || [];

  /* ---------------- UNIQUE FILTER VALUES ---------------- */

  const sheets = [...new Set(missingData.map(i => i.sheet_name))];
  const sites = [...new Set(missingData.map(i => i.site_name))];

  const anomalySheets = [...new Set(anomalyData.map(i => i.sheet))];
  const anomalySites = [...new Set(anomalyData.map(i => i.site))];

  /* ---------------- FILTER DATA ---------------- */

  const filteredMissing = missingData.filter(row => {
    const sheetMatch = sheetFilter ? row.sheet_name === sheetFilter : true;
    const siteMatch = siteFilter ? row.site_name === siteFilter : true;
    return sheetMatch && siteMatch;
  });

  const filteredAnomalies = anomalyData.filter(row => {
    const sheetMatch = anomalySheetFilter ? row.sheet === anomalySheetFilter : true;
    const siteMatch = anomalySiteFilter ? row.site === anomalySiteFilter : true;
    return sheetMatch && siteMatch;
  });

  /* ---------------- GROUP ANOMALIES ---------------- */

  const groupedAnomalies = {};

  filteredAnomalies.forEach(row => {

    const key = row.sheet + "_" + row.site;

    if (!groupedAnomalies[key]) {
      groupedAnomalies[key] = {
        sheet: row.sheet,
        site: row.site,
        forecasted: [],
        expected: [],
        issue: row.issue_type
      };
    }

    if (row.column_name?.toLowerCase().includes("forecast")) {
      groupedAnomalies[key].forecasted.push(row.cell_number);
    } else {
      groupedAnomalies[key].expected.push(row.cell_number);
    }

  });

  const anomalyRows = Object.values(groupedAnomalies);

  return (

    <div>

      {/* NAVBAR */}

      <header className="navbar">

        <div className="nav-left">
          <img src={logo} alt="logo" />
        </div>

        <nav className="nav-links">

          <a onClick={() => navigate("/")}>Home</a>

          <a onClick={() => navigate("/dashboard")}>
            Dashboard
          </a>

          <FeaturesPanel />

          <a>Reports</a>

          <a>Help</a>

          {!localStorage.getItem("user") ? (

            <button
              className="signin"
              onClick={() => navigate("/signin")}
            >
              Sign In
            </button>

          ) : (

            <AccountDropdown />

          )}

        </nav>

      </header>


      {/* ANALYSIS CONTENT */}

      <div className="analysis-container">

        {/* TITLE */}

        <h1 className="title">Excel Data Analysis</h1>

        {/* FILE NAME */}

        <p className="file-name">
          File : <span>{fileName}</span>
        </p>

        {/* SUMMARY CARDS */}

        <div className="summary-cards">

          <div className="card green">
            <h3>Total Cells</h3>
            <p>{summary.total_cells}</p>
          </div>

          <div className="card orange">
            <h3>Missing Values</h3>
            <p>{summary.missing_values}</p>
          </div>

          <div className="card red">
            <h3>Incomplete Data %</h3>
            <p>{summary.percentage}%</p>
          </div>

          <div className="card purple">
            <h3>Abnormal Values</h3>
            <p>{summary.abnormal_values}</p>
          </div>

          <div className="card blue">
            <h3>Underperforming Sites</h3>
            <p>{summary.underperforming_sites}</p>
          </div>

          <div className="card pink">
            <h3>Formula Errors</h3>
            <p>{formulaData.length}</p>
          </div>

        </div>


        {/* ---------------- Missing Data ---------------- */}

        <div
          className="section-box"
          onClick={() => setMissingOpen(!missingOpen)}
        >
          <span>Missing Data Analysis</span>
          <span className="arrow">{missingOpen ? "▲" : "▼"}</span>
        </div>

        {missingOpen && (

          <div className="dropdown-content">

            <div className="filter-container">

              <select
                value={sheetFilter}
                onChange={(e) => setSheetFilter(e.target.value)}
              >
                <option value="">All Sheets</option>
                {sheets.map((s, i) => (
                  <option key={i} value={s}>{s}</option>
                ))}
              </select>

              <select
                value={siteFilter}
                onChange={(e) => setSiteFilter(e.target.value)}
              >
                <option value="">All Sites</option>
                {sites.map((s, i) => (
                  <option key={i} value={s}>{s}</option>
                ))}
              </select>

              <button onClick={() => {
                setSheetFilter("");
                setSiteFilter("");
              }}>
                Clear Filters
              </button>

            </div>

            <table className="analysis-table">

              <thead>
                <tr>
                  <th>Sheet Name</th>
                  <th>Site Name</th>
                  <th>Column</th>
                  <th>Cell</th>
                  <th>Issue</th>
                </tr>
              </thead>

              <tbody>

                {filteredMissing.length === 0 ? (

                  <tr>
                    <td colSpan="5" style={{ textAlign: "center" }}>
                      No data found
                    </td>
                  </tr>

                ) : (

                  filteredMissing.map((row, idx) => (

                    <tr key={idx}>
                      <td>{row.sheet_name}</td>
                      <td>{row.site_name}</td>
                      <td>{row.column_name}</td>
                      <td>{row.cell}</td>
                      <td>{row.issue_type}</td>
                    </tr>

                  ))

                )}

              </tbody>

            </table>

            <div className="total-row">
              Showing Rows: {filteredMissing.length}
            </div>

          </div>

        )}


        {/* ---------------- Formula Detection ---------------- */}

        <div
          className="section-box"
          onClick={() => setFormulaOpen(!formulaOpen)}
        >
          <span>Formula Detection</span>
          <span className="arrow">{formulaOpen ? "▲" : "▼"}</span>
        </div>

        {formulaOpen && (

          <div className="dropdown-content">

            <div className="formula-count">
              Total Formula Errors: {formulaData.length}
            </div>

            <table className="analysis-table">

              <thead>
                <tr>
                  <th>Sheet</th>
                  <th>Column</th>
                  <th>Row</th>
                  <th>Expected Logic</th>
                  <th>Actual Formula</th>
                </tr>
              </thead>

              <tbody>

                {formulaData.length === 0 ? (

                  <tr>
                    <td colSpan="5" style={{ textAlign: "center" }}>
                      No formula errors found
                    </td>
                  </tr>

                ) : (

                  formulaData.map((f, idx) => (

                    <tr key={idx}>
                      <td>{f.sheet}</td>
                      <td>{f.column}</td>
                      <td>{f.row}</td>
                      <td>{f.expected_logic}</td>
                      <td>{f.given_formula}</td>
                    </tr>

                  ))

                )}

              </tbody>

            </table>

          </div>

        )}


        {/* ---------------- Anomaly Detection ---------------- */}

        <div
          className="section-box"
          onClick={() => setAnomalyOpen(!anomalyOpen)}
        >
          <span>Anomaly Detection</span>
          <span className="arrow">{anomalyOpen ? "▲" : "▼"}</span>
        </div>

        {anomalyOpen && (

          <div className="dropdown-content">

            <div className="filter-container">

              <select
                value={anomalySheetFilter}
                onChange={(e) => setAnomalySheetFilter(e.target.value)}
              >
                <option value="">All Sheets</option>
                {anomalySheets.map((s, i) => (
                  <option key={i} value={s}>{s}</option>
                ))}
              </select>

              <select
                value={anomalySiteFilter}
                onChange={(e) => setAnomalySiteFilter(e.target.value)}
              >
                <option value="">All Sites</option>
                {anomalySites.map((s, i) => (
                  <option key={i} value={s}>{s}</option>
                ))}
              </select>

              <button onClick={() => {
                setAnomalySheetFilter("");
                setAnomalySiteFilter("");
              }}>
                Clear Filters
              </button>

            </div>

            <table className="anomaly-table">

              <thead>
                <tr>
                  <th>Sheet</th>
                  <th>Site</th>
                  <th>Forecasted %</th>
                  <th>Expected %</th>
                  <th>Issue</th>
                </tr>
              </thead>

              <tbody>

                {anomalyRows.length === 0 ? (

                  <tr>
                    <td colSpan="5" style={{ textAlign: "center" }}>
                      No anomalies found
                    </td>
                  </tr>

                ) : (

                  anomalyRows.map((row, i) => (

                    <tr
                      key={i}
                      className={`row-${row.issue?.replace(/\s/g, "").toLowerCase()}`}
                    >

                      <td>{row.sheet}</td>

                      <td>{row.site}</td>

                      <td>
                        {row.forecasted.map((tag, index) => (
                          <span key={index} className="tag forecast">
                            {tag}
                          </span>
                        ))}
                      </td>

                      <td>
                        {row.expected.map((tag, index) => (
                          <span key={index} className="tag expected">
                            {tag}
                          </span>
                        ))}
                      </td>

                      <td>{row.issue}</td>

                    </tr>

                  ))

                )}

              </tbody>

            </table>

          </div>

        )}


        {/* ---------------- AI NOTES ---------------- */}

        <div
          className="section-box"
          onClick={() => setAiOpen(!aiOpen)}
        >
          <span>AI Notes</span>
          <span className="arrow">{aiOpen ? "▲" : "▼"}</span>
        </div>

        {aiOpen && (
          <div className="section-content">
            Coming Soon
          </div>
        )}


        {/* SAVE BUTTON */}

        <div className="save-container">
          <button className="save-btn">Save</button>
        </div>

      </div>

    </div>
  );
}