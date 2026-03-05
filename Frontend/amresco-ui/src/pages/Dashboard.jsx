import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getFiles } from "../services/api";
import logo from "../assets/logo.png";
import "./Dashboard.css";
import FeaturesPanel from "../components/FeaturesPanel";

export default function Dashboard() {
  const [files, setFiles] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    getFiles().then((res) => setFiles(res.data));
  }, []);

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
          <button className="signin">Sign In</button>
        </nav>
      </header>

      {/* TITLE */}
      <h1 className="title">Dashboard</h1>

      {/* Search + Upload */}
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

      {/* TABLE SECTION */}
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
                    <button className="analyze-btn">
                      Analyze
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

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