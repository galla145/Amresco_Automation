import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getFiles, analyzeFile } from "../services/api";
import logo from "../assets/logo.png";
import "./Dashboard.css";
import FeaturesPanel from "../components/FeaturesPanel";
import AccountDropdown from "../components/AccountDropdown";

export default function Dashboard() {
  const [files, setFiles] = useState([]);
  const [loadingFile, setLoadingFile] = useState(null);
  const navigate = useNavigate();

  // Fetch uploaded files
  useEffect(() => {
    getFiles()
      .then((res) => setFiles(res.data))
      .catch((err) => console.error(err));
  }, []);

  // Analyze selected file
  const handleAnalyze = async (filename) => {
    try {
      setLoadingFile(filename);

      const res = await analyzeFile(filename);
      console.log("Analysis result:", res.data);

      navigate("/analysis", {
        state: {
          data: res.data,
          filename: filename,
        },
      });
    } catch (error) {
      console.error("Analysis failed:", error);
      alert("Analysis failed");
    } finally {
      setLoadingFile(null);
    }
  };

  return (
    <div className="dashboard-container">

      {/* NAVBAR */}
      <header className="navbar">
        <div className="nav-left">
          <img src={logo} alt="logo" />
        </div>

        <nav className="nav-links">
          <a onClick={() => navigate("/")}>Home</a>
          <a className="active">Dashboard</a>
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

      {/* TITLE */}
      <h1 className="title">Dashboard</h1>

      {/* SEARCH + UPLOAD */}
      <div className="top-bar">
        <div className="search-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search files..."
            className="search-input"
          />
        </div>

        <button
          className="upload-btn"
          onClick={() => navigate("/")}
        >
          ⬆ Upload New File
        </button>
      </div>

      {/* TABLE */}
      <div className="content">
        <div className="table-card">

          <table>
            <thead>
              <tr>
                <th>Filename</th>
                <th>Uploaded</th>
                <th>Size</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {files.map((file, index) => (
                <tr key={index}>
                  <td className="file-name">{file.name}</td>
                  <td>{file.uploaded_at}</td>
                  <td>{file.size_kb} KB</td>
                  <td>
                    <button
                      className="analyze-btn"
                      onClick={() => handleAnalyze(file.name)}
                      disabled={loadingFile === file.name}
                    >
                      {loadingFile === file.name
                        ? "Analyzing..."
                        : "Analyze"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* PAGINATION */}
          <div className="pagination">
            <span>
              Showing 1 to {files.length} of {files.length} entries
            </span>

            <div>
              <button disabled>Previous</button>
              <button className="active">1</button>
              <button disabled>Next</button>
            </div>
          </div>

        </div>
      </div>

    </div>
  );
}