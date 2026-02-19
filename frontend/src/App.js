import { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import axios from "axios";

import Login from "./auth/Login";
import Register from "./auth/Register";
import GameList from "./games/GameList";
import Navbar from "./Navbar";

// send cookies and CSRF header on every request
axios.defaults.withCredentials = true;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // when the app loads try to hit a protected endpoint to see if a
  // session cookie already exists. this keeps the user logged in across
  // refreshes.
  useEffect(() => {
    axios
      .get("http://localhost:8000/api/genres/")
      .then(() => setIsAuthenticated(true))
      .catch(() => setIsAuthenticated(false));
  }, []);

  const location = useLocation();

  const handleLogout = async () => {
    try {
      await axios.post("http://localhost:8000/api/logout/");
    } catch (_) {
      // ignore errors; just clear state
    }
    setIsAuthenticated(false);
  };

  const PrivateRoute = ({ children }) => {
    return isAuthenticated ? children : <Navigate to="/login" />;
  };


  return (
    <Router>
      {/* only show navbar on non-auth pages */}
      {isAuthenticated && !["/login", "/register"].includes(location.pathname) && (
        <Navbar onLogout={handleLogout} />
      )}
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" />
            ) : (
              <Login setAuthenticated={setIsAuthenticated} />
            )
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" />
            ) : (
              <Register setAuthenticated={setIsAuthenticated} />
            )
          }
        />
        <Route 
          path="/dashboard" 
          element={
            <PrivateRoute>
              <GameList />
            </PrivateRoute>
          } 
        />
        <Route 
          path="/" 
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} 
        />
      </Routes>
    </Router>
  );
}

export default App;
