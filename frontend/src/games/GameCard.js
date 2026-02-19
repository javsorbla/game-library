
const GameCard = ({ game }) => {
  return (
    <div className="game-card">
      <img src={game.image || "https://via.placeholder.com/200"} alt={game.name} />
      <h2>{game.name}</h2>
      <p>Genre: {game.genre}</p>
      <p>Platform: {game.platform}</p>
      <p>Rating: {game.rating} ⭐</p>
    </div>
  );
};

export default GameCard;