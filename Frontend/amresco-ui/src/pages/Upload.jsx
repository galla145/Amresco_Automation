import { useState } from "react";
import { useNavigate } from "react-router-dom";

import logo from "../assets/logo.png";
import hero from "../assets/hero.png";
import uploadIcon from "../assets/upload.png";
import ai from "../assets/ai.png";
import cleaning from "../assets/cleaning.png";
import reports from "../assets/reports.png";
import bottom from "../assets/bottom.png";


import { uploadFile, analyzeFile } from "../services/api";
import FeaturesPanel from "../components/FeaturesPanel";
import AccountDropdown from "../components/AccountDropdown";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const navigate = useNavigate();

  // Upload File
  const handleUpload = async () => {
    if (!file) {
      alert("Please select an XLSX file");
      return;
    }

    try {
      const res = await uploadFile(file);
      console.log("Upload response:", res.data);
      setUploadStatus("File uploaded successfully!");
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus("Upload failed. Try again.");
    }
  };

  // Analyze File
  const handleAnalyze = async () => {
    if (!file) {
      alert("Upload a file first");
      return;
    }

    try {
      const res = await analyzeFile(file.name);
      console.log("Analysis response:", res.data);

      navigate("/analysis", {
        state: {
          data: res.data,
          filename: file.name,
        },
      });
    } catch (error) {
      console.error("Analysis error:", error);
      alert("Analysis failed");
    }
  };

  return (
    <div className="container">
      {/* NAVBAR */}
      <header className="navbar">
        <div className="nav-left">
          <img src={logo} alt="logo" />
        </div>

        <nav className="nav-links">
          <a className="active">Home</a>

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

      {/* HERO */}
      <section className="hero">

        {/* LEFT SIDE */}
        <div className="left">

          <h1>
            Upload & Analyze XLSX Files <br />
            with <span>AMRESCO Automation</span>
          </h1>

          <p>
            Automate Data Quality Checks, Anomaly Detection,
            and Performance Reporting with AI-Powered Excel Analysis.
          </p>

          {/* Upload Card */}
          <div className="upload-card">
            <h3>Upload an XLSX File</h3>

            <div className="drop-area">
              <img src={uploadIcon} alt="upload" />

              <p>Drag & drop your XLSX file or</p>

              <input
                type="file"
                accept=".xlsx"
                onChange={(e) => setFile(e.target.files[0])}
              />

              <small>Only .xlsx files are supported</small>

              {file && (
                <p className="file-name">
                  Selected File: <b>{file.name}</b>
                </p>
              )}
            </div>

            {/* Buttons */}
            <div className="button-group">
              <button
                className="upload-btn"
                onClick={handleUpload}
              >
                Upload
              </button>

              <button
                className="analyze-btn"
                onClick={handleAnalyze}
              >
                Analyze
              </button>
            </div>

            {uploadStatus && (
              <p className="upload-status">
                {uploadStatus}
              </p>
            )}
          </div>

          {/* Features */}
          <div className="features">

            <div>
              <img src={ai} alt="ai" />
              AI Agents
            </div>

            <div>
              <img src={cleaning} alt="cleaning" />
              Data Cleaning
            </div>

            <div>
              <img src={reports} alt="reports" />
              Detailed Reports
            </div>

          </div>

          <img
            src={bottom}
            className="bottom-img"
            alt="bottom"
          />
        </div>

        {/* RIGHT SIDE */}
        <div className="right">

          <img
            src={hero}
            className="hero-img"
            alt="hero"
          />

          <div className="about">
  <h2>About AMRESCO Automation</h2>

  <p>
    AMRESCO Automation is an AI-powered platform designed to simplify and 
    accelerate Excel data analysis for modern enterprises. It transforms 
    complex and raw spreadsheet data into meaningful insights that help 
    teams make faster and more informed business decisions.
  </p>

  <ul>
    <li>
      <b>AI-Powered Analysis:</b> Uses intelligent algorithms to analyze 
      large Excel datasets and extract meaningful patterns and insights.
    </li>

    <li>
      <b>Data Quality Assurance:</b> Automatically detects missing values, 
      duplicate records, and inconsistent formats to improve data reliability.
    </li>

    <li>
      <b>Anomaly Detection:</b> Identifies unusual or abnormal values in 
      datasets that may indicate potential errors or operational issues.
    </li>

    <li>
      <b>Formula Intelligence:</b> Examines formulas in Excel sheets to 
      detect calculation errors and optimize complex spreadsheet logic.
    </li>
  </ul>

  <p className="footer">
    AMRESCO Automation empowers enterprises with real-time data validation, 
    automated analytics, and intelligent insights to ensure accurate, 
    reliable, and actionable data across their operations.
  </p>
</div>

        </div>

      </section>
    </div>
  );
}