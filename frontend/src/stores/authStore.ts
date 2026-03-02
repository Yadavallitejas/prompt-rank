/**
 * PromptRank — Zustand Auth Store
 *
 * Manages user authentication state with localStorage persistence.
 */

import { create } from "zustand";
import api from "@/lib/api";

export interface User {
    id: string;
    username: string;
    email: string;
    rating: number;
    role: string;
    created_at: string;
}

interface AuthState {
    user: User | null;
    token: string | null;
    isLoading: boolean;

    /** Register a new user */
    register: (
        username: string,
        email: string,
        password: string
    ) => Promise<void>;

    /** Log in and persist JWT */
    login: (email: string, password: string) => Promise<void>;

    /** Fetch current user profile from /auth/me */
    fetchMe: () => Promise<void>;

    /** Clear auth state */
    logout: () => void;

    /** Hydrate token from localStorage on mount */
    hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
    user: null,
    token:
        typeof window !== "undefined"
            ? localStorage.getItem("pr_token")
            : null,
    isLoading: false,

    register: async (username, email, password) => {
        set({ isLoading: true });
        try {
            await api.post("/auth/register", { username, email, password });
            // Auto-login after registration
            await get().login(email, password);
        } finally {
            set({ isLoading: false });
        }
    },

    login: async (email, password) => {
        set({ isLoading: true });
        try {
            const { data } = await api.post("/auth/login", { email, password });
            const token = data.access_token;
            localStorage.setItem("pr_token", token);
            set({ token });
            // Fetch user profile
            await get().fetchMe();
        } finally {
            set({ isLoading: false });
        }
    },

    fetchMe: async () => {
        try {
            const { data } = await api.get("/auth/me");
            set({ user: data });
        } catch {
            // Token invalid/expired
            get().logout();
        }
    },

    logout: () => {
        localStorage.removeItem("pr_token");
        set({ user: null, token: null });
    },

    hydrate: () => {
        const token = localStorage.getItem("pr_token");
        if (token) {
            set({ token });
            get().fetchMe();
        }
    },
}));
