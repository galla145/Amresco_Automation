import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeFile, getFiles } from "../services/api";

import logo from "../assets/logo.png";
import "./MissingValues.css";

import FeaturesPanel from "../components/FeaturesPanel";
import AccountDropdown from "../components/AccountDropdown";

export default function AnomalyDetection() {

  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  // Fetch uploaded files
  useEffect(() => {

    getFiles()
      .then((res) => {
        setFiles(res.data);
      })
      .catch((err) => {
        console.error("Error fetching files:", err);
      });

  }, []);


  // Analyze selected file
  const handleAnalyze = async () => {

    if (!selectedFile) {
      alert("Please select one file to analyze");
      return;
    }

    try {

      setLoading(true);

      const res = await analyzeFile(selectedFile);

      console.log("Analysis result:", res.data);

      navigate("/anomaly-analysis", {
        state: {
          data: res.data,
          filename: selectedFile
        }
      });

    } catch (error) {

      console.error("Analysis failed:", error);
      alert("Analysis failed");

    } finally {

      setLoading(false);

    }

  };


  return (

    <div className="missing-container">

      {/* NAVBAR */}
      <header className="navbar">

        <div className="nav-left">
          <img src={logo} alt="logo"/>
        </div>

        <nav className="nav-links">
          <a onClick={() => navigate("/")}>Home</a>
          <a onClick={() => navigate("/dashboard")}>Dashboard</a>
          <FeaturesPanel/>
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


      {/* TITLE */}
      <h1 className="missing-title">
        Anomaly Detection Analyzer
      </h1>


      {/* CONTENT */}
      <div className="missing-content">

        <div className="missing-card">

          <div className="missing-header">

            <h3>Select One Uploaded File</h3>

            <button
              className="missing-analyze-btn"
              onClick={handleAnalyze}
              disabled={!selectedFile || loading}
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>

          </div>


          {/* FILE TABLE */}
          <table className="missing-table">

            <thead>
              <tr>
                <th></th>
                <th>Filename</th>
                <th>Uploaded</th>
                <th>Size</th>
              </tr>
            </thead>

            <tbody>

              {files.map((file, index) => (

                <tr key={index}>

                  <td>
                    <input
                      type="radio"
                      name="file"
                      checked={selectedFile === file.name}
                      onChange={() => setSelectedFile(file.name)}
                    />
                  </td>

                  <td>{file.name}</td>

                  <td>{file.uploaded_at}</td>

                  <td>{file.size_kb} KB</td>

                </tr>

              ))}

            </tbody>

          </table>


          {files.length === 0 && (
            <p className="no-files">
              No uploaded files found.
            </p>
          )}

        </div>

      </div>

    </div>

  );

}