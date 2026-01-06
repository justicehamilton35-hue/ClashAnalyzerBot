# 🎯 ClashFish - AI Clash Royale Coach

**Transform your Clash Royale gameplay with AI-powered analysis!**

ClashFish is like Stockfish for chess, but for Clash Royale. Upload your game recordings and get detailed AI analysis of your moves, mistakes, and improvement opportunities.

## 🌟 Features

### 📊 Comprehensive Analysis
- **Move-by-move evaluation** using trained DQN model
- **Move quality classification**: Brilliant (!!), Good (!), Inaccuracy (?!), Mistake (?), Blunder (??)
- **Q-value based scoring** (like centipawn loss in chess)
- **Top alternative suggestions** for each move

### 🎯 Mistake Detection
- **Elixir management errors**: Overcapping, poor trades
- **Spell wastage**: Arrows/Fireball with no targets
- **Poor card placement**: Units too far from action
- **Timing errors**: Slow reactions, overcommitment
- **Strategic blunders**: AI identifies suboptimal plays

### 📈 Performance Ratings (0-10)
- Elixir Management
- Card Placement
- Defensive Play
- Offensive Play
- Overall Rating

### 📱 Mobile-Friendly
- Upload screen recordings directly from your phone
- Responsive web interface
- Works on any device with a browser

### 📄 Multiple Report Formats
- **HTML**: Beautiful, interactive reports
- **JSON**: For developers and integrations
- **Text**: Simple, readable summaries

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Trained DQN model (from the original bot)
- Roboflow account (for vision models)
- Screen recordings of Clash Royale matches

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ClashAnalyzerBot.git
cd ClashAnalyzerBot

# Install dependencies
pip install -r requirements_clashfish.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your Roboflow API key
```

### Usage

#### Option 1: Web Interface (Recommended for Mobile)

1. **Start the API server:**
```bash
python api_server.py
```

2. **Open the mobile interface:**
- Open `frontend/index.html` in your browser
- Or visit `http://localhost:8000` if served

3. **Upload and analyze:**
- Record your Clash Royale match
- Upload the video
- Wait for analysis (~1-2 minutes)
- View your detailed report!

#### Option 2: Command Line

```bash
# Analyze a video file
python clashfish.py analyze <video_path>

# Specify model
python clashfish.py analyze <video_path> --model models/model_latest.pth

# Save report to file
python clashfish.py analyze <video_path> --output report.txt
```

## 📖 How It Works

### 1. Video Processing
- Extracts frames from your screen recording (2 FPS)
- Uses Roboflow computer vision models to detect:
  - Cards in hand
  - Elixir level
  - Troop positions (allied & enemy)
  - Tower HP

### 2. Game State Reconstruction
- Builds timeline of game states
- Identifies when you played cards
- Tracks elixir spending and generation

### 3. AI Analysis Engine
- Loads trained DQN model
- For each of your moves:
  - Calculates Q-value (move quality score)
  - Finds AI's top recommendations
  - Computes "evaluation loss" (how much worse than optimal)
  - Classifies move quality

### 4. Mistake Detection
- Analyzes patterns across the game
- Identifies specific error types
- Categorizes by severity (minor, moderate, critical)

### 5. Report Generation
- Compiles all analysis data
- Calculates performance ratings
- Generates improvement suggestions
- Creates formatted reports

## 📊 Example Analysis Report

