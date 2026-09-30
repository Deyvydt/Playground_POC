import { createContext, useContext, useEffect, useState } from "react";
import { listUsers } from "../api/client";

const SessionContext = createContext(null);

const FALLBACK_USERS = [
  { id: 1, name: "Ana Ríos", role: "admin", avatar_emoji: "👩‍💼", title: "Gerente Regional" },
  { id: 2, name: "Carlos Vega", role: "developer", avatar_emoji: "🧑‍💻", title: "AI Engineer" },
  { id: 3, name: "Lucía Soto", role: "viewer", avatar_emoji: "🙋‍♀️", title: "Analista de Negocio" },
];

export function SessionProvider({ children }) {
  const [users, setUsers] = useState(FALLBACK_USERS);
  const [currentUser, setCurrentUser] = useState(() => {
    const stored = localStorage.getItem("tcs-playground-user");
    return stored ? JSON.parse(stored) : FALLBACK_USERS[0];
  });

  useEffect(() => {
    listUsers()
      .then((data) => {
        if (data?.length) setUsers(data);
      })
      .catch(() => {});
  }, []);

  const switchUser = (user) => {
    setCurrentUser(user);
    localStorage.setItem("tcs-playground-user", JSON.stringify(user));
  };

  const can = (action) => {
    const role = currentUser?.role;
    if (role === "admin") return true;
    if (role === "developer") return action !== "delete" && action !== "manage_users";
    return action === "chat"; // viewer
  };

  return (
    <SessionContext.Provider value={{ users, currentUser, switchUser, can }}>
      {children}
    </SessionContext.Provider>
  );
}

export const useSession = () => useContext(SessionContext);
