'use client';

import { AnalysisResult } from '@/lib/api';

interface Props {
  result: AnalysisResult;
}

export default function AnalysisSummary({ result }: Props) {
  const { performance, playstyle, insights } = result;

  return (
    <div className="space-y-4">
      {/* Overall Score */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Overall Score</h3>

        <div className="text-center mb-6">
          <div className="text-5xl font-bold text-blue-400 mb-2">
            {performance.accuracy_score.toFixed(1)}%
          </div>
          <div className="text-sm text-slate-400">Accuracy</div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-400">Evaluation</span>
              <span className={performance.average_evaluation >= 0 ? 'text-green-400' : 'text-red-400'}>
                {performance.average_evaluation >= 0 ? '+' : ''}
                {performance.average_evaluation.toFixed(2)}
              </span>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-400">Win Probability</span>
              <span className="text-white">
                {(performance.average_win_probability * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Move Quality */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Move Quality</h3>

        <div className="space-y-2">
          {performance.move_quality.brilliant > 0 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-brilliant">⭐ Brilliant (!!!)</span>
              <span className="text-white font-semibold">
                {performance.move_quality.brilliant}
              </span>
            </div>
          )}

          {performance.move_quality.great > 0 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-great">Great (!!)</span>
              <span className="text-white font-semibold">
                {performance.move_quality.great}
              </span>
            </div>
          )}

          {performance.move_quality.good > 0 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-good">Good (!)</span>
              <span className="text-white font-semibold">
                {performance.move_quality.good}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between text-sm">
            <span className="text-book">Book</span>
            <span className="text-white font-semibold">
              {performance.move_quality.book}
            </span>
          </div>

          {performance.move_quality.inaccuracies > 0 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-inaccuracy">Inaccuracy (?!)</span>
              <span className="text-white font-semibold">
                {performance.move_quality.inaccuracies}
              </span>
            </div>
          )}

          {performance.move_quality.mistakes > 0 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-mistake">Mistake (?)</span>
              <span className="text-white font-semibold">
                {performance.move_quality.mistakes}
              </span>
            </div>
          )}

          {performance.move_quality.blunders > 0 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-blunder">⚠️ Blunder (??)</span>
              <span className="text-white font-semibold">
                {performance.move_quality.blunders}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Playstyle */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Playstyle</h3>

        <div className="text-center mb-4">
          <div className="text-2xl font-bold text-blue-400 capitalize mb-1">
            {playstyle.type}
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-400">Aggression</span>
              <span className="text-white">{playstyle.aggression_rating.toFixed(1)}/10</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-red-500 h-2 rounded-full"
                style={{ width: `${playstyle.aggression_rating * 10}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-400">Defense</span>
              <span className="text-white">{playstyle.defense_rating.toFixed(1)}/10</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${playstyle.defense_rating * 10}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-400">Elixir Efficiency</span>
              <span className="text-white">{playstyle.elixir_efficiency.toFixed(1)}/10</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full"
                style={{ width: `${playstyle.elixir_efficiency * 10}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Insights */}
      {(insights.strengths.length > 0 || insights.weaknesses.length > 0) && (
        <div className="bg-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Insights</h3>

          {insights.strengths.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-green-400 mb-2">Strengths</h4>
              <ul className="space-y-2">
                {insights.strengths.map((strength, idx) => (
                  <li key={idx} className="text-sm text-slate-300 flex items-start">
                    <span className="text-green-400 mr-2">✓</span>
                    {strength}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {insights.weaknesses.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-red-400 mb-2">Weaknesses</h4>
              <ul className="space-y-2">
                {insights.weaknesses.map((weakness, idx) => (
                  <li key={idx} className="text-sm text-slate-300 flex items-start">
                    <span className="text-red-400 mr-2">✗</span>
                    {weakness}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {insights.suggestions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-blue-400 mb-2">Suggestions</h4>
              <ul className="space-y-2">
                {insights.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="text-sm text-slate-300 flex items-start">
                    <span className="text-blue-400 mr-2">💡</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
