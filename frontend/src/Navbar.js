import { Link } from "react-router-dom";
import "./static/css/Navbar.css";

export default function Navbar({ onLogout }) {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/dashboard">Game Library</Link>
      </div>
      <div className="nav-links">
        <Link to="/tier">Tier List</Link>
      </div>
      <div className="nav-actions">
        <button className="logout-button" onClick={onLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
}
