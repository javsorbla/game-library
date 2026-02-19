import { useState, useEffect } from "react";
import axios from "axios";
import GameCard from "./GameCard";
import "../static/css/GameList.css";

const GameList = ({ token }) => {
  const [games, setGames] = useState([]);
  const [genres, setGenres] = useState([]);
  const [platforms, setPlatforms] = useState([]);
  const [selectedGenre, setSelectedGenre] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("");
  const [selectedPlayed, setSelectedPlayed] = useState("");

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

  // fetch auxiliary lists for filters
  useEffect(() => {
    if (!token) return;

    axios
      .get("http://localhost:8000/api/genres/")
      .then((res) => setGenres(res.data))
      .catch((err) => console.error(err));

    axios
      .get("http://localhost:8000/api/platforms/")
      .then((res) => setPlatforms(res.data))
      .catch((err) => console.error(err));
  }, [token]);

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">Videogame Dashboard</h1>
      <div className="filters">
        <label>
          Genre:
          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
          >
            <option value="">All</option>
            {genres.map((g) => (
              <option key={g.id} value={g.name}>
                {g.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Platform:
          <select
            value={selectedPlatform}
            onChange={(e) => setSelectedPlatform(e.target.value)}
          >
            <option value="">All</option>
            {platforms.map((p) => (
              <option key={p.id} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Played:
          <select
            value={selectedPlayed}
            onChange={(e) => setSelectedPlayed(e.target.value)}
          >
            <option value="">All</option>
            <option value="played">Played</option>
            <option value="unplayed">Not Played</option>
          </select>
        </label>
      </div>

      <div className="games-grid">
        {games
          .filter((game) => {
            if (selectedGenre && !game.genre.includes(selectedGenre)) return false;
            if (
              selectedPlatform &&
              !game.platform.includes(selectedPlatform)
            )
              return false;
            if (selectedPlayed === "played" && !game.is_played) return false;
            if (selectedPlayed === "unplayed" && game.is_played) return false;
            return true;
          })
          .map((game) => (
            <GameCard
              key={game.id}
              game={game}
              onTogglePlayed={(updated) => {
                setGames((prev) =>
                  prev.map((g) => (g.id === updated.id ? updated : g))
                );
              }}
            />
          ))}
      </div>
    </div>
  );
};

export default GameList;

