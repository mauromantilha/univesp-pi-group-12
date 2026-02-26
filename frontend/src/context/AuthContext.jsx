import { createContext, useContext, useState, useEffect } from "react";
import api from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMe().finally(() => setLoading(false));
  }, []);

  async function fetchMe() {
    try {
      const res = await api.get("/usuarios/me/");
      setUser(res.data);
      setToken("authenticated");
      return true;
    } catch {
      setUser(null);
      setToken(null);
      return false;
    }
  }

  async function login(username, password) {
    const res = await api.post("/auth/login/", { username, password });
    if (res.data?.user) {
      setUser(res.data.user);
      setToken("authenticated");
    } else {
      await fetchMe();
    }
    return res.data;
  }

  async function logout() {
    try {
      await api.post("/auth/logout/", {});
    } catch {
      // ignora erro de logout remoto
    }
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout, fetchMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
