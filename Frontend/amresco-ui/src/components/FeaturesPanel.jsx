import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./FeaturesPanel.css";

export default function FeaturesPanel() {
  const [open, setOpen] = useState(false);
  const panelRef = useRef();
  const navigate = useNavigate();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleNavigate = (path) => {
    setOpen(false);       // Close dropdown
    navigate(path);       // Navigate to page
  };

  return (
    <div className="features-wrapper" ref={panelRef}>

      {/* NORMAL NAVBAR LINK (NO BOX) */}
      <a
        className="nav-feature-link"
        onClick={() => setOpen(!open)}
      >
        Features
      </a>

      {open && (
        <div className="features-dropdown">

          {/* Missing Values */}
          <div
            className="feature-item"
            onClick={() => handleNavigate("/missing-values")}
          >
            <h4>Missing Values</h4>
            <p>Detect and report cells with missing or blank values.</p>
          </div>

          {/* Anomaly Detection */}
          <div
            className="feature-item"
            onClick={() => handleNavigate("/anomaly-detection")}
          >
            <h4>Anomaly Detection</h4>
            <p>Identify and highlight anomalies and outliers in your data.</p>
          </div>

          {/* AI Notes */}
          <div
            className="feature-item"
            onClick={() => handleNavigate("/ai-notes")}
          >
            <h4>AI Notes</h4>
            <p>Get AI-generated notes summarizing key insights from Excel data.</p>
          </div>

          {/* Formula Analysis */}
          <div
            className="feature-item"
            onClick={() => handleNavigate("/formula-analysis")}
          >
            <h4>Formula Analysis</h4>
            <p>Review and validate Excel formulas for errors and inconsistencies.</p>
          </div>

          

        </div>
      )}
    </div>
  );
}