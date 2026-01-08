'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { uploadVideo, startAnalysis } from '@/lib/api';

export default function HomePage() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.mp4') || file.name.endsWith('.MP4')) {
        setSelectedFile(file);
      } else {
        alert('Please upload an MP4 file');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setUploading(true);

    try {
      // Upload video
      const { job_id } = await uploadVideo(selectedFile);

      // Start analysis
      await startAnalysis(job_id);

      // Redirect to analysis page
      router.push(`/analyze/${job_id}`);
    } catch (error) {
      console.error('Error starting analysis:', error);
      alert('Failed to start analysis. Please try again.');
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">
                Clash Royale Analyzer
              </h1>
              <p className="text-slate-300 mt-1">
                Stockfish for Clash Royale - Analyze your gameplay like a pro
              </p>
            </div>
            <div className="text-sm text-slate-400">
              Powered by AI
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-slate-700">
            <div className="text-3xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Move Analysis
            </h3>
            <p className="text-slate-300">
              Every card play analyzed and classified as brilliant, good, mistake, or blunder
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-slate-700">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Win Probability
            </h3>
            <p className="text-slate-300">
              Real-time win percentage calculated throughout the entire match
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-slate-700">
            <div className="text-3xl mb-4">🎮</div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Playstyle Insights
            </h3>
            <p className="text-slate-300">
              Understand your playstyle: beatdown, cycle, control, or bridge spam
            </p>
          </div>
        </div>

        {/* Upload Area */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border-2 border-dashed border-slate-600">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-6 text-center">
              Upload Your Gameplay
            </h2>

            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
                dragActive
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-slate-600 hover:border-slate-500'
              }`}
            >
              {selectedFile ? (
                <div>
                  <div className="text-6xl mb-4">✅</div>
                  <p className="text-xl text-white font-semibold mb-2">
                    {selectedFile.name}
                  </p>
                  <p className="text-slate-400 mb-6">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-sm text-slate-400 hover:text-white"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div>
                  <div className="text-6xl mb-4">📹</div>
                  <p className="text-xl text-white mb-2">
                    Drag and drop your MP4 here
                  </p>
                  <p className="text-slate-400 mb-6">
                    or click to browse
                  </p>
                  <input
                    type="file"
                    accept=".mp4,.MP4"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-input"
                  />
                  <label
                    htmlFor="file-input"
                    className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg cursor-pointer transition-colors"
                  >
                    Choose File
                  </label>
                </div>
              )}
            </div>

            {selectedFile && (
              <div className="mt-8 text-center">
                <button
                  onClick={handleAnalyze}
                  disabled={uploading}
                  className={`px-8 py-4 rounded-xl font-bold text-lg transition-all ${
                    uploading
                      ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white shadow-lg hover:shadow-xl'
                  }`}
                >
                  {uploading ? (
                    <span className="flex items-center gap-3">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Starting Analysis...
                    </span>
                  ) : (
                    'Analyze Game'
                  )}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* How It Works */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">
            How It Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">
                1
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                Upload Video
              </h3>
              <p className="text-slate-400">
                Upload your Clash Royale gameplay MP4
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">
                2
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                AI Analysis
              </h3>
              <p className="text-slate-400">
                Our engine analyzes every frame and card play
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">
                3
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                Get Insights
              </h3>
              <p className="text-slate-400">
                See blunders, brilliant moves, and win probability
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">
                4
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                Improve
              </h3>
              <p className="text-slate-400">
                Learn from mistakes and master your playstyle
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900/50 backdrop-blur-sm border-t border-slate-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-center text-slate-400">
            Clash Royale Analyzer - Stockfish for Clash Royale
          </p>
        </div>
      </footer>
    </div>
  );
}
