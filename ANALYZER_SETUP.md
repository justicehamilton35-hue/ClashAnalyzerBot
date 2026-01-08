# Clash Royale Analyzer - Complete Setup Guide

This guide will help you set up the complete Clash Royale Analyzer system, including the backend API and frontend web interface.

## Overview

The Clash Royale Analyzer is a comprehensive system that analyzes your Clash Royale gameplay videos, similar to how Stockfish analyzes chess games. It consists of:

- **Video Processing**: Extracts frames from MP4 videos
- **Game State Tracking**: Detects cards, troops, towers, and elixir
- **Evaluation Engine**: Evaluates positions (-10 to +10 scale)
- **Move Analysis**: Classifies moves as brilliant, great, good, inaccuracy, mistake, or blunder
- **Backend API**: FastAPI server for video upload and analysis
- **Frontend**: React/Next.js web interface with chess.com-style layout

## Prerequisites

Before starting, ensure you have:

- **Python 3.12+** installed
- **Node.js 18+** and npm installed
- **Docker** running (for Roboflow Inference Server)
- **Roboflow Account** with API key and forked workflows
- **Git** for cloning the repository

## Part 1: Backend Setup

### Step 1: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install additional analyzer dependencies
pip install fastapi uvicorn opencv-python python-multipart python-dotenv
```

### Step 2: Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# Roboflow Configuration
ROBOFLOW_API_KEY=your_roboflow_api_key_here
WORKSPACE_TROOP_DETECTION=your-troop-workspace-name
WORKSPACE_CARD_DETECTION=your-card-workspace-name
```

To get these values:

