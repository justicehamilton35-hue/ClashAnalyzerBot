/**
 * API client for Clash Royale Analyzer backend
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AnalysisJob {
  job_id: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result_path?: string;
  error?: string;
}

export interface AnalysisResult {
  job_id: string;
  video_path: string;
  analysis_timestamp: string;
  game_summary: {
    duration: number;
    total_frames_analyzed: number;
    total_moves: number;
    your_moves: number;
    opponent_moves: number;
  };
  performance: {
    accuracy_score: number;
    average_evaluation: number;
    average_win_probability: number;
    move_quality: {
      brilliant: number;
      great: number;
      good: number;
      book: number;
      inaccuracies: number;
      mistakes: number;
      blunders: number;
    };
  };
  playstyle: {
    type: string;
    aggression_rating: number;
    defense_rating: number;
    elixir_efficiency: number;
  };
  insights: {
    strengths: string[];
    weaknesses: string[];
    suggestions: string[];
  };
  key_moments: Array<{
    timestamp: number;
    card: string;
    quality: string;
    symbol: string;
    explanation: string;
    eval_change: number;
    win_prob_before: number;
    win_prob_after: number;
  }>;
  timeline: Array<{
    timestamp: number;
    frame: number;
    evaluation: number;
    win_probability: number;
    your_elixir: number;
    opponent_elixir: number;
    your_troops: number;
    opponent_troops: number;
  }>;
  moves: Array<{
    timestamp: number;
    card: string;
    player: string;
    position: [number, number];
    quality: string;
    symbol: string;
    explanation: string;
    evaluation_before: number;
    evaluation_after: number;
    eval_change: number;
    win_prob_before: number;
    win_prob_after: number;
    themes: string[];
  }>;
}

/**
 * Upload a video file for analysis
 */
export async function uploadVideo(file: File): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Start analysis for an uploaded video
 */
export async function startAnalysis(
  jobId: string,
  options: { fps?: number; save_frames?: boolean } = {}
): Promise<{ job_id: string; status: string; message: string }> {
  const response = await api.post(`/api/analyze/${jobId}`, {
    fps: options.fps || 2,
    save_frames: options.save_frames || false,
  });

  return response.data;
}

/**
 * Get analysis job status
 */
export async function getAnalysisStatus(jobId: string): Promise<AnalysisJob> {
  const response = await api.get(`/api/status/${jobId}`);
  return response.data;
}

/**
 * Get complete analysis result
 */
export async function getAnalysisResult(jobId: string): Promise<AnalysisResult> {
  const response = await api.get(`/api/result/${jobId}`);
  return response.data;
}

/**
 * List all analysis jobs
 */
export async function listJobs(): Promise<{ total_jobs: number; jobs: any[] }> {
  const response = await api.get('/api/jobs');
  return response.data;
}

/**
 * Delete an analysis job
 */
export async function deleteJob(jobId: string): Promise<void> {
  await api.delete(`/api/job/${jobId}`);
}

/**
 * Download analysis file
 */
export function getDownloadUrl(jobId: string, fileType: 'report' | 'timeline' | 'summary'): string {
  return `${API_BASE_URL}/api/download/${jobId}/${fileType}`;
}

/**
 * Poll analysis status until complete or failed
 */
export async function pollAnalysisStatus(
  jobId: string,
  onProgress?: (status: AnalysisJob) => void,
  intervalMs: number = 2000
): Promise<AnalysisJob> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getAnalysisStatus(jobId);

        if (onProgress) {
          onProgress(status);
        }

        if (status.status === 'completed') {
          resolve(status);
        } else if (status.status === 'failed') {
          reject(new Error(status.error || 'Analysis failed'));
        } else {
          setTimeout(poll, intervalMs);
        }
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
}

export default api;
