/**
 * PromptRank — Axios API Client
 *
 * Configured with base URL pointing to the FastAPI backend.
 * Automatically attaches JWT token from the auth store.
 */

import axios from "axios";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 15000,
});

// ── Request interceptor: attach JWT ────────────────────────────────────
api.interceptors.request.use(
    (config) => {
        if (typeof window !== "undefined") {
            const token = localStorage.getItem("pr_token");
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// ── Response interceptor: handle 401 ───────────────────────────────────
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== "undefined") {
            localStorage.removeItem("pr_token");
            // Optionally redirect to login
            // window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);

export default api;
