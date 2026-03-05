import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getFiles } from "../services/api";
import logo from "../assets/logo.png";
import "./MissingValues.css";
import FeaturesPanel from "../components/FeaturesPanel";

export default function MissingValues() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const navigate = useNavigate();

  // Fetch uploaded files from backend
  useEffect(() => {
    getFiles()
      .then((res) => {
        setFiles(res.data);
      })
      .catch((err) => {
        console.error("Error fetching files:", err);
      });
  }, []);

  const handleAnalyze = () => {
    if (!selectedFile) {
      alert("Please select one file to analyze");
      return;
    }

    console.log("Analyzing:", selectedFile);
    // Later connect missing values API here
  };

  return (
    <div className="missing-container">

      {/* NAVBAR */}
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
          <button className="signin">Sign In</button>
        </nav>
      </header>


      {/* TITLE */}
      <h1 className="missing-title">Missing Values Analyzer</h1>


      {/* TABLE SECTION */}
      <div className="missing-content">
        <div className="missing-card">

          <div className="missing-header">
            <h3>Select One Uploaded File</h3>

            <button
              className="missing-analyze-btn"
              onClick={handleAnalyze}
              disabled={!selectedFile}
            >
              Analyze
            </button>
          </div>


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
                      name="fileSelect"
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
            <p className="no-files">No uploaded files found.</p>
          )}

        </div>
      </div>

    </div>
  );
}