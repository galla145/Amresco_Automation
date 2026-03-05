import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const getFiles = () => API.get("/files");

export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/upload", formData);
};

// ✅ ADD THIS
export const analyzeFile = (filename) =>
  API.get(`/analyze/${encodeURIComponent(filename)}`);