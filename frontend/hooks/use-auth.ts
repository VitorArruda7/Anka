"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "anka:token";

export function useAuth() {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    setToken(stored);
    setLoading(false);
  }, []);

  const login = (value: string) => {
    window.localStorage.setItem(STORAGE_KEY, value);
    setToken(value);
  };

  const logout = () => {
    window.localStorage.removeItem(STORAGE_KEY);
    setToken(null);
  };

  return {
    token,
    loading,
    login,
    logout,
    isAuthenticated: Boolean(token),
  };
}
