import logo from "./assets/logo.png";
import hero from "./assets/hero.png";
import uploadIcon from "./assets/upload.png";
import ai from "./assets/ai.png";
import cleaning from "./assets/cleaning.png";
import reports from "./assets/reports.png";
import bottom from "./assets/bottom.png";

export default function App() {
  return (
    <div className="container">

      {/* NAVBAR */}
      <header className="navbar">
        <div className="nav-left">
          <img src={logo} alt="logo" />
        </div>

        <nav className="nav-links">
          <a className="active">Home</a>
          <a>Dashboard</a>
          <a>Features</a>
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
            <br />
            with <span>AMRESCO Automation</span>
          </h1>

          <p>
            Automate Data Quality Checks, Anomaly Detection, and Performance
            Reporting with AI-Powered Excel Analysis
          </p>

          <div className="upload-card">
            <h3>Upload an XLSX File</h3>

            <div className="drop-area">
              <img src={uploadIcon} alt="upload" />
              <p>Drag & drop your XLSX file or</p>
              <button className="choose">Choose File</button>
              <small>Only .xlsx files are supported</small>
            </div>

            <button className="upload-btn">Upload File</button>
          </div>

          <div className="features">
            <div>
              <img src={ai} alt="" />
              <span>AI Agents</span>
            </div>

            <div>
              <img src={cleaning} alt="" />
              <span>Data Cleaning</span>
            </div>

            <div>
              <img src={reports} alt="" />
              <span>Detailed Reports</span>
            </div>
          </div>

          <img src={bottom} className="bottom-img" alt="" />
        </div>

        {/* RIGHT SIDE */}
        <div className="right">

          <img src={hero} alt="hero" className="hero-img" />

          <div className="about">
            <h2>About AMRESCO Automation</h2>

            <p>
              AMRESCO Automation leverages advanced AI to transform raw Excel data
              into valuable insights. Upload your XLSX file, and let our intelligent
              agents automatically analyze and detect missing data, zero values,
              anomalies, and performance patterns.
            </p>

            <ul>
              <li>AI-Powered Analysis and Reporting</li>
              <li>Data Quality Assurance</li>
              <li>Streamlined Performance Insights</li>
            </ul>

            <p className="footer">
              Empowering enterprises with real-time data quality analysis and performance.
            </p>
          </div>

        </div>

      </section>

    </div>
  );
}