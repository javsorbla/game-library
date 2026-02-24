import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "../static/css/TierList.css";

const API = "http://localhost:8000/api";

const TIER_COLORS = {
  S: "#ff7f7f",
  A: "#ffbf7f",
  B: "#ffff7f",
  C: "#7fff7f",
  D: "#7fbfff",
};

function getCsrf() {
  const match = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="));
  return match ? match.split("=")[1] : "";
}

// ─── Progress bar ─────────────────────────────────────────────────────────────
function ProgressBar({ done, total, label }) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return (
    <div className="ms-progress-wrapper">
      <div className="ms-progress-bar" style={{ width: `${pct}%` }} />
      <span className="ms-progress-label">
        {label && <strong>{label} · </strong>}
        {done} / {total} ({pct}%)
      </span>
    </div>
  );
}

// ─── Phase badge ──────────────────────────────────────────────────────────────
function PhaseBadge({ phase, groupInfo }) {
  if (phase === "groups") {
    return (
      <div className="ms-phase-badge groups">
        🏟 Group stage
        {groupInfo && <span className="ms-genre-tag">{groupInfo.genre}</span>}
      </div>
    );
  }
  if (phase === "final") {
    return <div className="ms-phase-badge final">🏆 Final</div>;
  }
  return null;
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
        {game.rating != null && <span>⭐ {Number(game.rating).toFixed(1)}</span>}
      </div>
    </button>
  );
}

// ─── Final tier list result ───────────────────────────────────────────────────
function TierResult({ ranking }) {
  const grouped = Object.keys(TIER_COLORS).reduce((acc, tier) => {
    acc[tier] = ranking.filter((g) => g.tier === tier);
    return acc;
  }, {});

  return (
    <div className="ms-result">
      <h2 className="ms-result-title">Your Tier List</h2>
      {Object.entries(TIER_COLORS).map(([tier, color]) => {
        const games = grouped[tier];
        if (!games || games.length === 0) return null;
        return (
          <div key={tier} className="ms-tier-row">
            <div className="ms-tier-label" style={{ background: color }}>
              {tier}
            </div>
            <div className="ms-tier-games">
              {games.map((g) => (
                <div key={g.id} className="ms-tier-game">
                  <img
                    src={g.image || "https://placehold.co/80x80/1a1a2e/white?text=?"}
                    alt={g.name}
                  />
                  <span className="ms-tier-game-rank">#{g.rank}</span>
                  <span className="ms-tier-game-name">{g.name}</span>
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
  const [uiState, setUiState] = useState("loading"); // loading | idle | playing | done | error
  const [session, setSession] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const applySession = (data) => {
    setSession(data);
    setUiState(data.phase === "finished" ? "done" : "playing");
  };

  // check for existing session on mount
  useEffect(() => {
    axios
      .get(`${API}/games/tournament/status/`)
      .then((res) => applySession(res.data))
      .catch((err) => {
        if (err.response?.status === 404) setUiState("idle");
        else { setError("Could not load session."); setUiState("error"); }
      });
  }, []);

  const handleStart = useCallback(() => {
    setUiState("loading");
    setError(null);
    axios
      .post(`${API}/games/tournament/start/`, {}, { headers: { "X-CSRFToken": getCsrf() } })
      .then((res) => applySession(res.data))
      .catch((err) => {
        setError(err.response?.data?.detail || "Could not start session.");
        setUiState("error");
      });
  }, []);

  const handleChoose = useCallback((winner) => {
    if (!session?.pair || busy) return;
    const loser = session.pair.find((g) => g.id !== winner.id);
    setBusy(true);
    axios
      .post(
        `${API}/games/tournament/answer/`,
        { winner: winner.id, loser: loser.id },
        { headers: { "X-CSRFToken": getCsrf() } }
      )
      .then((res) => { applySession(res.data); setBusy(false); })
      .catch((err) => {
        setError(err.response?.data?.detail || "Error submitting answer.");
        setUiState("error");
        setBusy(false);
      });
  }, [session, busy]);

  const handleRestart = () => {
    if (window.confirm("Restart? Your current progress will be lost.")) handleStart();
  };

  // group-level progress (shown inside the global bar during group stage)
  const groupLabel = session?.group_info
    ? `${session.group_info.genre} (${session.group_info.done}/${session.group_info.total})`
    : null;

  return (
    <div className="ms-container">
      <div className="ms-header">
        <button className="ms-back-btn" onClick={onBack}>← Back</button>
        <h1 className="ms-title">Tier List Builder</h1>
      </div>

      {uiState === "idle" && (
        <div className="ms-idle">
          <p>
            Your played games will be split into genre groups. The best from
            each group advance to the final — just pick your favourite each time.
          </p>
          <button className="ms-start-btn" onClick={handleStart}>Start Tier List</button>
        </div>
      )}

      {uiState === "loading" && <p className="ms-loading">Loading…</p>}

      {uiState === "error" && (
        <div className="ms-error">
          <p>{error}</p>
          <button className="ms-start-btn" onClick={handleStart}>Try again</button>
        </div>
      )}

      {uiState === "playing" && session && (
        <div className="ms-comparing">
          <PhaseBadge phase={session.phase} groupInfo={session.group_info} />
          <ProgressBar done={session.done} total={session.total} label={groupLabel} />
          <p className="ms-instruction">Which game do you prefer?</p>
          <div className="ms-pair">
            {session.pair?.map((game) => (
              <CompareCard key={game.id} game={game} onChoose={handleChoose} />
            ))}
          </div>
          <button className="ms-restart-btn" onClick={handleRestart}>Restart</button>
        </div>
      )}

      {uiState === "done" && session?.ranking && (
        <div>
          <TierResult ranking={session.ranking} />
          <button className="ms-start-btn ms-restart-final" onClick={handleStart}>
            Redo Tier List
          </button>
        </div>
      )}
    </div>
  );
}