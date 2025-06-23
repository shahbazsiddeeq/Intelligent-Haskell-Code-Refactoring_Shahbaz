import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:8000' });

export const ingest = (formData) => API.post('/ingest', formData, { headers: { 'Content-Type': 'multipart/form-data' }});