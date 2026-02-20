
const TierListGameCard = ({ game, onTogglePlayed }) => {

  return (
    <div className="tier-list-game-card">
      <img src={game.image || "https://via.placeholder.com/200"} alt={game.name} />
      <div className="info">
        <h3 title={game.name}>{game.name}</h3>
        <p>Genre: {game.genre}</p>
        <p>Release Date: {game.release_date}</p>
        <p>Platform: {game.platform}</p>
        <p>Rating: {game.rating} ⭐</p>
      </div>
    </div>
  );
};

export default TierListGameCard;