```
============================================================
CLASHFISH ANALYSIS REPORT
============================================================

GAME SUMMARY
------------------------------------------------------------
Duration: 3:42
Total Moves: 28
Overall Accuracy: 67.5% (GOOD)

MOVE QUALITY BREAKDOWN
------------------------------------------------------------
  Brilliant (!!):   2
  Good (!):         12
  Inaccuracies (?!): 8
  Mistakes (?):      4
  Blunders (??):     2

PERFORMANCE RATINGS
------------------------------------------------------------
  Elixir Management: 6.2/10 ██████░░░░
  Card Placement:    7.1/10 ███████░░░
  Defensive Play:    5.5/10 █████░░░░░
  Offensive Play:    6.8/10 ██████░░░░
  Overall:           6.4/10 ██████░░░░

TOP BLUNDERS
------------------------------------------------------------
1. [0:23] Arrows at (0.52, 0.18) - Loss: 45.2%
   → Should have played: Wait (save elixir)

2. [1:45] Wizard at (0.71, 0.85) - Loss: 38.7%
   → Should have played: Knight at (0.45, 0.62)

IMPROVEMENT TIPS
------------------------------------------------------------
📚 Elixir Management:
   You frequently overcap at 10 elixir. Play cards faster
   to maintain pressure and avoid wasting generation.

📚 Spell Usage:
   You wasted 2 spells. Save spells for grouped enemies
   or key targets. Don't panic-spell!

📚 Decision Making:
   You made 6 strategic errors. Think more carefully about
   each play. What is your win condition?
```

## 🎮 Recording Your Games

### iOS (iPhone/iPad)
1. Open Control Center
2. Press and hold Screen Recording button
3. Tap "Clash Royale" from the list
4. Play your match
5. Stop recording when done
6. Video saves to Photos app

### Android
1. Pull down notification shade
2. Tap "Screen Record"
3. Open Clash Royale
4. Play your match
5. Stop recording when done
6. Video saves to Gallery

### Desktop (BlueStacks/Emulator)
- Use OBS Studio or similar screen recording software
- Record just the game window
- Save as MP4

## 🔧 API Documentation

### Endpoints

#### `POST /upload`
Upload a video for analysis.

**Request:**
- Form data with `file` field
- Supported formats: MP4, MOV, AVI

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "pending",
  "message": "Video uploaded successfully",
  "status_url": "/status/uuid-here"
}
```

#### `GET /status/{job_id}`
Check analysis progress.

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "progress": 45,
  "message": "Analyzing moves...",
  "created_at": "2025-01-06T10:30:00"
}
```

#### `GET /report/{job_id}`
Get JSON analysis report.

#### `GET /report/{job_id}/html`
Get HTML formatted report.

#### `GET /report/{job_id}/text`
Download text report.

## 🏗️ Architecture

```
ClashFish Architecture
│
├── video_processor.py
│   └── Extracts frames and detects game state
│
├── clashfish_engine.py
│   └── Evaluates moves using DQN model
│
├── mistake_detector.py
│   └── Identifies specific error types
│
├── report_generator.py
│   └── Creates formatted reports (HTML/JSON/Text)
│
├── api_server.py
│   └── FastAPI web server for uploads
│
└── frontend/index.html
    └── Mobile-friendly upload interface
```

## 🎯 Move Quality Classifications

| Symbol | Name | Evaluation Loss | Description |
|--------|------|----------------|-------------|
| !! | Brilliant | < 0% | Better than AI's best move |
| ! | Good | 0-5% | Within 5% of optimal |
| (none) | Okay | 5-15% | Decent move |
| ?! | Inaccuracy | 15-30% | Noticeably suboptimal |
| ? | Mistake | 30-50% | Poor choice |
| ?? | Blunder | 50%+ | Terrible move |

## 🔬 Advanced Features

### Custom Model Training
Train ClashFish on your own gameplay style:
```bash
python train.py --games 1000 --save-interval 10
```

### Batch Analysis
Analyze multiple games at once:
```bash
python clashfish.py batch ./replays/*.mp4 --output ./reports/
```

### Deck Analysis
Get deck-specific recommendations:
```bash
python clashfish.py analyze game.mp4 --deck "Hog,Musketeer,Fireball,Zap"
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- [ ] Better troop detection models
- [ ] Tower HP tracking
- [ ] Deck-specific analysis
- [ ] Meta comparison (vs top players)
- [ ] Real-time overlay (during live play)
- [ ] Mobile app (iOS/Android)

## 📝 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Original Clash Royale bot by [original author]
- Inspired by Stockfish chess engine
- Roboflow for computer vision infrastructure

## 📧 Support

Questions or issues?
- GitHub Issues: [link]
- Discord: [link]
- Email: support@clashfish.ai

---

**Made with ❤️ by the ClashFish team**

Transform your gameplay. Become a better player. Win more matches. 🏆
