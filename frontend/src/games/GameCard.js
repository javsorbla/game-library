
import { useState } from "react";
import axios from "axios";

const GameCard = ({ game, onTogglePlayed }) => {
  // fallback to false if the field isn't present
  const [isPlayed, setIsPlayed] = useState(game.is_played || false);

  const getCsrf = () => {
    const split = document.cookie.split('; ').find((c) => c.startsWith('csrftoken='));
    return split ? split.split('=')[1] : '';
  };

  const handleToggle = () => {
    const method = isPlayed ? "delete" : "post";
    axios({
      method,
      url: `http://localhost:8000/api/games/${game.id}/played/`,
      headers: {
        'X-CSRFToken': getCsrf(),
      },
    })
      .then((res) => {
        if (method === "post") {
          setIsPlayed(true);
          if (onTogglePlayed) onTogglePlayed(res.data);
        } else {
          setIsPlayed(false);
          if (onTogglePlayed)
            onTogglePlayed({ ...game, is_played: false });
        }
      })
      .catch((err) => console.error(err));
  };

  return (
    <div className="game-card">
      <img src={game.image || "https://via.placeholder.com/200"} alt={game.name} />
      <h3 title={game.name}>{game.name}</h3>
      <p>Genre: {game.genre}</p>
      <p>Release Date: {game.release_date}</p>
      <p>Platform: {game.platform}</p>
      <p>Rating: {game.rating} ⭐</p>
      <label className="played-checkbox">
        <input
          type="checkbox"
          checked={isPlayed}
          onChange={handleToggle}
        />
        Played
      </label>
    </div>
  );
};

export default GameCard;