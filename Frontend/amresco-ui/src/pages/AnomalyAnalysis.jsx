import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

import styles from "./anomaly.module.css";

import logo from "../assets/logo.png";
import FeaturesPanel from "../components/FeaturesPanel";
import AccountDropdown from "../components/AccountDropdown";

export default function AnomalyAnalysis() {
  const navigate = useNavigate();
  const location = useLocation();

  const data = location.state?.data;
  const fileName = location.state?.fileName;

  const [sheetFilter, setSheetFilter] = useState("");
  const [siteFilter, setSiteFilter] = useState("");

  if (!data) {
    return <h2 style={{ padding: "40px" }}>No anomaly data found</h2>;
  }

  const summary = data.summary || {};
  const anomalyData = data.anomalies || [];

  const sheets = [...new Set(anomalyData.map(i => i.sheet))];
  const sites = [...new Set(anomalyData.map(i => i.site))];

  const filteredData = anomalyData.filter(row => {
    const sheetMatch = sheetFilter ? row.sheet === sheetFilter : true;
    const siteMatch = siteFilter ? row.site === siteFilter : true;
    return sheetMatch && siteMatch;
  });

  const grouped = {};

  filteredData.forEach(row => {
    const key = row.sheet + "_" + row.site;

    if (!grouped[key]) {
      grouped[key] = {
        sheet: row.sheet,
        site: row.site,
        forecasted: [],
        expected: [],
        issue: row.issue_type
      };
    }

    if (row.column_name?.toLowerCase().includes("forecast")) {
      grouped[key].forecasted.push(row.cell_number);
    } else {
      grouped[key].expected.push(row.cell_number);
    }
  });

  const anomalyRows = Object.values(grouped);

  return (
    <div>
      {/* NAVBAR (kept global) */}
      <header className="navbar">
        <div className="nav-left">
          <img src={logo} alt="logo" />
        </div>

        <nav className="nav-links">
          <a onClick={() => navigate("/")}>Home</a>
          <a onClick={() => navigate("/dashboard")}>Dashboard</a>
          <FeaturesPanel />
          <a>Reports</a>
          <a>Help</a>

          {!localStorage.getItem("user") ? (
            <button className="signin" onClick={() => navigate("/signin")}>
              Sign In
            </button>
          ) : (
            <AccountDropdown />
          )}
        </nav>
      </header>

      {/* PAGE */}
      <div className={styles.container}>
        <h1 className={styles.title}>Anomaly Detection Analysis</h1>

        <p className={styles.fileName}>
          File: <b>{fileName}</b>
        </p>

        {/* SUMMARY */}
        <div className={styles.summaryCards}>
          <div className={`${styles.card} ${styles.purple}`}>
            <h3>Abnormal Values</h3>
            <p>{summary.abnormal_values}</p>
          </div>

          <div className={`${styles.card} ${styles.blue}`}>
            <h3>Underperforming Sites</h3>
            <p>{summary.underperforming_sites}</p>
          </div>
        </div>

        {/* SECTION */}
        <div className={styles.sectionBox}>
          <span>Anomaly Detection</span>
        </div>

        <div className={styles.content}>
          {/* FILTERS */}
          <div className={styles.filters}>
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

          {/* TABLE */}
          <table className={styles.table}>
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
                  <tr key={i}>
                    <td>{row.sheet}</td>
                    <td>{row.site}</td>

                    <td>
                      {row.forecasted.map((tag, index) => (
                        <span key={index} className={`${styles.tag} ${styles.forecast}`}>
                          {tag}
                        </span>
                      ))}
                    </td>

                    <td>
                      {row.expected.map((tag, index) => (
                        <span key={index} className={`${styles.tag} ${styles.expected}`}>
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

          <div className={styles.totalRow}>
            Showing Rows: {anomalyRows.length}
          </div>
        </div>
      </div>
    </div>
  );
}