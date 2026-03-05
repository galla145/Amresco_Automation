import logo from "../assets/logo.png";
import hero from "../assets/hero.png";
import uploadIcon from "../assets/upload.png";
import ai from "../assets/ai.png";
import cleaning from "../assets/cleaning.png";
import reports from "../assets/reports.png";
import bottom from "../assets/bottom.png";

import { uploadFile } from "../services/api";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import FeaturesPanel from "../components/FeaturesPanel";

export default function UploadPage() {

  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const navigate = useNavigate();

  // Handle File Upload
  const handleUpload = async () => {

    if (!file) {
      alert("Please select an XLSX file");
      return;
    }

    try {

      await uploadFile(file);

      setUploadStatus("File uploaded successfully!");

    } catch (error) {

      setUploadStatus("Upload failed. Try again.");

    }
  };

  return (
    <div className="container">

      {/* NAVBAR */}
      <header className="navbar">

        <div className="nav-left">
          <img src={logo} alt="logo"/>
        </div>

        <nav className="nav-links">
          <a className="active">Home</a>
          <a onClick={() => navigate("/dashboard")}>Dashboard</a>
          <FeaturesPanel />
          <a>Reports</a>
          <a>Help</a>
          <button className="signin">Sign In</button>
        </nav>

      </header>


      {/* HERO SECTION */}
      <section className="hero">

        {/* LEFT SIDE */}
        <div className="left">

          <h1>
            Upload & Analyze XLSX Files
            <br/>
            with <span>AMRESCO Automation</span>
          </h1>

          <p>
            Automate Data Quality Checks, Anomaly Detection, and
            Performance Reporting with AI-Powered Excel Analysis.
          </p>

          {/* UPLOAD CARD */}
          <div className="upload-card">

            <h3>Upload an XLSX File</h3>

            <div className="drop-area">

              <img src={uploadIcon} alt="upload"/>

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

            {/* BUTTONS */}
            <div className="button-group">

              <button
                className="upload-btn"
                onClick={handleUpload}
              >
                Upload
              </button>

              <button
                className="analyze-btn"
              >
                Analyze
              </button>

            </div>

            {uploadStatus && (
              <p className="upload-status">{uploadStatus}</p>
            )}

          </div>


          {/* FEATURES */}
          <div className="features">

            <div>
              <img src={ai}/>
              AI Agents
            </div>

            <div>
              <img src={cleaning}/>
              Data Cleaning
            </div>

            <div>
              <img src={reports}/>
              Detailed Reports
            </div>

          </div>

          <img src={bottom} className="bottom-img"/>

        </div>


        {/* RIGHT SIDE */}
        <div className="right">

          <img src={hero} className="hero-img"/>

          <div className="about">

            <h2>About AMRESCO Automation</h2>

            <p>
              AMRESCO Automation leverages advanced AI to transform
              raw Excel data into valuable insights.
            </p>

            <ul>
              <li>AI-Powered Analysis</li>
              <li>Data Quality Assurance</li>
              <li>Performance Insights</li>
            </ul>

            <p className="footer">
              Empowering enterprises with real-time data quality analysis.
            </p>

          </div>

        </div>

      </section>

    </div>
  );
}