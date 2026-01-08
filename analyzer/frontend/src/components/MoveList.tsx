'use client';

interface Move {
  timestamp: number;
  card: string;
  player: string;
  quality: string;
  symbol: string;
  explanation: string;
  eval_change: number;
}

interface Props {
  moves: Move[];
  selectedTimestamp: number;
  onMoveSelect: (timestamp: number) => void;
}

const getQualityColor = (quality: string): string => {
  const colors: Record<string, string> = {
    brilliant: 'text-brilliant bg-brilliant/10 border-brilliant',
    great: 'text-great bg-great/10 border-great',
    good: 'text-good bg-good/10 border-good',
    book: 'text-book bg-book/10 border-book',
    inaccuracy: 'text-inaccuracy bg-inaccuracy/10 border-inaccuracy',
    mistake: 'text-mistake bg-mistake/10 border-mistake',
    blunder: 'text-blunder bg-blunder/10 border-blunder',
  };
  return colors[quality] || 'text-slate-400 bg-slate-700/10 border-slate-600';
};

export default function MoveList({ moves, selectedTimestamp, onMoveSelect }: Props) {
  return (
    <div className="bg-slate-800 rounded-lg h-[calc(100vh-12rem)] flex flex-col">
      <div className="p-4 border-b border-slate-700">
        <h2 className="text-xl font-bold text-white">Move List</h2>
        <p className="text-sm text-slate-400 mt-1">{moves.length} moves analyzed</p>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {moves.map((move, idx) => {
          const isSelected = Math.abs(move.timestamp - selectedTimestamp) < 0.5;

          return (
            <button
              key={idx}
              onClick={() => onMoveSelect(move.timestamp)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                isSelected
                  ? 'bg-blue-500/20 border-blue-500'
                  : 'bg-slate-700/50 border-slate-600 hover:bg-slate-700'
              }`}
            >
              {/* Move Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">
                    {move.timestamp.toFixed(1)}s
                  </span>
                  <span className="text-sm font-semibold text-white">
                    {move.card}
                  </span>
                  {move.symbol && (
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded border ${getQualityColor(
                        move.quality
                      )}`}
                    >
                      {move.symbol}
                    </span>
                  )}
                </div>
                <span
                  className={`text-sm font-mono ${
                    move.eval_change >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {move.eval_change >= 0 ? '+' : ''}
                  {move.eval_change.toFixed(1)}
                </span>
              </div>

              {/* Move Quality Badge */}
              {move.quality !== 'book' && (
                <div className="mb-2">
                  <span
                    className={`text-xs px-2 py-1 rounded capitalize ${getQualityColor(
                      move.quality
                    )}`}
                  >
                    {move.quality}
                  </span>
                </div>
              )}

              {/* Explanation */}
              {isSelected && move.explanation && (
                <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                  {move.explanation}
                </p>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
