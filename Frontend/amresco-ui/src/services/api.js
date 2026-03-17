import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000"
});

export const uploadFile = (file) => {

  const formData = new FormData();
  formData.append("file", file);

  return API.post("/upload", formData);

};

export const getFiles = () => {
  return API.get("/files");
};

export const analyzeFile = (filename) => {
  return API.get(`/analyze/${filename}`);
};

