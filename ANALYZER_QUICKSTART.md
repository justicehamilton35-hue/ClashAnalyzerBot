# Clash Royale Analyzer - Quick Start Guide

Get started analyzing your Clash Royale games in 5 minutes!

## Prerequisites

- Python 3.12+
- Node.js 18+
- Docker (running)
- Roboflow account with API key

## Quick Setup

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r analyzer_requirements.txt

# Frontend dependencies
cd analyzer/frontend && npm install && cd ../..
```

### 2. Configure Environment

Create `.env` in the root directory:

```bash
ROBOFLOW_API_KEY=your_api_key_here
WORKSPACE_TROOP_DETECTION=your-troop-workspace
WORKSPACE_CARD_DETECTION=your-card-workspace
```

### 3. Start Roboflow Inference Server

```bash
# In Docker terminal
inference server start
```

### 4. Start Backend

```bash
# Terminal 1
cd analyzer/backend/api
python main.py
```

### 5. Start Frontend

```bash
# Terminal 2
cd analyzer/frontend
npm run dev
```

## Use the Analyzer

1. Open http://localhost:3000
2. Upload your Clash Royale MP4 video
3. Click "Analyze Game"
4. View detailed analysis!

## What You Get

### Analysis Features

- **Evaluation Graph**: Position strength throughout the game (-10 to +10)
- **Win Probability**: Your win % at each moment (0-100%)
- **Move Classification**: Every card play rated (brilliant → blunder)
- **Playstyle Analysis**: Beatdown, cycle, control, or bridge spam
- **Insights**: Strengths, weaknesses, and improvement suggestions

### Move Quality

- ⭐ **Brilliant (!!!)**: Exceptional, game-winning move
- **Great (!!)**: Very strong move
- **Good (!)**: Solid, above-average move
- **Book**: Standard move
- ⚠️ **Inaccuracy (?!)**: Slight mistake
- **Mistake (?)**: Clear error
- 🚨 **Blunder (??)**: Severe mistake

## Example Analysis

After uploading your video, you'll see:

```
Overall Score: 87.3% Accuracy
Playstyle: Bridge Spam
Brilliant Moves: 2
Blunders: 1

Move Analysis:
1. [00:15] Hog Rider !! - Great move! (+1.8 eval)
2. [00:23] Fireball ! - Good spell usage (+0.7 eval)
3. [00:45] Knight ?? - Blunder! Wrong placement (-3.2 eval)
...
```

## Tips

1. **Record clear gameplay**: Make sure the full game area is visible
2. **Use MP4 format**: Other formats may not work
3. **Shorter clips**: 1-2 minute clips process faster
4. **Review blunders**: Learn the most from your mistakes

## Troubleshooting

**Backend won't start?**
- Check .env file exists with valid API keys
- Verify Inference Server running at http://localhost:9001

**Analysis taking too long?**
- Reduce FPS to 1 in settings
- Try shorter video clips first

**No cards detected?**
- Verify Roboflow workflows are forked correctly
- Check workspace names match exactly

## Next Steps

See [ANALYZER_SETUP.md](ANALYZER_SETUP.md) for:
- Detailed configuration
- Advanced features
- Performance tuning
- Custom evaluation weights

## Full Documentation

- **Setup Guide**: [ANALYZER_SETUP.md](ANALYZER_SETUP.md)
- **Architecture**: [analyzer/README.md](analyzer/README.md)
- **API Docs**: http://localhost:8000/docs (when running)

---

**Enjoy analyzing your games! 🎮**
