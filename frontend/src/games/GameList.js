import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import GameCard from "./GameCard";
import "../static/css/GameList.css";

const GameList = () => {
  const [games, setGames] = useState([]);
  const [pageInfo, setPageInfo] = useState({ next: null, previous: null, count: 0 });
  const [currentPage, setCurrentPage] = useState(1);
  const [genres, setGenres] = useState([]);
  const [platforms, setPlatforms] = useState([]);
  const [selectedGenre, setSelectedGenre] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("");
  const [selectedPlayed, setSelectedPlayed] = useState("");

  // utility that fetches games from the API using filters and pagination
  const fetchGames = () => {
    const params = { page: currentPage };
    if (selectedGenre) params.genre = selectedGenre;
    if (selectedPlatform) params.platform = selectedPlatform;
    if (selectedPlayed === "played") params.played = true;
    if (selectedPlayed === "unplayed") params.played = false;

    axios
      .get("http://localhost:8000/api/games/", { params })
      .then((res) => {
        setGames(res.data.results || []);
        setPageInfo({
          next: res.data.next,
          previous: res.data.previous,
          count: res.data.count,
        });
      })
      .catch((err) => {
        console.error(err);
      });
  };

  // reset to first page if any filter value changes
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedGenre, selectedPlatform, selectedPlayed]);

  // initial load and whenever page or filters change
  useEffect(() => {
    fetchGames();
  }, [currentPage, selectedGenre, selectedPlatform, selectedPlayed]);

  // fetch auxiliary lists for filters
  useEffect(() => {
    axios
      .get("http://localhost:8000/api/genres/")
      .then((res) => {
        const data = res.data.results ? res.data.results : res.data;
        setGenres(data);
      })
      .catch((err) => console.error(err));

    axios
      .get("http://localhost:8000/api/platforms/")
      .then((res) => {
        const data = res.data.results ? res.data.results : res.data;
        setPlatforms(data);
      })
      .catch((err) => console.error(err));
  }, []);

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">Videogame Dashboard</h1>
      <div className="options-bar">
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
        <Link to="/tierlist">
          <button className="tierlist-button">Tier List</button>
        </Link>
      </div>

      <div className="games-grid">
        {games.map((game) => (
          <GameCard
            key={game.id}
            game={game}
            onTogglePlayed={(updated) => {
              // update the cached page in-place
              setGames((prev) =>
                prev.map((g) => (g.id === updated.id ? updated : g))
              );
            }}
          />
        ))}
      </div>

      <div className="pagination-controls">
        <button
          disabled={!pageInfo.previous}
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
        >
          Previous
        </button>
        <span>
          Page {currentPage} of {Math.ceil(pageInfo.count / (games.length || 1)) || 1}
        </span>
        <button
          disabled={!pageInfo.next}
          onClick={() => setCurrentPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default GameList;

