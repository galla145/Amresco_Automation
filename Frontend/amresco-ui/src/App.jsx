import { BrowserRouter, Routes, Route } from "react-router-dom";

import Upload from "./pages/Upload";
import Dashboard from "./pages/Dashboard";
import MissingValues from "./pages/MissingValues";
import Analysis from "./pages/Analysis";
import MissingAnalysis from "./pages/MissingAnalysis";
import AnomalyDetection from "./pages/AnomalyDetection";
import AINotes from "./pages/AINotes";
import FormulaAnalysis from "./pages/FormulaAnalysis";
import AnomalyAnalysis from "./pages/AnomalyAnalysis";
import FormulaDetection from "./pages/FormulaDetection";
import SignIn from "./pages/SignIn";
import Signup from "./pages/Signup";

import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>

      <Routes>

        {/* Public Routes */}
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protected Routes */}
        <Route path="/" element={<Upload />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/missing-analysis"
          element={
            <ProtectedRoute>
              <MissingAnalysis />
            </ProtectedRoute>
          }
        />

        <Route
          path="/missing-values"
          element={
            <ProtectedRoute>
              <MissingValues />
            </ProtectedRoute>
          }
        />

        <Route
          path="/analysis"
          element={
            <ProtectedRoute>
              <Analysis />
            </ProtectedRoute>
          }
        />

        <Route
          path="/anomaly-detection"
          element={
            <ProtectedRoute>
              <AnomalyDetection />
            </ProtectedRoute>
          }
        />

        <Route
          path="/ai-notes"
          element={
            <ProtectedRoute>
              <AINotes />
            </ProtectedRoute>
          }
        />

        <Route
          path="/formula-analysis"
          element={
            <ProtectedRoute>
              <FormulaAnalysis />
            </ProtectedRoute>
          }
        />

        <Route
          path="/formula-detection"
          element={
            <ProtectedRoute>
              <FormulaDetection />
            </ProtectedRoute>
          }
        />

        <Route
          path="/anomaly-analysis"
          element={
            <ProtectedRoute>
              <AnomalyAnalysis />
            </ProtectedRoute>
          }
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;