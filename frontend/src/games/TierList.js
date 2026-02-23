import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "../static/css/TierList.css";

const API = "http://localhost:8000/api";

const TIER_COLORS = {
  S: { bg: "#ff7f7f", label: "S" },
  A: { bg: "#ffbf7f", label: "A" },
  B: { bg: "#ffff7f", label: "B" },
  C: { bg: "#7fff7f", label: "C" },
  D: { bg: "#7fbfff", label: "D" },
};

function getCsrf() {
  const match = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="));
  return match ? match.split("=")[1] : "";
}

// ─── Progress bar ────────────────────────────────────────────────────────────
function ProgressBar({ done, total }) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return (
    <div className="ms-progress-wrapper">
      <div className="ms-progress-bar" style={{ width: `${pct}%` }} />
      <span className="ms-progress-label">
        {done} / {total} comparisons ({pct}%)
      </span>
    </div>
  );
}

// ─── Game card for comparison ─────────────────────────────────────────────────
function CompareCard({ game, onChoose }) {
  return (
    <button className="ms-compare-card" onClick={() => onChoose(game)}>
      <img
        src={game.image || "https://placehold.co/400x220/1a1a2e/white?text=No+Image"}
        alt={game.name}
      />
      <div className="ms-compare-card-name">{game.name}</div>
      <div className="ms-compare-card-meta">
        {game.genre && <span>{game.genre}</span>}
        {game.rating && <span>⭐ {game.rating.toFixed(1)}</span>}
      </div>
    </button>
  );
}

// ─── Final tier list ──────────────────────────────────────────────────────────
function TierResult({ result }) {
  const grouped = Object.keys(TIER_COLORS).reduce((acc, tier) => {
    acc[tier] = result.filter((g) => g.tier === tier);
    return acc;
  }, {});

  return (
    <div className="ms-result">
      <h2 className="ms-result-title">Your Tier List</h2>
      {Object.entries(TIER_COLORS).map(([tier, { bg, label }]) => {
        const games = grouped[tier];
        if (!games || games.length === 0) return null;
        return (
          <div key={tier} className="ms-tier-row">
            <div className="ms-tier-label" style={{ background: bg }}>
              {label}
            </div>
            <div className="ms-tier-games">
              {games.map((g) => (
                <div key={g.id} className="ms-tier-game">
                  <img
                    src={g.image || "https://placehold.co/80x80/1a1a2e/white?text=?"}
                    alt={g.name}
                  />
                  <span>{g.name}</span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function TierList({ onBack }) {
  const [phase, setPhase] = useState("idle"); // idle | loading | comparing | done | error
  const [session, setSession] = useState(null); // { finished, done, total, pair, result }
  const [error, setError] = useState(null);
  const [chosen, setChosen] = useState(null); // id of the card the user just tapped

  const applySession = (data) => {
    setSession(data);
    setPhase(data.finished ? "done" : "comparing");
    setChosen(null);
  };

  // Check for an existing session on mount
  useEffect(() => {
    setPhase("loading");
    axios
      .get(`${API}/games/mergesort/status/`)
      .then((res) => applySession(res.data))
      .catch((err) => {
        if (err.response?.status === 404) {
          setPhase("idle");
        } else {
          setError("Could not load session.");
          setPhase("error");
        }
      });
  }, []);

  const handleStart = useCallback(() => {
    setPhase("loading");
    setError(null);
    axios
      .post(`${API}/games/mergesort/start/`, {}, { headers: { "X-CSRFToken": getCsrf() } })
      .then((res) => applySession(res.data))
      .catch((err) => {
        setError(err.response?.data?.detail || "Could not start session.");
        setPhase("error");
      });
  }, []);

  const handleChoose = useCallback(
    (winner) => {
      if (!session?.pair || chosen !== null) return;
      const loser = session.pair.find((g) => g.id !== winner.id);
      setChosen(winner.id);

      axios
        .post(
          `${API}/games/mergesort/answer/`,
          { winner: winner.id, loser: loser.id },
          { headers: { "X-CSRFToken": getCsrf() } }
        )
        .then((res) => applySession(res.data))
        .catch((err) => {
          setError(err.response?.data?.detail || "Error submitting answer.");
          setPhase("error");
        });
    },
    [session, chosen]
  );

  // ── render ────────────────────────────────────────────────────────────────
  return (
    <div className="ms-container">
      <div className="ms-header">
        <button className="ms-back-btn" onClick={onBack}>
          ← Back
        </button>
        <h1 className="ms-title">Tier List Builder</h1>
      </div>

      {phase === "idle" && (
        <div className="ms-idle">
          <p>Build your definitive tier list by comparing your played games one pair at a time.</p>
          <button className="ms-start-btn" onClick={handleStart}>
            Start Tier List
          </button>
        </div>
      )}

      {phase === "loading" && <p className="ms-loading">Loading…</p>}

      {phase === "error" && (
        <div className="ms-error">
          <p>{error}</p>
          <button className="ms-start-btn" onClick={handleStart}>
            Try again
          </button>
        </div>
      )}

      {phase === "comparing" && session && (
        <div className="ms-comparing">
          <ProgressBar done={session.done} total={session.total} />
          <p className="ms-instruction">Which game do you prefer?</p>
          <div className="ms-pair">
            {session.pair.map((game) => (
              <CompareCard
                key={game.id}
                game={game}
                onChoose={handleChoose}
              />
            ))}
          </div>
          <button
            className="ms-restart-btn"
            onClick={() => { if (window.confirm("Restart? Your progress will be lost.")) handleStart(); }}
          >
            Restart
          </button>
        </div>
      )}

      {phase === "done" && session?.result && (
        <div>
          <TierResult result={session.result} />
          <button className="ms-start-btn ms-restart-final" onClick={handleStart}>
            Redo Tier List
          </button>
        </div>
      )}
    </div>
  );
}