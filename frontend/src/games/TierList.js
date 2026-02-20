import { useState, useEffect } from "react";
import axios from "axios";
import GameCard from "./GameCard";
import "../static/css/GameList.css";

const TierList = () => {
  const [pair, setPair] = useState([]);
  const [ratings, setRatings] = useState([]);
  const [viewingResults, setViewingResults] = useState(false);
  const [error, setError] = useState(null);

  const fetchPair = () => {
    axios
      .get("http://localhost:8000/api/games/tier/pair/")
      .then((res) => {
        setPair(res.data || []);
      })
      .catch((err) => {
        console.error(err);
        setError(err.response?.data?.detail || "Unable to fetch pair");
      });
  };

  const submitResult = (winnerId, loserId) => {
    axios
      .post(
        "http://localhost:8000/api/games/tier/submit/",
        { winner: winnerId, loser: loserId },
        { headers: { "X-CSRFToken": getCsrf() } }
      )
      .then(() => {
        // simply fetch another pair
        fetchPair();
      })
      .catch((err) => {
        console.error(err);
        setError(err.response?.data?.detail || "submit failed");
      });
  };

  const fetchRatings = () => {
    axios
      .get("http://localhost:8000/api/games/tier/rankings/")
      .then((res) => setRatings(res.data || []))
      .catch((err) => {
        console.error(err);
        setError(err.response?.data?.detail || "Unable to fetch rankings");
      });
  };

  // helper to read CSRF cookie (same as GameCard)
  const getCsrf = () => {
    const split = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="));
    return split ? split.split("=")[1] : "";
  };

  useEffect(() => {
    if (!viewingResults) {
      fetchPair();
    }
  }, [viewingResults]);

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">Played Games Tier List</h1>
      {error && <p className="error">{error}</p>}

      {!viewingResults ? (
        <div>
          {pair.length === 2 ? (
            <div className="pair-container">
              {pair.map((g) => (
                <div key={g.id} className="tier-card" onClick={() => {
                    const loser = pair.find(x => x.id !== g.id);
                    submitResult(g.id, loser.id);
                  }}>
                  <GameCard game={g} />
                  <button className="choose-button">Select</button>
                </div>
              ))}
            </div>
          ) : (
            <p>Loading games...</p>
          )}
        </div>
      ) : (
        <div className="rankings-list">
          {ratings.map((g, idx) => (
            <div key={g.id} className="ranking-item">
              {idx + 1}. {g.name} ({g.tier_rating.toFixed(1)})
            </div>
          ))}
        </div>
      )}

      <button
        className="view-rankings-button"
        onClick={() => {
          if (viewingResults) {
            setViewingResults(false);
            setError(null);
          } else {
            fetchRatings();
            setViewingResults(true);
          }
        }}
      >
        {viewingResults ? "Back to comparisons" : "View Rankings"}
      </button>
    </div>
  );
};

export default TierList;
