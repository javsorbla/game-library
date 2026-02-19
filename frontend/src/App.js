import { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";

import Login from "./auth/Login";
import Register from "./auth/Register";
import GameList from "./games/GameList";
import Navbar from "./Navbar";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");

  // apply stored token synchronously so child components can fetch immediately
  if (token && !axios.defaults.headers.common["Authorization"]) {
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  }

  const handleLogout = () => {
    setToken("");
    localStorage.removeItem("token");
    delete axios.defaults.headers.common["Authorization"];
  };

  useEffect(() => {
    if (token) {
      localStorage.setItem("token", token);
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    }
  }, [token]);

  const PrivateRoute = ({ children }) => {
    return token ? children : <Navigate to="/login" />;
  };

  return (
    <Router>
      {token && <Navbar onLogout={handleLogout} />}
      <Routes>
        <Route 
          path="/login" 
          element={<Login setToken={setToken} />} 
        />
        <Route
          path="/register"
          element={<Register setToken={setToken} />}
        />
        <Route 
          path="/dashboard" 
          element={
            <PrivateRoute>
              <GameList token={token} />
            </PrivateRoute>
          } 
        />
        <Route 
          path="/" 
          element={<Navigate to={token ? "/dashboard" : "/login"} />} 
        />
      </Routes>
    </Router>
  );
}

export default App;
