type Player = { name: string; score: number };

function topScorerName(players: Player[], rank: number): string {
  const sorted = [...players].sort((a, b) => b.score - a.score);
  const winner = sorted[rank];
  return winner.name.toUpperCase();
}

const players: Player[] = [
  { name: "Ada", score: 42 },
  { name: "Grace", score: 91 },
];

console.log(topScorerName(players, 5));
