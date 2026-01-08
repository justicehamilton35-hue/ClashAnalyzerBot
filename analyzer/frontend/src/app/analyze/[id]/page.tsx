'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
  getAnalysisStatus,
  getAnalysisResult,
  pollAnalysisStatus,
  AnalysisJob,
  AnalysisResult,
} from '@/lib/api';
import EvaluationGraph from '@/components/EvaluationGraph';
import MoveList from '@/components/MoveList';
import AnalysisSummary from '@/components/AnalysisSummary';

export default function AnalyzePage() {
  const params = useParams();
  const jobId = params.id as string;

  const [status, setStatus] = useState<AnalysisJob | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimestamp, setSelectedTimestamp] = useState<number>(0);

  useEffect(() => {
    if (!jobId) return;

    // Start polling for status
    pollAnalysisStatus(jobId, (updatedStatus) => {
      setStatus(updatedStatus);
    })
      .then(async (finalStatus) => {
        // Analysis complete - fetch result
        const analysisResult = await getAnalysisResult(jobId);
        setResult(analysisResult);
      })
      .catch((err) => {
        setError(err.message || 'Analysis failed');
      });
  }, [jobId]);

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-white mb-4">Analysis Failed</h1>
          <p className="text-slate-400 mb-8">{error}</p>
          <a
            href="/"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Back to Home
          </a>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="bg-slate-800 rounded-lg p-12 text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-white mb-4">
              {status?.status === 'processing'
                ? 'Analyzing Your Game...'
                : 'Loading...'}
            </h2>
            <p className="text-slate-400 mb-6">{status?.message}</p>
            {status && (
              <div className="max-w-md mx-auto">
                <div className="w-full bg-slate-700 rounded-full h-3 mb-2">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${status.progress * 100}%` }}
                  />
                </div>
                <p className="text-sm text-slate-500">
                  {(status.progress * 100).toFixed(0)}% complete
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <a
                href="/"
                className="text-sm text-slate-400 hover:text-white mb-2 block"
              >
                ← Back to Home
              </a>
              <h1 className="text-2xl font-bold text-white">Game Analysis</h1>
            </div>
            <div className="flex gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">
                  {result.performance.accuracy_score.toFixed(1)}%
                </div>
                <div className="text-sm text-slate-400">Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white capitalize">
                  {result.playstyle.type}
                </div>
                <div className="text-sm text-slate-400">Playstyle</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout - Chess.com Style */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Analysis Summary */}
          <div className="col-span-3">
            <AnalysisSummary result={result} />
          </div>

          {/* Center - Evaluation Graph and Timeline */}
          <div className="col-span-6">
            <div className="bg-slate-800 rounded-lg p-6 mb-6">
              <h2 className="text-xl font-bold text-white mb-4">
                Evaluation & Win Probability
              </h2>
              <EvaluationGraph
                timeline={result.timeline}
                selectedTimestamp={selectedTimestamp}
                onTimestampSelect={setSelectedTimestamp}
              />
            </div>

            {/* Game Board Visualization (Placeholder) */}
            <div className="bg-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">
                Game State
              </h2>
              <div className="aspect-[9/16] bg-slate-700 rounded-lg flex items-center justify-center">
                <p className="text-slate-400">
                  Video playback at timestamp: {selectedTimestamp.toFixed(2)}s
                </p>
              </div>
            </div>
          </div>

          {/* Right Sidebar - Move List */}
          <div className="col-span-3">
            <MoveList
              moves={result.moves}
              selectedTimestamp={selectedTimestamp}
              onMoveSelect={(timestamp) => setSelectedTimestamp(timestamp)}
            />
          </div>
        </div>

        {/* Key Moments */}
        {result.key_moments && result.key_moments.length > 0 && (
          <div className="mt-6 bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Key Moments</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.key_moments.map((moment, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedTimestamp(moment.timestamp)}
                  className="bg-slate-700 rounded-lg p-4 cursor-pointer hover:bg-slate-600 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-white">
                      {moment.card} {moment.symbol}
                    </span>
                    <span className="text-sm text-slate-400">
                      {moment.timestamp.toFixed(1)}s
                    </span>
                  </div>
                  <p className="text-sm text-slate-300">{moment.explanation}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
