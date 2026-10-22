import { createContext, useContext, useState } from "react";
import { api, clearToken, getToken, setToken } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [loggedIn, setLoggedIn] = useState(Boolean(getToken()));

  const login = async (username, password) => {
    const data = await api("/admin/login/", { method: "POST", body: { username, password } });
    setToken(data.token);
    setLoggedIn(true);
  };
  const logout = () => {
    clearToken();
    setLoggedIn(false);
  };

  return <AuthContext.Provider value={{ loggedIn, login, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
