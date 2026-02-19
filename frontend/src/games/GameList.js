import { useState, useEffect } from "react";
import axios from "axios";
import GameCard from "./GameCard";
import "../static/css/GameList.css";

const GameList = ({ token }) => {
  const [games, setGames] = useState([]);

  useEffect(() => {
    if (!token) {
      return; // nothing to do if we don't have a token yet
    }
    // ensures header is set for this request in case parent didn't
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;

    axios
      .get("http://localhost:8000/api/games/")
      .then((res) => setGames(res.data))
      .catch((err) => {
        if (err.response && err.response.status === 401) {
          // token may have expired; redirect to login by reloading
          window.location.href = "/login";
        } else {
          console.error(err);
        }
      });
  }, [token]);

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">Videogame Dashboard</h1>
      <div className="games-grid">
        {games.map((game) => (
          <GameCard key={game.id} game={game} />
        ))}
      </div>
    </div>
  );
};

export default GameList;
