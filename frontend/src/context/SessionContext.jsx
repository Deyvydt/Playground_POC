import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { TOKEN_KEY, getToken, login as apiLogin, me } from "../api/client";

const SessionContext = createContext(null);

const clearToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
};

export function SessionProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [status, setStatus] = useState(() => (getToken() ? "checking" : "anonymous"));

  useEffect(() => {
    if (!getToken()) return;
    me()
      .then((user) => {
        setCurrentUser(user);
        setStatus("authenticated");
      })
      .catch(() => {
        clearToken();
        setStatus("anonymous");
      });
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setCurrentUser(null);
    setStatus("anonymous");
  }, []);

  useEffect(() => {
    window.addEventListener("auth:expired", logout);
    return () => window.removeEventListener("auth:expired", logout);
  }, [logout]);

  const login = async (email, password, remember) => {
    const { token, user } = await apiLogin(email, password);
    clearToken();
    (remember ? localStorage : sessionStorage).setItem(TOKEN_KEY, token);
    if (remember) localStorage.setItem("ap-last-email", email);
    return () => {
      setCurrentUser(user);
      setStatus("authenticated");
    };
  };

  const can = (permission) => Boolean(currentUser?.permissions?.includes(permission));

  return (
    <SessionContext.Provider
      value={{ currentUser, setCurrentUser, status, isAuthenticated: status === "authenticated", login, logout, can }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export const useSession = () => useContext(SessionContext);
