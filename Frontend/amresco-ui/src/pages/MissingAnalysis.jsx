import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import styles from "./missing.module.css";

import logo from "../assets/logo.png";
import FeaturesPanel from "../components/FeaturesPanel";
import AccountDropdown from "../components/AccountDropdown";

export default function MissingAnalysis() {
  const navigate = useNavigate();
  const location = useLocation();

  const data = location.state?.data;
  const fileName = location.state?.fileName;

  const [sheetFilter, setSheetFilter] = useState("");
  const [siteFilter, setSiteFilter] = useState("");

  if (!data) {
    return <h2 style={{ padding: "40px" }}>No analysis data found</h2>;
  }

  const summary = data.summary || {};
  const missingData = data.missing || [];

  const sheets = [...new Set(missingData.map((i) => i.sheet_name))];
  const sites = [...new Set(missingData.map((i) => i.site_name))];

  const filteredData = missingData.filter((row) => {
    const sheetMatch = sheetFilter ? row.sheet_name === sheetFilter : true;
    const siteMatch = siteFilter ? row.site_name === siteFilter : true;
    return sheetMatch && siteMatch;
  });

  return (
    <div>
      {/* NAVBAR (keep global) */}
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
        <h1 className={styles.title}>Missing Data Analysis</h1>

        <p className={styles.fileName}>
          File: <b>{fileName}</b>
        </p>

        {/* SUMMARY */}
        <div className={styles.summaryCards}>
          <div className={`${styles.card} ${styles.green}`}>
            <h3>Total Cells</h3>
            <p>{summary.total_cells}</p>
          </div>

          <div className={`${styles.card} ${styles.orange}`}>
            <h3>Missing Values</h3>
            <p>{summary.missing_values}</p>
          </div>

          <div className={`${styles.card} ${styles.red}`}>
            <h3>Incomplete Data</h3>
            <p>{summary.percentage}%</p>
          </div>
        </div>

        {/* FILTERS */}
        <div className={styles.filters}>
          <select
            value={sheetFilter}
            onChange={(e) => setSheetFilter(e.target.value)}
          >
            <option value="">All Sheets</option>
            {sheets.map((s, i) => (
              <option key={i} value={s}>
                {s}
              </option>
            ))}
          </select>

          <select
            value={siteFilter}
            onChange={(e) => setSiteFilter(e.target.value)}
          >
            <option value="">All Sites</option>
            {sites.map((s, i) => (
              <option key={i} value={s}>
                {s}
              </option>
            ))}
          </select>

          <button
            onClick={() => {
              setSheetFilter("");
              setSiteFilter("");
            }}
          >
            Clear Filters
          </button>
        </div>

        {/* TABLE */}
        <h2 className={styles.sectionTitle}>Missing Values Overview</h2>

        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Sheet Name</th>
                <th>Site Name</th>
                <th>Column Name</th>
                <th>Cell Number</th>
                <th>Issue Type</th>
              </tr>
            </thead>

            <tbody>
              {filteredData.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: "center" }}>
                    No missing values found
                  </td>
                </tr>
              ) : (
                filteredData.map((row, index) => (
                  <tr key={index}>
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
        </div>

        <div className={styles.totalRow}>
          Showing Rows: {filteredData.length}
        </div>
      </div>
    </div>
  );
}