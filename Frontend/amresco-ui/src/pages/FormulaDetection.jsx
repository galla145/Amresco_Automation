import { useLocation, useNavigate } from "react-router-dom";
import styles from "./formulaDetection.module.css";

import logo from "../assets/logo.png";
import FeaturesPanel from "../components/FeaturesPanel";
import AccountDropdown from "../components/AccountDropdown";

export default function FormulaDetection() {
  const navigate = useNavigate();
  const location = useLocation();

  const data = location.state?.data;
  const fileName = location.state?.fileName || "Uploaded File";

  if (!data) {
    return <h2 style={{ padding: "40px" }}>No formula data found</h2>;
  }

  const summary = data.summary || {};
  const formulaData = data.formulas || [];

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
        <h1 className={styles.title}>Formula Detection Analysis</h1>

        <p className={styles.fileName}>
          File: <span>{fileName}</span>
        </p>

        {/* SUMMARY */}
        <div className={styles.summaryCards}>
          <div className={`${styles.card} ${styles.green}`}>
            <h3>Total Cells</h3>
            <p>{summary.total_cells}</p>
          </div>

          <div className={`${styles.card} ${styles.pink}`}>
            <h3>Formula Errors</h3>
            <p>{formulaData.length}</p>
          </div>
        </div>

        {/* TABLE */}
        <div className={styles.sectionBox}>
          <span>Formula Errors Details</span>
        </div>

        <div className={styles.content}>
          <table className={styles.table}>
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
                    <td className={styles.expected}>{f.expected_logic}</td>
                    <td className={styles.actual}>{f.given_formula}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          <div className={styles.totalRow}>
            Showing Rows: {formulaData.length}
          </div>
        </div>
      </div>
    </div>
  );
}