1. Go to [Roboflow](https://roboflow.com/) and log in
2. Get your API key from Settings → Private API Key
3. Fork the two workflows (see main README.md for links)
4. Copy the workspace names from your forked workflows

### Step 3: Start Roboflow Inference Server

```bash
# In Docker terminal
pip install inference-cli
inference server start

# Verify it's running at http://localhost:9001
```

### Step 4: Test the Analyzer

Test the core analyzer with a sample video:

```bash
python analyzer/engine/analyzer.py path/to/your/video.mp4
```

This will analyze the video and save results to `analyzer/data/analysis_results/`.

### Step 5: Start Backend API Server

```bash
# From the root directory
cd analyzer/backend/api
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Test it by visiting:
- `http://localhost:8000/` - API root
- `http://localhost:8000/health` - Health check

## Part 2: Frontend Setup

### Step 1: Install Node Dependencies

```bash
cd analyzer/frontend
npm install
```

### Step 2: Configure Frontend Environment

Create `analyzer/frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Using the Analyzer

### Via Web Interface (Recommended)

1. Open `http://localhost:3000` in your browser
2. Upload your Clash Royale gameplay MP4 video
3. Click "Analyze Game"
4. Wait for analysis to complete (progress shown)
5. View detailed analysis with:
   - Evaluation graph
   - Win probability timeline
   - Move-by-move breakdown
   - Playstyle analysis
   - Strengths and weaknesses

### Via Command Line

```bash
# Analyze a video directly
python analyzer/engine/analyzer.py your_game.mp4 --fps 2 --save-frames

# Results saved to analyzer/data/analysis_results/
```

### Via API

```bash
# 1. Upload video
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@your_game.mp4"

# Response: { "job_id": "abc-123..." }

# 2. Start analysis
curl -X POST "http://localhost:8000/api/analyze/{job_id}" \
  -H "Content-Type: application/json" \
  -d '{"fps": 2, "save_frames": false}'

# 3. Check status
curl "http://localhost:8000/api/status/{job_id}"

# 4. Get results when complete
curl "http://localhost:8000/api/result/{job_id}"
```

## Understanding the Analysis

### Move Classifications

- **Brilliant (!!!)**: Exceptional move, best or only winning move
- **Great (!!)**: Very strong move, significantly better than alternatives
- **Good (!)**: Solid move, above average
- **Book**: Standard, expected move
- **Inaccuracy (?!)**: Suboptimal, loses slight advantage
- **Mistake (?)**: Clear error, loses significant advantage
- **Blunder (??)**: Severe mistake, potentially game-losing

### Evaluation Metrics

- **Position Score**: -10 (losing badly) to +10 (winning decisively)
- **Win Probability**: 0% (certain loss) to 100% (certain win)
- **Accuracy Score**: Percentage of good moves (brilliant/great/good/book)

### Playstyle Types

- **Beatdown**: Heavy, expensive pushes
- **Cycle**: Fast, cheap card cycling
- **Control**: Board control and defense-focused
- **Bridge Spam**: Aggressive, constant pressure
- **Balanced**: Mix of strategies

## Project Structure

```
ClashAnalyzerBot/
├── analyzer/                    # New analyzer system
│   ├── backend/                # Backend API
│   │   └── api/
│   │       └── main.py        # FastAPI server
│   ├── frontend/               # React/Next.js frontend
│   │   ├── src/
│   │   │   ├── app/          # Next.js pages
│   │   │   ├── components/   # React components
│   │   │   └── lib/          # API client
│   │   └── package.json
│   ├── engine/                 # Analysis engine
│   │   ├── analyzer.py        # Main orchestrator
│   │   ├── game_state_tracker.py
│   │   ├── evaluation/        # Position evaluation
│   │   └── analysis/          # Move analysis
│   ├── utils/                  # Utilities
│   │   └── video_processor.py
│   └── data/                   # Data storage
│       ├── videos/            # Uploaded videos
│       └── analysis_results/  # Analysis outputs
├── env.py                      # Original bot environment
├── dqn_agent.py               # Original DQN agent
├── Actions.py                  # Screen capture/control
└── .env                        # Configuration
```

## Troubleshooting

### "ROBOFLOW_API_KEY environment variable is not set"

Make sure you have a `.env` file in the root directory with your API key.

### "Could not initialize analyzer"

1. Check that Docker is running
2. Verify Inference Server is running at `http://localhost:9001`
3. Test your API key and workspace names

### "Analysis failed" or slow processing

1. Reduce FPS (try fps=1 instead of fps=2)
2. Check video format (must be MP4)
3. Ensure video shows clear gameplay area
4. Check that Roboflow models are accessible

### Frontend can't connect to backend

1. Verify backend is running on port 8000
2. Check NEXT_PUBLIC_API_URL in `.env.local`
3. Check browser console for CORS errors

### "No predictions found in results"

Your Roboflow workflows might need adjustment:
1. Verify you forked both workflows
2. Check workspace names match exactly
3. Test workflows directly in Roboflow

## Performance Tips

1. **Use lower FPS**: Set fps=1 or fps=2 for faster analysis
2. **Disable frame saving**: Set save_frames=false to save disk space
3. **Process shorter clips**: Analyze 1-2 minute clips for faster results
4. **Use production build**: For frontend, run `npm run build && npm start`

## Advanced Configuration

### Custom Evaluation Weights

Edit `analyzer/engine/evaluation/position_evaluator.py`:

```python
# Line ~115
total_score = (
    material * 0.25 +      # Material advantage
    board_control * 0.15 + # Territory control
    elixir * 0.10 +       # Elixir advantage
    towers * 0.30 +       # Tower health
    positioning * 0.10 +  # Troop positioning
    pressure * 0.05 +     # Offensive pressure
    defense * 0.05        # Defense rating
)
```

### Custom Move Thresholds

Edit `analyzer/engine/analysis/move_analyzer.py`:

```python
# Line ~90 - Adjust these thresholds
if eval_change >= 3.0:
    return MoveQuality.BRILLIANT
elif eval_change >= 1.5:
    return MoveQuality.GREAT
# ... etc
```

## Next Steps

1. **Record gameplay**: Use screen recording to capture your Clash Royale matches
2. **Analyze games**: Upload videos and review the analysis
3. **Study blunders**: Focus on learning from your mistakes
4. **Track progress**: Compare accuracy scores across multiple games
5. **Share results**: Download analysis reports to share with friends

## Support

For issues or questions:
- Check the main README.md
- Review this setup guide
- Check the API documentation at `http://localhost:8000/docs`

Happy analyzing! 🎮
